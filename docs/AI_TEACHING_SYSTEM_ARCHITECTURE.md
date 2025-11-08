# AI 在线教学系统 - 系统架构与部署方案

## 系统概述

这是一个基于Pipecat框架构建的多租户1对1 AI在线教学平台，支持数千个教室同时运行，提供实时语音对话、消息、白板、资源共享等功能。

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户层 (User Layer)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  Web Browser  │  Mobile App  │  Desktop App  │  Tablet                  │
│  (React PWA)  │  (React Native) │  (Electron)  │                        │
└────────┬──────────────┬────────────┬─────────────────────────────────────┘
         │              │            │
         ├──────────────┴────────────┘
         │  HTTPS / WSS
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CDN层 (CDN Layer)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  Cloudflare CDN                                                          │
│  - 静态资源加速                                                           │
│  - DDoS防护                                                              │
│  - SSL/TLS终止                                                           │
│  - 地理路由                                                              │
└────────┬────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       负载均衡层 (Load Balancer)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  AWS ALB / NGINX Plus                                                    │
│  - HTTP/HTTPS负载均衡                                                     │
│  - WebSocket连接路由                                                      │
│  - 健康检查                                                               │
│  - SSL卸载                                                               │
└────────┬────────────────┬────────────────────────────────────────────────┘
         │                │
    ┌────┴────┐      ┌────┴────┐
    │         │      │         │
    ▼         ▼      ▼         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        应用层 (Application Layer)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────────┐ │
│  │  API服务器 (x3+)    │  │  WebSocket服务器    │  │  Bot管理服务器     │ │
│  │  FastAPI           │  │  (x5+)             │  │  (x10+)           │ │
│  │                    │  │  FastAPI +         │  │  Pipecat Runner   │ │
│  │  - REST API        │  │  WebSocket         │  │                   │ │
│  │  - 用户认证         │  │                    │  │  每个Bot处理一个   │ │
│  │  - 教室管理         │  │  - 消息路由        │  │  1:1教室会话      │ │
│  │  - 学习分析         │  │  - 会话状态        │  │                   │ │
│  │  - 资源管理         │  │  - 实时事件        │  │  - Pipeline执行   │ │
│  └────────────────────┘  └────────────────────┘  │  - STT/LLM/TTS    │ │
│                                                   │  - 音频处理       │ │
│                                                   │  - WebRTC管理     │ │
│                                                   └───────────────────┘ │
│                                                                          │
└────────┬──────────────────┬──────────────────────┬───────────────────────┘
         │                  │                      │
         ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        缓存层 (Cache Layer)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  Redis Cluster (x3 masters, x3 replicas)                                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐                 │
│  │ 会话缓存     │  │ 消息队列     │  │ 实时状态       │                 │
│  │ Session     │  │ Pub/Sub      │  │ User Online    │                 │
│  └─────────────┘  └──────────────┘  └────────────────┘                 │
└────────┬────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       数据层 (Data Layer)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  MySQL 8.0 (Primary + 2 Replicas)                                       │
│  ┌──────────────────┐  ┌──────────────────┐                            │
│  │  Primary (写)     │  │  Replica (读)     │                            │
│  │  - 用户数据       │  │  - 查询负载       │                            │
│  │  - 教室数据       │  │  - 分析查询       │                            │
│  │  - 消息记录       │  │  - 报表生成       │                            │
│  └──────────────────┘  └──────────────────┘                            │
│                                                                          │
│  InnoDB引擎 (事务支持)                                                     │
│  JSON原生支持 (灵活数据)                                                   │
└────────┬────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      存储层 (Storage Layer)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  S3兼容对象存储                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ 音频文件      │  │ 录音文件      │  │ 用户资源      │                  │
│  │ Audio Files  │  │ Recordings   │  │ User Files   │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      外部服务层 (External Services)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐     │
│  │ OpenAI     │  │ Deepgram   │  │ ElevenLabs │  │ Daily.co     │     │
│  │ (LLM)      │  │ (STT)      │  │ (TTS)      │  │ (WebRTC)     │     │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘     │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                        │
│  │ Anthropic  │  │ Azure      │  │ Sentry     │                        │
│  │ (LLM)      │  │ (STT/TTS)  │  │ (监控)      │                        │
│  └────────────┘  └────────────┘  └────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      消息队列层 (Message Queue)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  RabbitMQ / AWS SQS                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ 录音处理队列  │  │ 分析队列      │  │ 通知队列      │                  │
│  │ Recording    │  │ Analytics    │  │ Notification │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      监控层 (Monitoring Layer)                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐     │
│  │ Prometheus │  │ Grafana    │  │ ELK Stack  │  │ Sentry       │     │
│  │ (指标)      │  │ (可视化)    │  │ (日志)      │  │ (错误追踪)    │     │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 核心组件详解

