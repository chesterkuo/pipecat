"""
AI在线教学系统 - Bot实现示例

这个示例展示如何使用Pipecat框架创建一个1对1 AI教学Bot。
支持实时语音对话、消息历史、学习评估等功能。

使用方法:
    python ai_teaching_bot.py --classroom-id <classroom_id>

依赖:
    - pipecat-ai
    - openai
    - deepgram-sdk
    - elevenlabs
    - daily-python
    - sqlalchemy
    - redis
"""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Pipecat imports
from pipecat.frames.frames import (
    Frame,
    TextFrame,
    AudioRawFrame,
    TranscriptionFrame,
    LLMMessagesFrame,
    StartFrame,
    EndFrame,
    CancelFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai import OpenAILLMService
from pipecat.services.deepgram import DeepgramSTTService, DeepgramTTSService
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Redis
import aioredis

# Logging
import logging
from loguru import logger

# ============================================================================
# 配置
# ============================================================================

@dataclass
class ClassroomConfig:
    """教室配置"""
    classroom_id: str
    student_id: str
    ai_teacher_id: str

    # AI教师配置
    teacher_name: str
    teacher_display_name: str
    system_prompt: str
    subject: str
    lesson_topic: str

    # WebRTC配置 (Daily.co)
    room_url: str
    room_token: str

    # AI服务配置
    openai_api_key: str
    openai_model: str = "gpt-4-turbo"
    deepgram_api_key: str

    # 数据库 (MySQL 8) 和Redis
    database_url: str  # mysql+pymysql://user:pass@localhost/ai_teaching
    redis_url: str


# ============================================================================
# 自定义处理器
# ============================================================================

class ConversationLogger(FrameProcessor):
    """
    对话记录器 - 将对话保存到数据库
    """

    def __init__(self, classroom_id: str, db_session: AsyncSession, redis_client):
        super().__init__()
        self.classroom_id = classroom_id
        self.db_session = db_session
        self.redis_client = redis_client
        self.message_count = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """处理帧并记录消息"""

        # 记录学生输入
        if isinstance(frame, TranscriptionFrame) and direction == FrameDirection.DOWNSTREAM:
            await self._save_message(
                role="student",
                message_type="text",
                content=frame.text,
                transcript=frame.text,
                transcript_confidence=getattr(frame, 'confidence', None),
            )

        # 记录AI回复
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            # 检查是否是AI生成的文本
            if hasattr(frame, 'is_llm_response') and frame.is_llm_response:
                await self._save_message(
                    role="assistant",
                    message_type="text",
                    content=frame.text,
                )

        # 继续传递帧
        await self.push_frame(frame, direction)

    async def _save_message(
        self,
        role: str,
        message_type: str,
        content: str,
        transcript: Optional[str] = None,
        transcript_confidence: Optional[float] = None,
    ):
        """保存消息到数据库和Redis缓存"""

        message_data = {
            "id": f"msg_{self.classroom_id}_{self.message_count}",
            "classroom_id": self.classroom_id,
            "role": role,
            "message_type": message_type,
            "content": content,
            "transcript": transcript,
            "transcript_confidence": transcript_confidence,
            "timestamp": datetime.now().isoformat(),
        }

        # 保存到Redis缓存 (最近100条消息)
        await self.redis_client.lpush(
            f"classroom:messages:{self.classroom_id}",
            json.dumps(message_data),
        )
        await self.redis_client.ltrim(
            f"classroom:messages:{self.classroom_id}",
            0,
            99,
        )

        # 异步保存到数据库 (这里简化处理，实际应使用消息队列)
        logger.info(f"Saved message: {message_data}")

        self.message_count += 1


class LearningAnalyzer(FrameProcessor):
    """
    学习分析器 - 分析学生的学习行为和表现
    """

    def __init__(self, classroom_id: str, student_id: str, redis_client):
        super().__init__()
        self.classroom_id = classroom_id
        self.student_id = student_id
        self.redis_client = redis_client

        # 统计指标
        self.student_messages = 0
        self.ai_messages = 0
        self.questions_asked = 0
        self.total_response_time_ms = 0
        self.interruptions = 0

        self.last_student_message_time = None
        self.session_start_time = datetime.now()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """分析学习行为"""

        if isinstance(frame, TranscriptionFrame):
            self.student_messages += 1

            # 检测是否是问题
            if self._is_question(frame.text):
                self.questions_asked += 1

            # 记录时间用于计算响应时间
            self.last_student_message_time = datetime.now()

        elif isinstance(frame, TextFrame) and hasattr(frame, 'is_llm_response'):
            self.ai_messages += 1

            # 计算响应时间
            if self.last_student_message_time:
                response_time = (datetime.now() - self.last_student_message_time).total_seconds() * 1000
                self.total_response_time_ms += response_time

        # 检测打断
        elif isinstance(frame, CancelFrame):
            self.interruptions += 1

        # 继续传递帧
        await self.push_frame(frame, direction)

    def _is_question(self, text: str) -> bool:
        """简单的问题检测"""
        question_keywords = ["吗", "呢", "么", "？", "?", "什么", "怎么", "为什么", "如何"]
        return any(keyword in text for keyword in question_keywords)

    async def get_analytics(self) -> Dict[str, Any]:
        """获取分析数据"""
        duration = (datetime.now() - self.session_start_time).total_seconds()
        avg_response_time = (
            self.total_response_time_ms / self.ai_messages
            if self.ai_messages > 0
            else 0
        )

        return {
            "classroom_id": self.classroom_id,
            "student_id": self.student_id,
            "duration_seconds": duration,
            "student_messages": self.student_messages,
            "ai_messages": self.ai_messages,
            "total_messages": self.student_messages + self.ai_messages,
            "questions_asked": self.questions_asked,
            "average_response_time_ms": avg_response_time,
            "interruptions": self.interruptions,
            "engagement_score": self._calculate_engagement_score(),
        }

    def _calculate_engagement_score(self) -> float:
        """计算参与度分数 (0-100)"""
        # 简化的评分算法
        score = 0

        # 消息数量得分 (最多40分)
        score += min(self.student_messages * 2, 40)

        # 提问得分 (最多30分)
        score += min(self.questions_asked * 5, 30)

        # 响应速度得分 (最多30分)
        avg_response_time = (
            self.total_response_time_ms / self.ai_messages
            if self.ai_messages > 0
            else 5000
        )
        if avg_response_time < 1000:
            score += 30
        elif avg_response_time < 2000:
            score += 20
        elif avg_response_time < 3000:
            score += 10

        return min(score, 100)


class SessionStateManager(FrameProcessor):
    """
    会话状态管理器 - 管理教室会话的状态
    """

    def __init__(self, classroom_id: str, redis_client):
        super().__init__()
        self.classroom_id = classroom_id
        self.redis_client = redis_client
        self.is_active = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """处理会话状态变化"""

        if isinstance(frame, StartFrame):
            await self._update_session_state("active")
            self.is_active = True

        elif isinstance(frame, EndFrame):
            await self._update_session_state("completed")
            self.is_active = False

        # 心跳更新
        if self.is_active:
            await self._heartbeat()

        await self.push_frame(frame, direction)

    async def _update_session_state(self, status: str):
        """更新会话状态到Redis"""
        await self.redis_client.hset(
            f"session:{self.classroom_id}",
            "status",
            status,
        )
        await self.redis_client.hset(
            f"session:{self.classroom_id}",
            "last_activity",
            datetime.now().isoformat(),
        )
        logger.info(f"Classroom {self.classroom_id} status: {status}")

    async def _heartbeat(self):
        """发送心跳，更新最后活动时间"""
        await self.redis_client.hset(
            f"session:{self.classroom_id}",
            "last_activity",
            datetime.now().isoformat(),
        )


# ============================================================================
# Bot构建器
# ============================================================================

class AITeachingBot:
    """AI教学Bot"""

    def __init__(self, config: ClassroomConfig):
        self.config = config
        self.pipeline: Optional[Pipeline] = None
        self.task: Optional[PipelineTask] = None
        self.runner: Optional[PipelineRunner] = None

        # 数据库和Redis连接
        self.db_engine = None
        self.db_session = None
        self.redis_client = None

        # 自定义处理器
        self.conversation_logger = None
        self.learning_analyzer = None
        self.session_state_manager = None

    async def initialize(self):
        """初始化数据库和Redis连接"""
        # 数据库
        self.db_engine = create_async_engine(self.config.database_url)
        async_session = sessionmaker(
            self.db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.db_session = async_session()

        # Redis
        self.redis_client = await aioredis.from_url(
            self.config.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

        logger.info(f"Initialized database and Redis for classroom {self.config.classroom_id}")

    async def create_pipeline(self) -> Pipeline:
        """创建Pipecat Pipeline"""

        # 初始化自定义处理器
        self.conversation_logger = ConversationLogger(
            self.config.classroom_id,
            self.db_session,
            self.redis_client,
        )

        self.learning_analyzer = LearningAnalyzer(
            self.config.classroom_id,
            self.config.student_id,
            self.redis_client,
        )

        self.session_state_manager = SessionStateManager(
            self.config.classroom_id,
            self.redis_client,
        )

        # Daily.co Transport
        transport = DailyTransport(
            self.config.room_url,
            self.config.room_token,
            self.config.teacher_display_name,
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_out_enabled=False,  # 暂不启用视频
                transcription_enabled=True,
            ),
        )

        # STT Service (Deepgram)
        stt = DeepgramSTTService(
            api_key=self.config.deepgram_api_key,
            language="zh-CN",
        )

        # LLM Service (OpenAI)
        llm = OpenAILLMService(
            api_key=self.config.openai_api_key,
            model=self.config.openai_model,
        )

        # LLM Context
        context = OpenAILLMContext(
            messages=[
                {
                    "role": "system",
                    "content": self.config.system_prompt,
                }
            ]
        )
        context_aggregator = llm.create_context_aggregator(context)

        # TTS Service (Deepgram)
        tts = DeepgramTTSService(
            api_key=self.config.deepgram_api_key,
            voice="aura-asteria-zh",  # 中文语音
        )

        # 构建Pipeline
        pipeline = Pipeline([
            transport.input(),           # 1. 接收音频输入
            stt,                         # 2. 语音转文本
            self.conversation_logger,    # 3. 记录学生消息
            self.learning_analyzer,      # 4. 分析学习行为
            context_aggregator.user(),   # 5. 聚合用户消息
            llm,                         # 6. LLM生成回复
            self.conversation_logger,    # 7. 记录AI回复
            context_aggregator.assistant(), # 8. 聚合助手消息
            tts,                         # 9. 文本转语音
            transport.output(),          # 10. 输出音频
            self.session_state_manager,  # 11. 管理会话状态
        ])

        return pipeline

    async def start(self):
        """启动Bot"""
        logger.info(f"Starting AI Teaching Bot for classroom {self.config.classroom_id}")

        # 初始化连接
        await self.initialize()

        # 创建Pipeline
        self.pipeline = await self.create_pipeline()

        # 创建并运行任务
        self.task = PipelineTask(self.pipeline)
        self.runner = PipelineRunner()

        # 设置会话状态为active
        await self.redis_client.hset(
            f"session:{self.config.classroom_id}",
            mapping={
                "classroom_id": self.config.classroom_id,
                "student_id": self.config.student_id,
                "ai_teacher_id": self.config.ai_teacher_id,
                "status": "active",
                "started_at": datetime.now().isoformat(),
            },
        )

        try:
            # 运行Pipeline
            await self.runner.run(self.task)
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        logger.info(f"Cleaning up classroom {self.config.classroom_id}")

        # 获取分析数据
        if self.learning_analyzer:
            analytics = await self.learning_analyzer.get_analytics()
            logger.info(f"Session analytics: {analytics}")

            # 保存到Redis
            await self.redis_client.hset(
                f"session:{self.config.classroom_id}:analytics",
                mapping=analytics,
            )

        # 更新会话状态
        await self.redis_client.hset(
            f"session:{self.config.classroom_id}",
            "status",
            "completed",
        )
        await self.redis_client.hset(
            f"session:{self.config.classroom_id}",
            "ended_at",
            datetime.now().isoformat(),
        )

        # 关闭连接
        if self.db_session:
            await self.db_session.close()
        if self.db_engine:
            await self.db_engine.dispose()
        if self.redis_client:
            await self.redis_client.close()

    async def stop(self):
        """停止Bot"""
        if self.task:
            await self.task.cancel()


# ============================================================================
# 系统提示词模板
# ============================================================================

def create_system_prompt(teacher_name: str, subject: str, lesson_topic: str) -> str:
    """创建AI教师的系统提示词"""

    return f"""你是一位名叫{teacher_name}的专业{subject}老师，正在进行一对一在线教学。

# 教学主题
今天的课程主题是：{lesson_topic}

# 你的教学风格
- 耐心友好：用鼓励和支持的语气与学生交流
- 循序渐进：从简单概念开始，逐步深入
- 互动性强：经常提问，检查学生理解程度
- 举例说明：用生动的例子帮助学生理解抽象概念
- 因材施教：根据学生的回答调整教学节奏和难度

# 教学规则
1. 始终使用中文进行教学
2. 回答要简洁清晰，避免冗长
3. 当学生遇到困难时，提供提示而不是直接给出答案
4. 经常给予正面反馈和鼓励
5. 定期总结学习要点
6. 注意学生的语气和情绪，适时调整教学方式
7. 每次回复控制在2-3句话以内，保持对话自然流畅

# 对话示例
学生：老师好
你：你好！很高兴见到你。今天我们要学习{lesson_topic}，你准备好了吗？

学生：我有一个问题不太明白
你：没问题，请说出你的疑问，我会耐心为你解答。

学生：我觉得这个太难了
你：别担心，我们可以慢慢来。让我用一个简单的例子帮你理解。

# 重要提醒
- 始终保持鼓励和支持的态度
- 让学生主导学习节奏
- 创造一个安全、积极的学习环境
"""


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""

    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # 从环境变量或命令行参数获取配置
    classroom_id = os.getenv("CLASSROOM_ID", "test-classroom-001")

    # 创建配置
    config = ClassroomConfig(
        classroom_id=classroom_id,
        student_id="student-001",
        ai_teacher_id="teacher-math-001",

        # AI教师配置
        teacher_name="小明老师",
        teacher_display_name="小明数学老师",
        subject="数学",
        lesson_topic="一元二次方程",
        system_prompt=create_system_prompt("小明老师", "数学", "一元二次方程"),

        # WebRTC配置
        room_url=os.getenv("DAILY_ROOM_URL", "https://example.daily.co/test-room"),
        room_token=os.getenv("DAILY_ROOM_TOKEN", ""),

        # AI服务配置
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model="gpt-4-turbo",
        deepgram_api_key=os.getenv("DEEPGRAM_API_KEY", ""),

        # 数据库和Redis
        database_url=os.getenv("DATABASE_URL", "mysql+aiomysql://user:pass@localhost/ai_teaching?charset=utf8mb4"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    )

    # 创建并启动Bot
    bot = AITeachingBot(config)

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping bot...")
        await bot.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
