# AI 在线教学系统 - API 接口设计

## 概述
本文档定义了AI在线教学系统的完整REST API和WebSocket API接口规范。

## 基础信息

### Base URL
```
Production: https://api.aiteaching.example.com/v1
Staging: https://api-staging.aiteaching.example.com/v1
Development: http://localhost:8000/v1
```

### 认证方式
```http
Authorization: Bearer {JWT_TOKEN}
```

### 通用响应格式
```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2024-11-08T10:30:00Z",
  "request_id": "req_abc123"
}
```

### 错误响应格式
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "CLASSROOM_NOT_FOUND",
    "message": "The requested classroom does not exist",
    "details": {},
    "field_errors": []
  },
  "timestamp": "2024-11-08T10:30:00Z",
  "request_id": "req_abc123"
}
```

### HTTP状态码
- `200 OK` - 请求成功
- `201 Created` - 资源创建成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证
- `403 Forbidden` - 无权限
- `404 Not Found` - 资源不存在
- `409 Conflict` - 资源冲突
- `422 Unprocessable Entity` - 验证失败
- `429 Too Many Requests` - 请求过于频繁
- `500 Internal Server Error` - 服务器错误
- `503 Service Unavailable` - 服务不可用

---

## 1. 认证与授权 API

### 1.1 用户注册
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "username": "student123",
  "password": "SecurePass123!",
  "full_name": "张三",
  "role": "student",
  "language": "zh-CN",
  "timezone": "Asia/Shanghai"
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "student@example.com",
      "username": "student123",
      "full_name": "张三",
      "role": "student",
      "email_verified": false,
      "created_at": "2024-11-08T10:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

### 1.2 用户登录
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "student@example.com",
      "username": "student123",
      "full_name": "张三",
      "role": "student",
      "avatar_url": "https://cdn.example.com/avatars/user123.jpg"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

### 1.3 刷新令牌
```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 1.4 登出
```http
POST /auth/logout
Authorization: Bearer {token}
```

### 1.5 获取当前用户信息
```http
GET /auth/me
Authorization: Bearer {token}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "username": "student123",
    "full_name": "张三",
    "role": "student",
    "avatar_url": "https://cdn.example.com/avatars/user123.jpg",
    "profile": {
      "grade_level": "middle",
      "preferred_subjects": ["math", "science"],
      "learning_goals": ["improve math skills", "prepare for exam"]
    },
    "settings": {
      "notifications_enabled": true,
      "auto_record": true,
      "preferred_voice": "zh-CN-XiaoxiaoNeural"
    }
  }
}
```

---

## 2. 用户管理 API

### 2.1 更新用户资料
```http
PATCH /users/me
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "full_name": "李四",
  "avatar_url": "https://cdn.example.com/avatars/new.jpg",
  "language": "en-US"
}
```

### 2.2 更新用户详细资料
```http
PUT /users/me/profile
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "grade_level": "high",
  "learning_style": "visual",
  "preferred_subjects": ["math", "physics", "chemistry"],
  "learning_goals": ["prepare for college entrance exam"],
  "school_name": "北京第一中学"
}
```

### 2.3 更新用户设置
```http
PUT /users/me/settings
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "notifications_enabled": true,
  "email_notifications": false,
  "auto_record": true,
  "preferred_voice": "zh-CN-XiaoxiaoNeural",
  "auto_transcribe": true,
  "theme": "dark"
}
```

### 2.4 修改密码
```http
POST /users/me/change-password
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

---

## 3. AI教师管理 API

### 3.1 获取AI教师列表
```http
GET /ai-teachers
Authorization: Bearer {token}

