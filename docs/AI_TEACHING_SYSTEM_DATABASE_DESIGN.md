# AI 在线教学系统 - 数据库架构设计

## 概述
本文档定义了支持多教室、多学生同时在线的1对1 AI教学系统的完整数据库架构。

## 技术栈
- **主数据库**: PostgreSQL 15+
- **缓存**: Redis 7+
- **会话存储**: Redis (WebSocket会话)
- **文件存储**: S3兼容对象存储

---

## 数据库模式设计

### 1. 用户管理模块

#### 1.1 users (用户表)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### 1.2 user_profiles (用户详细资料)
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    grade_level VARCHAR(50), -- 年级: elementary, middle, high, college
    learning_style VARCHAR(50), -- visual, auditory, kinesthetic, reading
    preferred_subjects TEXT[], -- 偏好科目
    learning_goals TEXT[],
    special_needs TEXT,
    parent_email VARCHAR(255),
    parent_phone VARCHAR(20),
    school_name VARCHAR(200),
    country VARCHAR(100),
    state_province VARCHAR(100),
    city VARCHAR(100),
    bio TEXT,
    interests TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE UNIQUE INDEX idx_user_profiles_user_id_unique ON user_profiles(user_id);
```

#### 1.3 user_settings (用户设置)
```sql
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, setting_key)
);

CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
```

---

### 2. AI教师配置模块

#### 2.1 ai_teachers (AI教师模板)
```sql
CREATE TABLE ai_teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(100) NOT NULL, -- math, science, english, etc.
    grade_levels VARCHAR(50)[], -- elementary, middle, high, college
    avatar_url TEXT,
    voice_id VARCHAR(100), -- TTS voice identifier
    voice_provider VARCHAR(50), -- elevenlabs, openai, google, etc.
    personality_traits JSONB DEFAULT '{}'::jsonb,
    teaching_style VARCHAR(50), -- patient, encouraging, challenging, adaptive
    language VARCHAR(10) DEFAULT 'zh-CN',

    -- AI Model Configuration
    llm_provider VARCHAR(50) NOT NULL, -- openai, anthropic, google
    llm_model VARCHAR(100) NOT NULL, -- gpt-4, claude-3-opus, gemini-pro
    llm_temperature DECIMAL(3,2) DEFAULT 0.7,
    llm_max_tokens INTEGER DEFAULT 2000,

    -- System Prompt
    system_prompt TEXT NOT NULL,
    conversation_starters TEXT[],

    -- Capabilities
    supports_voice BOOLEAN DEFAULT TRUE,
    supports_video BOOLEAN DEFAULT FALSE,
    supports_screen_share BOOLEAN DEFAULT FALSE,
    supports_whiteboard BOOLEAN DEFAULT TRUE,
    supports_file_upload BOOLEAN DEFAULT TRUE,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ai_teachers_subject ON ai_teachers(subject);
CREATE INDEX idx_ai_teachers_is_active ON ai_teachers(is_active);
CREATE INDEX idx_ai_teachers_created_by ON ai_teachers(created_by);
```

#### 2.2 ai_teacher_knowledge_base (AI教师知识库)
```sql
CREATE TABLE ai_teacher_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ai_teacher_id UUID NOT NULL REFERENCES ai_teachers(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50), -- lesson, faq, example, reference
    subject_area VARCHAR(100),
    difficulty_level VARCHAR(20), -- beginner, intermediate, advanced
    tags TEXT[],
    file_urls TEXT[],
    embedding_vector vector(1536), -- for semantic search (pgvector extension)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_teacher_kb_teacher_id ON ai_teacher_knowledge_base(ai_teacher_id);