### 1. API服务器 (FastAPI)

**技术栈**:
- FastAPI 0.104+
- Python 3.11+
- SQLAlchemy 2.0
- Alembic (数据库迁移)
- Pydantic v2 (数据验证)

**职责**:
- REST API端点
- 用户认证与授权 (JWT)
- 教室CRUD操作
- AI教师管理
- 学习分析查询
- 资源上传下载
- Webhook管理

**水平扩展**:
- 无状态设计，可任意扩展
- 使用Redis共享会话
- 通过负载均衡器分发请求

**目录结构**:
```
api-server/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── classrooms.py
│   │   │   ├── teachers.py
│   │   │   └── learning.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
├── tests/
├── requirements.txt
└── Dockerfile
```

---

### 2. WebSocket服务器

**技术栈**:
- FastAPI WebSocket
- Redis Pub/Sub (消息广播)
- aioredis (异步Redis客户端)

**职责**:
- 维护客户端WebSocket连接
- 路由消息到Bot服务器
- 广播实时事件
- 管理在线状态
- 心跳检测

**连接管理**:
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.classroom_connections: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, classroom_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        if classroom_id not in self.classroom_connections:
            self.classroom_connections[classroom_id] = set()
        self.classroom_connections[classroom_id].add(user_id)

    async def broadcast_to_classroom(self, classroom_id: str, message: dict):
        if classroom_id in self.classroom_connections:
            for user_id in self.classroom_connections[classroom_id]:
                if user_id in self.active_connections:
                    await self.active_connections[user_id].send_json(message)
```

**扩展策略**:
- 使用Redis Pub/Sub跨服务器广播
- 使用一致性哈希路由连接
- 支持5万+ 并发WebSocket连接 (单服务器)

---

### 3. Bot管理服务器 (Pipecat Runner)

**技术栈**:
- Pipecat Framework
- Python 3.11+
- asyncio
- Daily.co SDK / LiveKit SDK

**职责**:
- 为每个教室创建独立的Pipecat Pipeline
- 管理STT/LLM/TTS服务链
- 处理音频流
- WebRTC房间管理
- 录音和转录

**Pipeline架构**:
```python
async def create_classroom_pipeline(classroom_id: str, config: ClassroomConfig):
    # Transport (Daily.co WebRTC)
    transport = DailyTransport(
        room_url=config.room_url,
        token=config.room_token,
        bot_name=config.ai_teacher.display_name,
    )

    # STT Service
    stt = DeepgramSTTService(api_key=config.deepgram_key)

    # LLM Service
    llm = OpenAILLMService(
        api_key=config.openai_key,
        model=config.ai_teacher.llm_model,
        system_prompt=config.ai_teacher.system_prompt,
    )

    # TTS Service
    tts = ElevenLabsTTSService(
        api_key=config.elevenlabs_key,
        voice_id=config.ai_teacher.voice_id,
    )

    # Create Pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        tts,
        transport.output(),
    ])

    # Add processors
    pipeline.add_processor(ConversationLogger(classroom_id))
    pipeline.add_processor(MetricsCollector(classroom_id))

    # Run
    task = PipelineTask(pipeline)
    await PipelineRunner().run(task)
```

**Bot生命周期管理**:
```python
class BotManager:
    def __init__(self):
        self.active_bots: Dict[str, PipelineTask] = {}

    async def start_bot(self, classroom_id: str, config: ClassroomConfig):
        if classroom_id in self.active_bots:
            raise ValueError(f"Bot already running for classroom {classroom_id}")

        task = await create_classroom_pipeline(classroom_id, config)
        self.active_bots[classroom_id] = task

    async def stop_bot(self, classroom_id: str):
        if classroom_id in self.active_bots:
            task = self.active_bots[classroom_id]
            await task.cancel()
            del self.active_bots[classroom_id]

    def get_bot_status(self, classroom_id: str):
        return classroom_id in self.active_bots