Query Parameters:
- subject: string (optional) - 科目筛选
- grade_level: string (optional) - 年级筛选
- language: string (optional) - 语言筛选
- page: integer (default: 1)
- page_size: integer (default: 20, max: 100)
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "math_teacher_primary",
        "display_name": "小明数学老师",
        "description": "专注小学数学教学，擅长引导式教学",
        "subject": "math",
        "grade_levels": ["elementary"],
        "avatar_url": "https://cdn.example.com/teachers/math1.jpg",
        "teaching_style": "patient",
        "language": "zh-CN",
        "voice_provider": "azure",
        "supports_voice": true,
        "supports_video": false,
        "supports_whiteboard": true,
        "personality_traits": {
          "patience": 9,
          "enthusiasm": 8,
          "strictness": 5
        }
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 45,
      "total_pages": 3
    }
  }
}
```

### 3.2 获取单个AI教师详情
```http
GET /ai-teachers/{teacher_id}
Authorization: Bearer {token}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "math_teacher_primary",
    "display_name": "小明数学老师",
    "description": "专注小学数学教学，擅长引导式教学",
    "subject": "math",
    "grade_levels": ["elementary"],
    "avatar_url": "https://cdn.example.com/teachers/math1.jpg",
    "voice_id": "zh-CN-XiaoxiaoNeural",
    "voice_provider": "azure",
    "teaching_style": "patient",
    "language": "zh-CN",
    "llm_provider": "openai",
    "llm_model": "gpt-4-turbo",
    "system_prompt": "你是一位耐心的小学数学老师...",
    "conversation_starters": [
      "今天我们学什么呢？",
      "我有一道题不会做",
      "能帮我复习一下乘法口诀吗？"
    ],
    "capabilities": {
      "supports_voice": true,
      "supports_video": false,
      "supports_screen_share": false,
      "supports_whiteboard": true,
      "supports_file_upload": true
    },
    "statistics": {
      "total_sessions": 1250,
      "average_rating": 4.8,
      "total_students": 450
    }
  }
}
```

### 3.3 创建自定义AI教师 (Admin only)
```http
POST /ai-teachers
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "custom_science_teacher",
  "display_name": "科学探索老师",
  "description": "专注初中科学实验教学",
  "subject": "science",
  "grade_levels": ["middle"],
  "voice_provider": "elevenlabs",
  "voice_id": "voice_abc123",
  "teaching_style": "encouraging",
  "language": "zh-CN",
  "llm_provider": "anthropic",
  "llm_model": "claude-3-opus",
  "llm_temperature": 0.8,
  "system_prompt": "你是一位充满热情的科学老师...",
  "conversation_starters": [
    "今天做什么实验？",
    "为什么会这样？"
  ]
}
```

---

## 4. 教室管理 API

### 4.1 创建教室
```http
POST /classrooms
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "数学补习 - 代数基础",
  "ai_teacher_id": "660e8400-e29b-41d4-a716-446655440000",
  "subject": "math",
  "lesson_topic": "一元二次方程",
  "learning_objectives": [
    "理解一元二次方程的概念",
    "掌握求解方法",
    "能够应用到实际问题"
  ],
  "duration_minutes": 60,
  "scheduled_start_at": "2024-11-08T14:00:00Z",
  "transport_type": "daily",
  "recording_enabled": true
}
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "数学补习 - 代数基础",
    "student_id": "550e8400-e29b-41d4-a716-446655440000",
    "ai_teacher_id": "660e8400-e29b-41d4-a716-446655440000",
    "subject": "math",
    "lesson_topic": "一元二次方程",
    "status": "scheduled",
    "transport_type": "daily",
    "room_url": "https://example.daily.co/ai-classroom-770e8400",
    "room_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "scheduled_start_at": "2024-11-08T14:00:00Z",
    "recording_enabled": true,
    "created_at": "2024-11-08T10:30:00Z"
  }
}
```

### 4.2 获取我的教室列表
```http
GET /classrooms
Authorization: Bearer {token}