CREATE INDEX idx_ai_teacher_kb_subject ON ai_teacher_knowledge_base(subject_area);
CREATE INDEX idx_ai_teacher_kb_tags ON ai_teacher_knowledge_base USING GIN(tags);
-- CREATE INDEX idx_ai_teacher_kb_vector ON ai_teacher_knowledge_base USING ivfflat(embedding_vector);
```

---

### 3. 教室管理模块

#### 3.1 classrooms (教室/会话)
```sql
CREATE TABLE classrooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Info
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Participants
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ai_teacher_id UUID NOT NULL REFERENCES ai_teachers(id) ON DELETE RESTRICT,

    -- Session Configuration
    subject VARCHAR(100) NOT NULL,
    lesson_topic VARCHAR(500),
    learning_objectives TEXT[],
    duration_minutes INTEGER, -- planned duration

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'active', 'paused', 'completed', 'cancelled', 'error')),

    -- WebRTC / Transport Configuration
    transport_type VARCHAR(50) DEFAULT 'daily', -- daily, livekit, webrtc, websocket
    room_url TEXT, -- Daily.co room URL or similar
    room_token TEXT, -- Access token for student
    room_config JSONB DEFAULT '{}'::jsonb,

    -- Timing
    scheduled_start_at TIMESTAMP WITH TIME ZONE,
    actual_start_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,

    -- Analytics
    total_messages INTEGER DEFAULT 0,
    student_messages INTEGER DEFAULT 0,
    ai_messages INTEGER DEFAULT 0,
    total_audio_duration_seconds INTEGER DEFAULT 0,

    -- Quality Metrics
    average_response_time_ms INTEGER,
    interruption_count INTEGER DEFAULT 0,
    technical_issues_count INTEGER DEFAULT 0,

    -- Recording
    recording_enabled BOOLEAN DEFAULT FALSE,
    recording_url TEXT,
    transcript_url TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_classrooms_student_id ON classrooms(student_id);
CREATE INDEX idx_classrooms_ai_teacher_id ON classrooms(ai_teacher_id);
CREATE INDEX idx_classrooms_status ON classrooms(status);
CREATE INDEX idx_classrooms_scheduled_start ON classrooms(scheduled_start_at);
CREATE INDEX idx_classrooms_actual_start ON classrooms(actual_start_at);
CREATE INDEX idx_classrooms_created_at ON classrooms(created_at);
```

#### 3.2 classroom_participants (教室参与者 - 支持多人扩展)
```sql
CREATE TABLE classroom_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    participant_type VARCHAR(50) NOT NULL CHECK (participant_type IN ('student', 'observer', 'assistant')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP WITH TIME ZONE,
    total_time_seconds INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_classroom_participants_classroom_id ON classroom_participants(classroom_id);
CREATE INDEX idx_classroom_participants_user_id ON classroom_participants(user_id);
CREATE UNIQUE INDEX idx_classroom_participants_unique ON classroom_participants(classroom_id, user_id)
    WHERE left_at IS NULL;
```

#### 3.3 classroom_resources (教室资源)
```sql
CREATE TABLE classroom_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- pdf, image, video, link, whiteboard, code
    title VARCHAR(500),
    file_url TEXT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    thumbnail_url TEXT,
    content TEXT, -- for text content or code
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_classroom_resources_classroom_id ON classroom_resources(classroom_id);
CREATE INDEX idx_classroom_resources_type ON classroom_resources(resource_type);
```

---

### 4. 对话历史模块

#### 4.1 conversation_messages (对话消息)
```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,

    -- Message Info
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('text', 'audio', 'image', 'system', 'tool_call', 'tool_response')),
    role VARCHAR(50) NOT NULL CHECK (role IN ('student', 'assistant', 'system', 'tool')),

    -- Content
    content TEXT,
    content_json JSONB, -- for structured content
    audio_url TEXT,
    audio_duration_seconds DECIMAL(10,2),
    image_url TEXT,

    -- Transcription (for audio messages)
    transcript TEXT,
    transcript_confidence DECIMAL(5,4),

    -- LLM Context
    llm_model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,

    -- Metadata
    parent_message_id UUID REFERENCES conversation_messages(id),
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_messages_classroom_id ON conversation_messages(classroom_id);
CREATE INDEX idx_conversation_messages_timestamp ON conversation_messages(timestamp);
CREATE INDEX idx_conversation_messages_role ON conversation_messages(role);
CREATE INDEX idx_conversation_messages_parent ON conversation_messages(parent_message_id);

-- Partitioning by month for scalability
CREATE TABLE conversation_messages_2024_11 PARTITION OF conversation_messages
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
```

#### 4.2 conversation_turns (对话轮次)
```sql
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,

    -- Student Input
    student_message_id UUID REFERENCES conversation_messages(id),
    student_input_text TEXT,
    student_audio_url TEXT,

    -- AI Response
    ai_message_id UUID REFERENCES conversation_messages(id),
    ai_response_text TEXT,
    ai_audio_url TEXT,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    response_time_ms INTEGER,

    -- Quality
    was_interrupted BOOLEAN DEFAULT FALSE,
    had_error BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_turns_classroom_id ON conversation_turns(classroom_id);