```

**水平扩展**:
- 每个Bot服务器可运行50-100个并发Bot
- 使用Kubernetes HPA自动扩展
- Bot分配策略: 最少连接数优先

---

### 4. 数据库设计 (MySQL 8)

**主从架构**:
- 1个主节点 (写操作)
- 2个从节点 (读操作)
- GTID复制 (全局事务ID)
- 自动故障转移 (MHA或Orchestrator)

**分区策略**:
```sql
-- 按月分区消息表
CREATE TABLE conversation_messages (
    id CHAR(36),
    classroom_id CHAR(36),
    content TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY (id, created_at)
) ENGINE=InnoDB
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202411 VALUES LESS THAN (202412),
    PARTITION p202412 VALUES LESS THAN (202501),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

**索引优化**:
```sql
-- 复合索引
CREATE INDEX idx_classrooms_student_status
    ON classrooms(student_id, status, scheduled_start_at);

-- 函数索引 (MySQL 8.0.13+)
CREATE INDEX idx_classrooms_email_lower
    ON classrooms((LOWER(email)));

-- 全文索引
CREATE FULLTEXT INDEX idx_classrooms_content
    ON classrooms(name, description);
```

**连接池配置**:
```python
# SQLAlchemy with MySQL
engine = create_engine(
    "mysql+pymysql://user:pass@localhost/ai_teaching?charset=utf8mb4",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

---

### 5. Redis集群

**集群配置**:
- 3个主节点
- 3个从节点
- 哨兵模式 (高可用)

**使用场景**:

**会话缓存**:
```python
# 存储活跃教室会话
await redis.hset(
    f"session:{classroom_id}",
    mapping={
        "student_id": student_id,
        "ai_teacher_id": ai_teacher_id,
        "started_at": datetime.now().isoformat(),
        "status": "active",
    },
)
await redis.expire(f"session:{classroom_id}", 86400)  # 24小时
```

**用户在线状态**:
```python
# 用户上线
await redis.setex(f"user:online:{user_id}", 300, "online")

# 获取在线用户
online_users = await redis.keys("user:online:*")
```

**消息队列 (Pub/Sub)**:
```python
# 发布消息到教室
await redis.publish(
    f"classroom:{classroom_id}",
    json.dumps({
        "event": "new_message",
        "data": message_data,
    }),
)

# 订阅教室消息
pubsub = redis.pubsub()
await pubsub.subscribe(f"classroom:{classroom_id}")
async for message in pubsub.listen():
    # 处理消息
    pass
```

**限流 (Rate Limiting)**:
```python
# 使用滑动窗口限流
async def check_rate_limit(user_id: str, limit: int = 60) -> bool:
    key = f"ratelimit:{user_id}:{int(time.time() // 60)}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
    return current <= limit
```

---

## 部署架构

### 1. Kubernetes部署

**集群配置**:
- 3个主节点 (控制平面)
- 10+ 工作节点 (可扩展)
- 使用Kubernetes 1.28+

**Namespace划分**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-teaching-prod
---
apiVersion: v1
kind: Namespace
metadata:
  name: ai-teaching-staging
```

**API服务器部署**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: ai-teaching-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api
        image: ai-teaching/api-server:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-server
  namespace: ai-teaching-prod
spec:
  selector:
    app: api-server
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

**Bot管理服务器部署**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bot-manager
  namespace: ai-teaching-prod
spec:
  replicas: 10  # 根据负载自动扩展
  selector:
    matchLabels:
      app: bot-manager
  template:
    metadata:
      labels:
        app: bot-manager
    spec:
      containers:
      - name: bot
        image: ai-teaching/bot-manager:v1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: MAX_CONCURRENT_BOTS
          value: "50"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-services-secret
              key: openai-key
        - name: DEEPGRAM_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-services-secret
              key: deepgram-key
        - name: ELEVENLABS_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-services-secret
              key: elevenlabs-key
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bot-manager-hpa
  namespace: ai-teaching-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bot-manager
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**WebSocket服务器部署**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: websocket-server
  namespace: ai-teaching-prod
spec:
  replicas: 5
  selector:
    matchLabels:
      app: websocket-server
  template:
    metadata:
      labels:
        app: websocket-server
    spec:
      containers:
      - name: websocket
        image: ai-teaching/websocket-server:v1.0.0
        ports:
        - containerPort: 8002
        env:
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 3000m
            memory: 6Gi
```

**Ingress配置**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-teaching-ingress
  namespace: ai-teaching-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/websocket-services: websocket-server
spec:
  tls:
  - hosts:
    - api.aiteaching.example.com
    secretName: api-tls
  rules:
  - host: api.aiteaching.example.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: api-server
            port:
              number: 80
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: websocket-server
            port:
              number: 8002
```

---

### 2. Docker Compose (开发环境)