Query Parameters:
- status: string (optional) - scheduled, active, completed, cancelled
- subject: string (optional) - 科目筛选
- from_date: string (optional) - ISO 8601 日期
- to_date: string (optional) - ISO 8601 日期
- page: integer (default: 1)
- page_size: integer (default: 20)
- sort: string (default: -created_at) - created_at, -created_at, scheduled_start_at
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "数学补习 - 代数基础",
        "subject": "math",
        "lesson_topic": "一元二次方程",
        "status": "scheduled",
        "ai_teacher": {
          "id": "660e8400-e29b-41d4-a716-446655440000",
          "display_name": "小明数学老师",
          "avatar_url": "https://cdn.example.com/teachers/math1.jpg"
        },
        "scheduled_start_at": "2024-11-08T14:00:00Z",
        "duration_minutes": 60,
        "created_at": "2024-11-08T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 15,
      "total_pages": 1
    }
  }
}
```

### 4.3 获取教室详情
```http
GET /classrooms/{classroom_id}
Authorization: Bearer {token}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "数学补习 - 代数基础",
    "description": null,
    "student": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "student123",
      "full_name": "张三",
      "avatar_url": "https://cdn.example.com/avatars/user123.jpg"
    },
    "ai_teacher": {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "display_name": "小明数学老师",
      "avatar_url": "https://cdn.example.com/teachers/math1.jpg",
      "voice_provider": "azure",
      "teaching_style": "patient"
    },
    "subject": "math",
    "lesson_topic": "一元二次方程",
    "learning_objectives": [
      "理解一元二次方程的概念",
      "掌握求解方法"
    ],
    "status": "scheduled",
    "transport_type": "daily",
    "room_url": "https://example.daily.co/ai-classroom-770e8400",
    "room_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "room_config": {
      "enable_chat": true,
      "enable_screenshare": false,
      "max_participants": 2
    },
    "scheduled_start_at": "2024-11-08T14:00:00Z",
    "actual_start_at": null,
    "ended_at": null,
    "duration_minutes": 60,
    "analytics": {
      "total_messages": 0,
      "student_messages": 0,
      "ai_messages": 0
    },
    "recording_enabled": true,
    "recording_url": null,
    "transcript_url": null,
    "created_at": "2024-11-08T10:30:00Z",
    "updated_at": "2024-11-08T10:30:00Z"
  }
}
```

### 4.4 开始教室会话
```http
POST /classrooms/{classroom_id}/start
Authorization: Bearer {token}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "actual_start_at": "2024-11-08T14:00:30Z",
    "websocket_url": "wss://api.aiteaching.example.com/ws/classrooms/770e8400",
    "websocket_token": "ws_token_abc123"
  }
}
```

### 4.5 暂停教室会话
```http
POST /classrooms/{classroom_id}/pause
Authorization: Bearer {token}
```

### 4.6 恢复教室会话
```http
POST /classrooms/{classroom_id}/resume
Authorization: Bearer {token}
```

### 4.7 结束教室会话
```http
POST /classrooms/{classroom_id}/end
Authorization: Bearer {token}
```

**Request Body (Optional):**
```json
{
  "feedback": {
    "rating": 5,
    "comment": "非常棒的一节课！",
    "helpful": true
  }
}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "ended_at": "2024-11-08T15:05:00Z",
    "duration_seconds": 3870,
    "analytics": {
      "total_messages": 45,
      "student_messages": 23,
      "ai_messages": 22,
      "total_audio_duration_seconds": 3600,
      "average_response_time_ms": 850
    },
    "assessment": {
      "overall_score": 85,
      "engagement_score": 90,
      "comprehension_score": 80,
      "strengths": ["积极提问", "理解能力强"],
      "recommendations": ["可以多练习应用题"]
    }
  }
}
```

### 4.8 取消教室
```http
DELETE /classrooms/{classroom_id}
Authorization: Bearer {token}
```

### 4.9 获取教室消息历史
```http
GET /classrooms/{classroom_id}/messages
Authorization: Bearer {token}

Query Parameters:
- limit: integer (default: 50, max: 200)
- before: string (optional) - message_id, 分页游标
- after: string (optional) - message_id, 分页游标
- role: string (optional) - student, assistant, system
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg_001",
        "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
        "role": "student",
        "message_type": "text",
        "content": "老师好，我想学习一元二次方程",
        "timestamp": "2024-11-08T14:01:00Z"
      },
      {
        "id": "msg_002",
        "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
        "role": "assistant",
        "message_type": "text",
        "content": "你好！很高兴帮你学习一元二次方程。我们先从基础概念开始...",
        "audio_url": "https://cdn.example.com/audio/msg_002.mp3",
        "audio_duration_seconds": 12.5,
        "timestamp": "2024-11-08T14:01:02Z",
        "processing_time_ms": 850
      }
    ],
    "has_more": true,
    "next_cursor": "msg_050"
  }
}
```

### 4.10 上传教室资源
```http
POST /classrooms/{classroom_id}/resources
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <binary>
title: "代数练习题.pdf"
resource_type: "pdf"
```

**Response: 201 Created**
```json
{
  "success": true,
  "data": {
    "id": "res_001",
    "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
    "resource_type": "pdf",
    "title": "代数练习题.pdf",
    "file_url": "https://cdn.example.com/resources/res_001.pdf",
    "file_size_bytes": 245678,
    "thumbnail_url": "https://cdn.example.com/thumbnails/res_001.jpg",
    "created_at": "2024-11-08T14:15:00Z"
  }
}
```

### 4.11 获取教室资源列表
```http
GET /classrooms/{classroom_id}/resources
Authorization: Bearer {token}
```

---

## 5. 学习分析 API

### 5.1 获取学习进度
```http
GET /learning/progress
Authorization: Bearer {token}