CREATE INDEX idx_conversation_turns_number ON conversation_turns(classroom_id, turn_number);
```

---

### 5. 学习分析模块

#### 5.1 learning_assessments (学习评估)
```sql
CREATE TABLE learning_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Assessment Type
    assessment_type VARCHAR(50) NOT NULL, -- formative, summative, diagnostic

    -- Scores
    overall_score DECIMAL(5,2), -- 0-100
    engagement_score DECIMAL(5,2),
    comprehension_score DECIMAL(5,2),
    participation_score DECIMAL(5,2),

    -- Detailed Analysis
    strengths TEXT[],
    weaknesses TEXT[],
    recommendations TEXT[],

    -- AI Analysis
    ai_summary TEXT,
    ai_feedback JSONB,

    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assessed_by VARCHAR(50), -- 'ai_auto', 'teacher', 'system'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_learning_assessments_classroom_id ON learning_assessments(classroom_id);
CREATE INDEX idx_learning_assessments_student_id ON learning_assessments(student_id);
CREATE INDEX idx_learning_assessments_assessed_at ON learning_assessments(assessed_at);
```

#### 5.2 learning_progress (学习进度)
```sql
CREATE TABLE learning_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(100) NOT NULL,

    -- Progress Metrics
    total_sessions INTEGER DEFAULT 0,
    total_duration_minutes INTEGER DEFAULT 0,
    current_level VARCHAR(50), -- beginner, intermediate, advanced
    progress_percentage DECIMAL(5,2), -- 0-100

    -- Mastery
    topics_mastered TEXT[],
    topics_in_progress TEXT[],
    topics_not_started TEXT[],

    -- Statistics
    average_session_score DECIMAL(5,2),
    total_messages_sent INTEGER DEFAULT 0,
    total_questions_asked INTEGER DEFAULT 0,

    last_session_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, subject)
);

CREATE INDEX idx_learning_progress_student_id ON learning_progress(student_id);
CREATE INDEX idx_learning_progress_subject ON learning_progress(subject);
```

#### 5.3 achievement_badges (成就徽章)
```sql
CREATE TABLE achievement_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon_url TEXT,
    badge_type VARCHAR(50), -- milestone, streak, mastery, special
    criteria JSONB NOT NULL,
    points INTEGER DEFAULT 0,
    rarity VARCHAR(20) DEFAULT 'common', -- common, uncommon, rare, epic, legendary
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id UUID NOT NULL REFERENCES achievement_badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(user_id, badge_id)
);

CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX idx_user_badges_earned_at ON user_badges(earned_at);
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(200) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    api_key_prefix VARCHAR(20) NOT NULL,

    -- Permissions
    scopes TEXT[], -- read:classrooms, write:classrooms, read:messages, etc.

    -- Rate Limiting
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 1000,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(api_key_hash);
```

#### 7.2 audit_logs (审计日志)
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_status INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Partitioning by month
CREATE TABLE audit_logs_2024_11 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
```

#### 7.3 system_config (系统配置)
```sql
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(200) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 数据库优化策略

### 1. 分区策略
- `conversation_messages`: 按月分区
- `audit_logs`: 按月分区
- 自动归档超过1年的历史数据

### 2. 索引优化
- B-Tree索引用于精确查找和范围查询
- GIN索引用于JSONB和数组字段
- 部分索引用于频繁查询的条件组合

### 3. 缓存策略
- Redis缓存热点数据（活跃会话、用户状态）
- 消息列表缓存最近100条
- 用户设置缓存30分钟

### 4. 备份策略
- 每日全量备份
- 每小时增量备份
- 30天保留周期

### 5. 数据归档
- 完成超过90天的教室归档到冷存储
- 保留最近6个月的消息记录
- 学习数据永久保留

---

## 扩展性考虑

### 1. 分片策略
- 按 `student_id` 哈希分片
- 支持水平扩展到多个数据库实例

### 2. 读写分离
- 主库处理写操作
- 只读副本处理查询和报表

### 3. 消息队列
- 使用 RabbitMQ/Kafka 处理异步任务
- 解耦教室创建、录音处理、分析计算

### 4. CDN加速
- 音频文件通过CDN分发
- 头像、资源文件使用对象存储+CDN

---

## 性能指标

- 支持 **10,000+** 并发教室
- 消息延迟 < 100ms
- 数据库查询 < 50ms (99th percentile)
- WebSocket连接支持 100,000+ 并发