```yaml
version: '3.8'

services:
  # API服务器
  api-server:
    build: ./api-server
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: mysql+pymysql://user:pass@mysql:3306/ai_teaching?charset=utf8mb4
      REDIS_URL: redis://redis:6379
    depends_on:
      - mysql
      - redis
    volumes:
      - ./api-server:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # WebSocket服务器
  websocket-server:
    build: ./websocket-server
    ports:
      - "8002:8002"
    environment:
      REDIS_URL: redis://redis:6379
    depends_on:
      - redis

  # Bot管理服务器
  bot-manager:
    build: ./bot-manager
    ports:
      - "8001:8001"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY}
      ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY}
    depends_on:
      - redis

  # MySQL
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: ai_teaching
      MYSQL_USER: user
      MYSQL_PASSWORD: pass
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # 前端
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

  # NGINX (反向代理)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api-server
      - websocket-server
      - frontend

volumes:
  mysql_data:
  redis_data:
```

---

### 3. CI/CD流程

**GitHub Actions**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=app tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker images
        run: |
          docker build -t ai-teaching/api-server:${{ github.sha }} ./api-server
          docker build -t ai-teaching/bot-manager:${{ github.sha }} ./bot-manager
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ai-teaching/api-server:${{ github.sha }}
          docker push ai-teaching/bot-manager:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v4
        with:
          manifests: |
            k8s/api-server.yaml
            k8s/bot-manager.yaml
          images: |
            ai-teaching/api-server:${{ github.sha }}
            ai-teaching/bot-manager:${{ github.sha }}
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
```

---

## 监控与告警

### 1. Prometheus + Grafana

**指标收集**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 计数器
active_classrooms = Gauge('active_classrooms', 'Number of active classrooms')
total_messages = Counter('total_messages', 'Total messages sent')
websocket_connections = Gauge('websocket_connections', 'Active WebSocket connections')

# 直方图
api_latency = Histogram('api_request_duration_seconds', 'API request latency')
bot_response_time = Histogram('bot_response_time_seconds', 'Bot response time')
```

**Grafana仪表盘**:
- 系统概览 (活跃教室、在线用户、消息数)
- 性能指标 (API延迟、Bot响应时间)
- 资源使用 (CPU、内存、网络)
- 错误率和成功率
- 用户行为分析

### 2. 日志管理 (ELK Stack)

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

logger.info("Classroom started", extra={
    "classroom_id": classroom_id,
    "student_id": student_id,
    "ai_teacher_id": ai_teacher_id,
})
```

### 3. 错误追踪 (Sentry)

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://...@sentry.io/...",
    traces_sample_rate=0.1,
    environment="production",
)
```

---

## 安全策略

### 1. 认证与授权
- JWT令牌认证
- 刷新令牌机制
- API密钥管理
- RBAC权限控制

### 2. 网络安全
- HTTPS/WSS加密传输
- CORS配置
- Rate Limiting
- DDoS防护 (Cloudflare)

### 3. 数据安全
- 数据库加密
- 敏感数据脱敏
- 定期备份
- 访问审计日志

---

## 成本估算 (月度)

**云服务 (AWS)**:
- EC2 (Kubernetes工作节点): $2,000
- RDS MySQL 8.0: $500
- ElastiCache Redis: $300
- S3存储: $200
- 负载均衡器: $100
- 数据传输: $500

**AI服务**:
- OpenAI API: $5,000 (假设1万节课/月)
- Deepgram STT: $1,000
- ElevenLabs TTS: $2,000
- Daily.co WebRTC: $1,000

**其他**:
- CDN (Cloudflare): $200
- 监控 (Datadog/Sentry): $300
- 域名和证书: $50

**总计**: 约 $13,150/月 (支持1万节课/月)

**单节课成本**: $1.31

---

## 性能指标

- **并发教室**: 10,000+
- **WebSocket连接**: 50,000+
- **API响应时间**: < 50ms (P99)
- **消息延迟**: < 100ms
- **Bot响应时间**: < 1秒 (语音到语音)
- **数据库查询**: < 20ms (P95)
- **系统可用性**: 99.9%

---

## 总结

这个架构设计支持大规模的1对1 AI在线教学场景，具有以下特点:

✅ **高可用**: 无单点故障，自动故障转移
✅ **可扩展**: 水平扩展，支持1万+ 并发教室
✅ **低延迟**: < 100ms消息延迟，实时体验
✅ **成本优化**: 按需扩展，合理控制成本
✅ **安全可靠**: 多层安全防护，数据加密
✅ **可观测**: 完善的监控、日志、告警系统