Query Parameters:
- subject: string (optional) - 科目筛选
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "progress": [
      {
        "subject": "math",
        "current_level": "intermediate",
        "progress_percentage": 65.5,
        "total_sessions": 25,
        "total_duration_minutes": 1500,
        "topics_mastered": ["基础代数", "一元一次方程"],
        "topics_in_progress": ["一元二次方程", "函数基础"],
        "topics_not_started": ["三角函数", "微积分"],
        "average_session_score": 82.5,
        "last_session_at": "2024-11-08T15:00:00Z"
      }
    ]
  }
}
```

### 5.2 获取教室评估报告
```http
GET /classrooms/{classroom_id}/assessment
Authorization: Bearer {token}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "id": "assess_001",
    "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
    "assessment_type": "formative",
    "scores": {
      "overall_score": 85,
      "engagement_score": 90,
      "comprehension_score": 80,
      "participation_score": 88
    },
    "strengths": [
      "积极提问，学习态度认真",
      "对概念理解较快",
      "能够举一反三"
    ],
    "weaknesses": [
      "计算速度有待提高",
      "应用题理解需要加强"
    ],
    "recommendations": [
      "建议多做计算练习题",
      "可以尝试更多实际应用场景",
      "复习基础概念"
    ],
    "ai_summary": "本节课学生表现优秀，对一元二次方程的概念掌握较好...",
    "assessed_at": "2024-11-08T15:05:30Z"
  }
}
```

### 5.3 获取学习统计
```http
GET /learning/statistics
Authorization: Bearer {token}

