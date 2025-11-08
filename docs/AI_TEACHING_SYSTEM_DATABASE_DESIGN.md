# AI 在线教学系统 - 数据库架构设计 (MySQL 8)

## 概述
本文档定义了支持多教室、多学生同时在线的1对1 AI教学系统的完整数据库架构。

## 技术栈
- **主数据库**: MySQL 8.0+
- **缓存**: Redis 7+
- **会话存储**: Redis (WebSocket会话)
- **文件存储**: S3兼容对象存储

---

## 数据库模式设计

### 1. 用户管理模块

#### 1.1 users (用户表)
```sql
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    role VARCHAR(50) NOT NULL CHECK (role IN ('student', 'admin', 'teacher')),
    avatar_url TEXT,
    language VARCHAR(10) DEFAULT 'zh-CN',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    email_verified BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20),
    phone_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    metadata JSON DEFAULT NULL,
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_role (role),
    INDEX idx_users_status (status),
    INDEX idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 1.2 user_profiles (用户详细资料)
```sql
CREATE TABLE user_profiles (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    grade_level VARCHAR(50) COMMENT '年级: elementary, middle, high, college',
    learning_style VARCHAR(50) COMMENT 'visual, auditory, kinesthetic, reading',
    preferred_subjects JSON COMMENT '偏好科目数组',
    learning_goals JSON COMMENT '学习目标数组',
    special_needs TEXT,
    parent_email VARCHAR(255),
    parent_phone VARCHAR(20),
    school_name VARCHAR(200),
    country VARCHAR(100),
    state_province VARCHAR(100),
    city VARCHAR(100),
    bio TEXT,
    interests JSON COMMENT '兴趣数组',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_user_profiles_user_id_unique (user_id),
    INDEX idx_user_profiles_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 1.3 user_settings (用户设置)
```sql
CREATE TABLE user_settings (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY idx_user_settings_unique (user_id, setting_key),
    INDEX idx_user_settings_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 2. AI教师配置模块

#### 2.1 ai_teachers (AI教师模板)
```sql
CREATE TABLE ai_teachers (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL COMMENT 'math, science, english, etc.',
    grade_levels JSON COMMENT 'elementary, middle, high, college 数组',
    avatar_url TEXT,
    voice_id VARCHAR(100) COMMENT 'TTS voice identifier',
    voice_provider VARCHAR(50) COMMENT 'elevenlabs, openai, google, etc.',
    personality_traits JSON,
    teaching_style VARCHAR(50) COMMENT 'patient, encouraging, challenging, adaptive',
    language VARCHAR(10) DEFAULT 'zh-CN',

    -- AI Model Configuration
    llm_provider VARCHAR(50) NOT NULL COMMENT 'openai, anthropic, google',
    llm_model VARCHAR(100) NOT NULL COMMENT 'gpt-4, claude-3-opus, gemini-pro',
    llm_temperature DECIMAL(3,2) DEFAULT 0.7,
    llm_max_tokens INT DEFAULT 2000,

    -- System Prompt
    system_prompt TEXT NOT NULL,
    conversation_starters JSON COMMENT '开场白数组',

    -- Capabilities
    supports_voice BOOLEAN DEFAULT TRUE,
    supports_video BOOLEAN DEFAULT FALSE,
    supports_screen_share BOOLEAN DEFAULT FALSE,
    supports_whiteboard BOOLEAN DEFAULT TRUE,
    supports_file_upload BOOLEAN DEFAULT TRUE,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,
    created_by CHAR(36),
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON,

    INDEX idx_ai_teachers_subject (subject),
    INDEX idx_ai_teachers_is_active (is_active),
    INDEX idx_ai_teachers_created_by (created_by),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 2.2 ai_teacher_knowledge_base (AI教师知识库)
```sql
CREATE TABLE ai_teacher_knowledge_base (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    ai_teacher_id CHAR(36) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) COMMENT 'lesson, faq, example, reference',
    subject_area VARCHAR(100),
    difficulty_level VARCHAR(20) COMMENT 'beginner, intermediate, advanced',
    tags JSON COMMENT '标签数组',
    file_urls JSON COMMENT '文件URL数组',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_ai_teacher_kb_teacher_id (ai_teacher_id),
    INDEX idx_ai_teacher_kb_subject (subject_area),
    FULLTEXT INDEX idx_ai_teacher_kb_content (title, content),
    FOREIGN KEY (ai_teacher_id) REFERENCES ai_teachers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 3. 教室管理模块

#### 3.1 classrooms (教室/会话)
```sql
CREATE TABLE classrooms (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),

    -- Basic Info
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Participants
    student_id CHAR(36) NOT NULL,
    ai_teacher_id CHAR(36) NOT NULL,

    -- Session Configuration
    subject VARCHAR(100) NOT NULL,
    lesson_topic VARCHAR(500),
    learning_objectives JSON COMMENT '学习目标数组',
    duration_minutes INT COMMENT '计划时长',

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'active', 'paused', 'completed', 'cancelled', 'error')),

    -- WebRTC / Transport Configuration
    transport_type VARCHAR(50) DEFAULT 'daily' COMMENT 'daily, livekit, webrtc, websocket',
    room_url TEXT COMMENT 'Daily.co room URL or similar',
    room_token TEXT COMMENT 'Access token for student',
    room_config JSON,

    -- Timing
    scheduled_start_at TIMESTAMP NULL,
    actual_start_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,

    -- Analytics
    total_messages INT DEFAULT 0,
    student_messages INT DEFAULT 0,
    ai_messages INT DEFAULT 0,
    total_audio_duration_seconds INT DEFAULT 0,

    -- Quality Metrics
    average_response_time_ms INT,
    interruption_count INT DEFAULT 0,
    technical_issues_count INT DEFAULT 0,

    -- Recording
    recording_enabled BOOLEAN DEFAULT FALSE,
    recording_url TEXT,
    transcript_url TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON,

    INDEX idx_classrooms_student_id (student_id),
    INDEX idx_classrooms_ai_teacher_id (ai_teacher_id),
    INDEX idx_classrooms_status (status),
    INDEX idx_classrooms_scheduled_start (scheduled_start_at),
    INDEX idx_classrooms_actual_start (actual_start_at),
    INDEX idx_classrooms_created_at (created_at),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ai_teacher_id) REFERENCES ai_teachers(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 3.2 classroom_participants (教室参与者 - 支持多人扩展)
```sql
CREATE TABLE classroom_participants (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    classroom_id CHAR(36) NOT NULL,
    user_id CHAR(36),
    participant_type VARCHAR(50) NOT NULL CHECK (participant_type IN ('student', 'observer', 'assistant')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP NULL,
    total_time_seconds INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_classroom_participants_classroom_id (classroom_id),
    INDEX idx_classroom_participants_user_id (user_id),
    UNIQUE KEY idx_classroom_participants_unique (classroom_id, user_id, left_at),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 3.3 classroom_resources (教室资源)
```sql
CREATE TABLE classroom_resources (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    classroom_id CHAR(36) NOT NULL,
    resource_type VARCHAR(50) NOT NULL COMMENT 'pdf, image, video, link, whiteboard, code',
    title VARCHAR(500),
    file_url TEXT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    thumbnail_url TEXT,
    content TEXT COMMENT 'for text content or code',
    uploaded_by CHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,

    INDEX idx_classroom_resources_classroom_id (classroom_id),
    INDEX idx_classroom_resources_type (resource_type),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 4. 对话历史模块

#### 4.1 conversation_messages (对话消息 - 按月分区)
```sql
CREATE TABLE conversation_messages (
    id CHAR(36) NOT NULL,
    classroom_id CHAR(36) NOT NULL,

    -- Message Info
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('text', 'audio', 'image', 'system', 'tool_call', 'tool_response')),
    role VARCHAR(50) NOT NULL CHECK (role IN ('student', 'assistant', 'system', 'tool')),

    -- Content
    content TEXT,
    content_json JSON COMMENT 'for structured content',
    audio_url TEXT,
    audio_duration_seconds DECIMAL(10,2),
    image_url TEXT,

    -- Transcription (for audio messages)
    transcript TEXT,
    transcript_confidence DECIMAL(5,4),

    -- LLM Context
    llm_model VARCHAR(100),
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,

    -- Timing
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INT,

    -- Metadata
    parent_message_id CHAR(36),
    metadata JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id, created_at),
    INDEX idx_conversation_messages_classroom_id (classroom_id),
    INDEX idx_conversation_messages_timestamp (timestamp),
    INDEX idx_conversation_messages_role (role),
    INDEX idx_conversation_messages_parent (parent_message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202411 VALUES LESS THAN (202412),
    PARTITION p202412 VALUES LESS THAN (202501),
    PARTITION p202501 VALUES LESS THAN (202502),
    PARTITION p202502 VALUES LESS THAN (202503),
    PARTITION p202503 VALUES LESS THAN (202504),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 4.2 conversation_turns (对话轮次)
```sql
CREATE TABLE conversation_turns (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    classroom_id CHAR(36) NOT NULL,
    turn_number INT NOT NULL,

    -- Student Input
    student_message_id CHAR(36),
    student_input_text TEXT,
    student_audio_url TEXT,

    -- AI Response
    ai_message_id CHAR(36),
    ai_response_text TEXT,
    ai_audio_url TEXT,

    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    response_time_ms INT,

    -- Quality
    was_interrupted BOOLEAN DEFAULT FALSE,
    had_error BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_conversation_turns_classroom_id (classroom_id),
    INDEX idx_conversation_turns_number (classroom_id, turn_number),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 5. 学习分析模块

#### 5.1 learning_assessments (学习评估)
```sql
CREATE TABLE learning_assessments (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    classroom_id CHAR(36) NOT NULL,
    student_id CHAR(36) NOT NULL,

    -- Assessment Type
    assessment_type VARCHAR(50) NOT NULL COMMENT 'formative, summative, diagnostic',

    -- Scores
    overall_score DECIMAL(5,2) COMMENT '0-100',
    engagement_score DECIMAL(5,2),
    comprehension_score DECIMAL(5,2),
    participation_score DECIMAL(5,2),

    -- Detailed Analysis
    strengths JSON COMMENT '优势数组',
    weaknesses JSON COMMENT '劣势数组',
    recommendations JSON COMMENT '建议数组',

    -- AI Analysis
    ai_summary TEXT,
    ai_feedback JSON,

    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assessed_by VARCHAR(50) COMMENT 'ai_auto, teacher, system',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,

    INDEX idx_learning_assessments_classroom_id (classroom_id),
    INDEX idx_learning_assessments_student_id (student_id),
    INDEX idx_learning_assessments_assessed_at (assessed_at),
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 5.2 learning_progress (学习进度)
```sql
CREATE TABLE learning_progress (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36) NOT NULL,
    subject VARCHAR(100) NOT NULL,

    -- Progress Metrics
    total_sessions INT DEFAULT 0,
    total_duration_minutes INT DEFAULT 0,
    current_level VARCHAR(50) COMMENT 'beginner, intermediate, advanced',
    progress_percentage DECIMAL(5,2) COMMENT '0-100',

    -- Mastery
    topics_mastered JSON COMMENT '已掌握主题数组',
    topics_in_progress JSON COMMENT '学习中主题数组',
    topics_not_started JSON COMMENT '未开始主题数组',

    -- Statistics
    average_session_score DECIMAL(5,2),
    total_messages_sent INT DEFAULT 0,
    total_questions_asked INT DEFAULT 0,

    last_session_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY idx_learning_progress_unique (student_id, subject),
    INDEX idx_learning_progress_student_id (student_id),
    INDEX idx_learning_progress_subject (subject),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 5.3 achievement_badges (成就徽章)
```sql
CREATE TABLE achievement_badges (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon_url TEXT,
    badge_type VARCHAR(50) COMMENT 'milestone, streak, mastery, special',
    criteria JSON NOT NULL,
    points INT DEFAULT 0,
    rarity VARCHAR(20) DEFAULT 'common' COMMENT 'common, uncommon, rare, epic, legendary',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_badges (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    badge_id CHAR(36) NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,

    UNIQUE KEY idx_user_badges_unique (user_id, badge_id),
    INDEX idx_user_badges_user_id (user_id),
    INDEX idx_user_badges_earned_at (earned_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES achievement_badges(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 6. 会话状态管理 (Redis)

#### 6.1 Active Sessions
```redis
# Key: session:{classroom_id}
# Type: Hash
# Fields:
{
    "classroom_id": "uuid",
    "student_id": "uuid",
    "ai_teacher_id": "uuid",
    "status": "active|paused",
    "started_at": "iso8601",
    "last_activity": "iso8601",
    "websocket_id": "connection_id",
    "transport_room_id": "daily_room_id",
    "message_count": 0,
    "is_recording": false
}
# TTL: 24 hours
```

#### 6.2 User Online Status
```redis
# Key: user:online:{user_id}
# Type: String
# Value: "online|away|busy|offline"
# TTL: 5 minutes (heartbeat renewal)

# Key: user:connections:{user_id}
# Type: Set
# Members: [websocket_connection_ids]
```

#### 6.3 Classroom Queue
```redis
# Key: classroom:queue:{student_id}
# Type: Sorted Set
# Score: timestamp
# Members: classroom_id
```

#### 6.4 Message Cache
```redis
# Key: classroom:messages:{classroom_id}
# Type: List
# Value: JSON message objects
# TTL: 1 hour
# Max length: 100 messages
```

#### 6.5 Real-time Metrics
```redis
# Key: metrics:active_classrooms
# Type: Set
# Members: classroom_ids

# Key: metrics:hourly:{YYYY-MM-DD-HH}
# Type: Hash
# Fields:
{
    "total_sessions": 0,
    "total_students": 0,
    "total_messages": 0,
    "total_duration_seconds": 0
}
```

---

### 7. 系统管理模块

#### 7.1 api_keys (API密钥管理)
```sql
CREATE TABLE api_keys (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36),
    key_name VARCHAR(200) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    api_key_prefix VARCHAR(20) NOT NULL,

    -- Permissions
    scopes JSON COMMENT 'read:classrooms, write:classrooms, read:messages, etc. 数组',

    -- Rate Limiting
    rate_limit_per_minute INT DEFAULT 60,
    rate_limit_per_hour INT DEFAULT 1000,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,

    INDEX idx_api_keys_user_id (user_id),
    INDEX idx_api_keys_hash (api_key_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 7.2 audit_logs (审计日志 - 按月分区)
```sql
CREATE TABLE audit_logs (
    id CHAR(36) NOT NULL,
    user_id CHAR(36),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id CHAR(36),
    ip_address VARCHAR(45) COMMENT 'IPv4 or IPv6',
    user_agent TEXT,
    request_data JSON,
    response_status INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id, created_at),
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_action (action),
    INDEX idx_audit_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202411 VALUES LESS THAN (202412),
    PARTITION p202412 VALUES LESS THAN (202501),
    PARTITION p202501 VALUES LESS THAN (202502),
    PARTITION p202502 VALUES LESS THAN (202503),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 7.3 system_config (系统配置)
```sql
CREATE TABLE system_config (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    config_key VARCHAR(200) UNIQUE NOT NULL,
    config_value JSON NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by CHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (updated_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## MySQL 8 特性应用

### 1. JSON 数据类型
MySQL 8 原生支持JSON，提供高效的JSON查询和操作：

```sql
-- 查询JSON数组元素
SELECT * FROM user_profiles
WHERE JSON_CONTAINS(preferred_subjects, '"math"');

-- 查询JSON对象属性
SELECT * FROM classrooms
WHERE JSON_EXTRACT(metadata, '$.priority') = 'high';

-- 更新JSON字段
UPDATE ai_teachers
SET personality_traits = JSON_SET(
    personality_traits,
    '$.patience',
    10
)
WHERE id = 'teacher-001';
```

### 2. 窗口函数
用于复杂的分析查询：

```sql
-- 计算学生的学习排名
SELECT
    student_id,
    subject,
    average_session_score,
    RANK() OVER (PARTITION BY subject ORDER BY average_session_score DESC) as rank
FROM learning_progress;
```

### 3. CTE (公共表表达式)
提高查询可读性：

```sql
WITH student_stats AS (
    SELECT
        student_id,
        COUNT(*) as total_sessions,
        AVG(total_messages) as avg_messages
    FROM classrooms
    WHERE status = 'completed'
    GROUP BY student_id
)
SELECT u.username, s.*
FROM student_stats s
JOIN users u ON u.id = s.student_id;
```

### 4. 分区表管理
自动管理分区：

```sql
-- 添加新月份分区
ALTER TABLE conversation_messages
ADD PARTITION (
    PARTITION p202504 VALUES LESS THAN (202505)
);

-- 删除旧分区（归档数据）
ALTER TABLE conversation_messages
DROP PARTITION p202411;
```

---

## 数据库优化策略

### 1. 索引优化
```sql
-- 复合索引
CREATE INDEX idx_classrooms_student_status
ON classrooms(student_id, status, scheduled_start_at);

-- 函数索引 (MySQL 8.0.13+)
CREATE INDEX idx_users_email_lower
ON users((LOWER(email)));

-- 全文索引
CREATE FULLTEXT INDEX idx_messages_content
ON conversation_messages(content, transcript);
```

### 2. 查询优化
```sql
-- 使用EXPLAIN分析查询
EXPLAIN SELECT * FROM classrooms
WHERE student_id = 'xxx' AND status = 'active';

-- 使用FORCE INDEX强制使用索引
SELECT * FROM classrooms
FORCE INDEX (idx_classrooms_student_status)
WHERE student_id = 'xxx';
```

### 3. 缓存策略
- Redis缓存热点数据（活跃会话、用户状态）
- 消息列表缓存最近100条
- 用户设置缓存30分钟
- 查询结果集缓存（使用Redis）

### 4. 连接池配置
```python
# SQLAlchemy with MySQL
engine = create_engine(
    "mysql+pymysql://user:pass@localhost/ai_teaching?charset=utf8mb4",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)
```

### 5. 备份策略
```bash
# 全量备份
mysqldump -u root -p --single-transaction \
    --routines --triggers --events \
    ai_teaching > backup_$(date +%Y%m%d).sql

# 增量备份（使用binlog）
mysqlbinlog --start-datetime="2024-11-08 00:00:00" \
    /var/log/mysql/mysql-bin.000001 > incremental.sql
```

---

## 扩展性考虑

### 1. 主从复制
```sql
-- 主库配置 (my.cnf)
[mysqld]
server-id=1
log-bin=mysql-bin
binlog-format=ROW
sync_binlog=1

-- 从库配置
[mysqld]
server-id=2
relay-log=mysql-relay-bin
read_only=1
```

### 2. 读写分离
```python
# 使用SQLAlchemy实现读写分离
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 写库
write_engine = create_engine("mysql+pymysql://user:pass@master-host/db")

# 读库
read_engine = create_engine("mysql+pymysql://user:pass@slave-host/db")

# 根据操作类型选择引擎
def get_session(readonly=False):
    engine = read_engine if readonly else write_engine
    Session = sessionmaker(bind=engine)
    return Session()
```

### 3. 分库分表
- 按 `student_id` 哈希分表
- 消息表按时间范围分区
- 支持水平扩展到多个数据库实例

### 4. 数据归档
```sql
-- 创建归档表
CREATE TABLE conversation_messages_archive
LIKE conversation_messages;

-- 移动旧数据到归档表
INSERT INTO conversation_messages_archive
SELECT * FROM conversation_messages
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- 删除已归档数据
DELETE FROM conversation_messages
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
```

---

## 性能指标

- 支持 **10,000+** 并发教室
- 消息写入延迟 < 10ms
- 数据库查询 < 20ms (P95)
- 单表支持 **1亿+** 记录
- QPS: 50,000+ (读), 10,000+ (写)

---

## 监控指标

### 关键指标
```sql
-- 慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- 连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- InnoDB状态
SHOW ENGINE INNODB STATUS;

-- 表大小
SELECT
    table_name,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'ai_teaching'
ORDER BY size_mb DESC;
```

### Prometheus监控
```yaml
# MySQL Exporter配置
scrape_configs:
  - job_name: 'mysql'
    static_configs:
      - targets: ['localhost:9104']
```

---

## 总结

本设计基于MySQL 8.0，充分利用了其新特性：
- ✅ JSON原生支持
- ✅ 窗口函数
- ✅ CTE公共表表达式
- ✅ 函数索引
- ✅ 范围分区
- ✅ 高性能InnoDB引擎
- ✅ 完善的备份和恢复机制

适合构建大规模、高并发的AI在线教学平台。