Query Parameters:
- period: string (optional) - week, month, year, all
- subject: string (optional)
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "period": "month",
    "from_date": "2024-10-01",
    "to_date": "2024-10-31",
    "total_sessions": 12,
    "total_duration_minutes": 720,
    "total_subjects": 3,
    "average_score": 83.5,
    "total_messages_sent": 456,
    "total_questions_asked": 89,
    "subjects_breakdown": [
      {
        "subject": "math",
        "sessions": 8,
        "duration_minutes": 480,
        "average_score": 85
      },
      {
        "subject": "science",
        "sessions": 3,
        "duration_minutes": 180,
        "average_score": 80
      },
      {
        "subject": "english",
        "sessions": 1,
        "duration_minutes": 60,
        "average_score": 85
      }
    ],
    "daily_activity": [
      {
        "date": "2024-10-15",
        "sessions": 2,
        "duration_minutes": 120
      }
    ],
    "improvement_trend": {
      "direction": "improving",
      "percentage": 12.5
    }
  }
}
```

### 5.4 获取成就徽章
```http
GET /learning/badges
Authorization: Bearer {token}
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "earned_badges": [
      {
        "badge_id": "badge_001",
        "name": "学习新手",
        "description": "完成第一节课",
        "icon_url": "https://cdn.example.com/badges/beginner.png",
        "badge_type": "milestone",
        "rarity": "common",
        "points": 10,
        "earned_at": "2024-10-01T10:00:00Z"
      },
      {
        "badge_id": "badge_015",
        "name": "连续学习7天",
        "description": "坚持连续7天上课",
        "icon_url": "https://cdn.example.com/badges/streak7.png",
        "badge_type": "streak",
        "rarity": "uncommon",
        "points": 50,
        "earned_at": "2024-10-20T10:00:00Z"
      }
    ],
    "available_badges": [
      {
        "badge_id": "badge_020",
        "name": "数学大师",
        "description": "数学科目得分达到90分以上10次",
        "icon_url": "https://cdn.example.com/badges/math_master.png",
        "badge_type": "mastery",
        "rarity": "rare",
        "points": 100,
        "progress": {
          "current": 7,
          "required": 10
        }
      }
    ],
    "total_points": 450,
    "total_earned": 8
  }
}
```

---

## 6. WebSocket 实时通信 API

### 6.1 连接WebSocket
```
wss://api.aiteaching.example.com/ws/classrooms/{classroom_id}?token={websocket_token}
```

### 6.2 消息格式

#### 客户端发送消息格式
```json
{
  "type": "message",
  "event": "send_text|send_audio|start_speaking|stop_speaking|heartbeat",
  "data": {},
  "timestamp": "2024-11-08T14:01:00Z",
  "message_id": "client_msg_001"
}
```

#### 服务器响应消息格式
```json
{
  "type": "message|event|error|system",
  "event": "message_received|ai_response|session_started|session_ended|error",
  "data": {},
  "timestamp": "2024-11-08T14:01:02Z",
  "message_id": "server_msg_001"
}
```

### 6.3 WebSocket 事件类型

#### 6.3.1 客户端 -> 服务器

**发送文本消息**
```json
{
  "type": "message",
  "event": "send_text",
  "data": {
    "content": "老师，这道题怎么做？"
  },
  "message_id": "client_msg_001"
}
```

**发送音频消息**
```json
{
  "type": "message",
  "event": "send_audio",
  "data": {
    "audio_data": "base64_encoded_audio_chunk",
    "audio_format": "pcm16",
    "sample_rate": 16000,
    "is_final": false
  },
  "message_id": "client_msg_002"
}
```

**开始说话 (VAD)**
```json
{
  "type": "event",
  "event": "start_speaking",
  "data": {},
  "message_id": "client_event_001"
}
```

**停止说话 (VAD)**
```json
{
  "type": "event",
  "event": "stop_speaking",
  "data": {},
  "message_id": "client_event_002"
}
```

**打断AI回答**
```json
{
  "type": "event",
  "event": "interrupt",
  "data": {},
  "message_id": "client_event_003"
}
```

**心跳**
```json
{
  "type": "event",
  "event": "heartbeat",
  "data": {},
  "message_id": "client_heartbeat_001"
}
```

#### 6.3.2 服务器 -> 客户端

**会话开始**
```json
{
  "type": "system",
  "event": "session_started",
  "data": {
    "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
    "ai_teacher": {
      "display_name": "小明数学老师",
      "avatar_url": "https://cdn.example.com/teachers/math1.jpg"
    },
    "greeting": "你好！我是小明老师，今天我们学习一元二次方程。"
  },
  "timestamp": "2024-11-08T14:00:30Z"
}
```

**消息接收确认**
```json
{
  "type": "system",
  "event": "message_received",
  "data": {
    "client_message_id": "client_msg_001",
    "server_message_id": "msg_001",
    "status": "processing"
  },
  "timestamp": "2024-11-08T14:01:00Z"
}
```

**AI文本回复**
```json
{
  "type": "message",
  "event": "ai_text_response",
  "data": {
    "message_id": "msg_002",
    "content": "让我来帮你解答这道题...",
    "is_final": true
  },
  "timestamp": "2024-11-08T14:01:02Z"
}
```

**AI音频回复**
```json
{
  "type": "message",
  "event": "ai_audio_response",
  "data": {
    "message_id": "msg_002",
    "audio_data": "base64_encoded_audio_chunk",
    "audio_format": "pcm16",
    "sample_rate": 24000,
    "is_final": false,
    "sequence": 1
  },
  "timestamp": "2024-11-08T14:01:02Z"
}
```

**AI流式文本（打字效果）**
```json
{
  "type": "message",
  "event": "ai_text_delta",
  "data": {
    "message_id": "msg_003",
    "delta": "让我",
    "is_final": false
  },
  "timestamp": "2024-11-08T14:01:02.100Z"
}
```

**转录结果 (STT)**
```json
{
  "type": "event",
  "event": "transcription",
  "data": {
    "text": "老师，这道题怎么做？",
    "is_final": true,
    "confidence": 0.95,
    "language": "zh-CN"
  },
  "timestamp": "2024-11-08T14:01:00.500Z"
}
```

**中间转录结果**
```json
{
  "type": "event",
  "event": "interim_transcription",
  "data": {
    "text": "老师这道",
    "is_final": false,
    "confidence": 0.75
  },
  "timestamp": "2024-11-08T14:01:00.200Z"
}
```

**AI开始思考**
```json
{
  "type": "event",
  "event": "ai_thinking",
  "data": {
    "message": "正在思考..."
  },
  "timestamp": "2024-11-08T14:01:01Z"
}
```

**错误通知**
```json
{
  "type": "error",
  "event": "error",
  "data": {
    "code": "AUDIO_PROCESSING_ERROR",
    "message": "音频处理失败，请重试",
    "details": {},
    "recoverable": true
  },
  "timestamp": "2024-11-08T14:01:05Z"
}
```

**会话结束**
```json
{
  "type": "system",
  "event": "session_ended",
  "data": {
    "reason": "student_ended",
    "duration_seconds": 3870,
    "message_count": 45,
    "summary": "本次课程已结束，感谢你的参与！"
  },
  "timestamp": "2024-11-08T15:05:00Z"
}
```

---

## 7. 管理员 API

### 7.1 获取系统统计
```http
GET /admin/statistics
Authorization: Bearer {admin_token}

Query Parameters:
- period: string (default: today) - today, week, month, year
```

**Response: 200 OK**
```json
{
  "success": true,
  "data": {
    "period": "today",
    "active_classrooms": 127,
    "total_students_online": 127,
    "total_sessions_today": 456,
    "total_messages_today": 12450,
    "average_session_duration_minutes": 45,
    "peak_concurrent_sessions": 145,
    "system_health": {
      "status": "healthy",
      "cpu_usage": 45.2,
      "memory_usage": 62.8,
      "websocket_connections": 254
    }
  }
}
```

### 7.2 获取所有教室
```http
GET /admin/classrooms
Authorization: Bearer {admin_token}

Query Parameters:
- status: string (optional)
- page: integer
- page_size: integer
```

### 7.3 强制结束教室
```http
POST /admin/classrooms/{classroom_id}/force-end
Authorization: Bearer {admin_token}
```

---

## 8. Webhook 通知

系统可以向配置的URL发送webhook通知。

### 8.1 配置Webhook
```http
POST /webhooks
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "url": "https://yourapp.com/webhooks/ai-teaching",
  "events": ["classroom.started", "classroom.ended", "assessment.created"],
  "secret": "your_webhook_secret"
}
```

### 8.2 Webhook事件格式

**教室开始**
```json
{
  "event": "classroom.started",
  "data": {
    "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
    "student_id": "550e8400-e29b-41d4-a716-446655440000",
    "ai_teacher_id": "660e8400-e29b-41d4-a716-446655440000",
    "started_at": "2024-11-08T14:00:30Z"
  },
  "timestamp": "2024-11-08T14:00:30Z",
  "signature": "sha256=..."
}
```

**教室结束**
```json
{
  "event": "classroom.ended",
  "data": {
    "classroom_id": "770e8400-e29b-41d4-a716-446655440000",
    "duration_seconds": 3870,
    "message_count": 45,
    "ended_at": "2024-11-08T15:05:00Z"
  },
  "timestamp": "2024-11-08T15:05:00Z",
  "signature": "sha256=..."
}
```

---

## 9. 速率限制

### 9.1 限制规则
- 认证端点: 5 请求/分钟
- 一般API: 100 请求/分钟
- WebSocket消息: 60 消息/分钟
- 文件上传: 10 请求/小时

### 9.2 响应头
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699445460
```

### 9.3 超限响应
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after": 30
  }
}
```

---

## 10. 错误代码

| 错误代码 | HTTP状态 | 描述 |
|---------|---------|------|
| `UNAUTHORIZED` | 401 | 未认证或令牌无效 |
| `FORBIDDEN` | 403 | 无权限访问资源 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `CLASSROOM_NOT_FOUND` | 404 | 教室不存在 |
| `CLASSROOM_ALREADY_ACTIVE` | 409 | 教室已激活 |
| `CLASSROOM_ALREADY_ENDED` | 409 | 教室已结束 |
| `AI_TEACHER_NOT_FOUND` | 404 | AI教师不存在 |
| `AI_TEACHER_UNAVAILABLE` | 503 | AI教师服务不可用 |
| `AUDIO_PROCESSING_ERROR` | 500 | 音频处理错误 |
| `STT_SERVICE_ERROR` | 503 | 语音识别服务错误 |
| `TTS_SERVICE_ERROR` | 503 | 语音合成服务错误 |
| `LLM_SERVICE_ERROR` | 503 | LLM服务错误 |
| `WEBSOCKET_CONNECTION_ERROR` | 500 | WebSocket连接错误 |
| `RATE_LIMIT_EXCEEDED` | 429 | 超过速率限制 |
| `INTERNAL_SERVER_ERROR` | 500 | 内部服务器错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂时不可用 |

---

## API变更日志

### v1.0.0 (2024-11-08)
- 初始API版本
- 完整的教室管理功能
- WebSocket实时通信
- 学习分析API
