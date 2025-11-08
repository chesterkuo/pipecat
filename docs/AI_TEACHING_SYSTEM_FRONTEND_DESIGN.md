# AI 在线教学系统 - 前端组件设计

## 概述
本文档定义了AI在线教学系统的完整前端架构、组件设计和用户界面规范。

## 技术栈

### 核心框架
- **React 18+** - UI框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架

### 状态管理
- **Zustand** - 全局状态管理
- **React Query (TanStack Query)** - 服务器状态管理
- **Jotai** - 原子化状态管理（可选）

### 实时通信
- **WebSocket** - 实时消息
- **Daily.co SDK** / **LiveKit SDK** - WebRTC音视频
- **pipecat-client-react** - Pipecat官方React SDK

### UI组件库
- **Shadcn/ui** - 基础组件
- **Radix UI** - 无样式可访问组件
- **Framer Motion** - 动画库
- **React Icons** - 图标库

### 音频处理
- **Web Audio API** - 音频处理
- **Recorder.js** - 音频录制
- **WaveSurfer.js** - 音频波形可视化

### 其他工具
- **React Router v6** - 路由管理
- **React Hook Form** - 表单管理
- **Zod** - 表单验证
- **date-fns** - 日期处理
- **Recharts** - 数据可视化

---

## 项目结构

```
frontend/
├── public/
│   ├── assets/
│   │   ├── icons/
│   │   ├── images/
│   │   └── sounds/
│   └── index.html
├── src/
│   ├── api/                    # API客户端
│   │   ├── client.ts           # Axios实例
│   │   ├── auth.ts             # 认证API
│   │   ├── classrooms.ts       # 教室API
│   │   ├── teachers.ts         # AI教师API
│   │   ├── learning.ts         # 学习分析API
│   │   └── websocket.ts        # WebSocket客户端
│   ├── components/             # React组件
│   │   ├── auth/               # 认证相关
│   │   ├── classroom/          # 教室相关
│   │   ├── common/             # 通用组件
│   │   ├── dashboard/          # 仪表盘
│   │   ├── layout/             # 布局组件
│   │   ├── learning/           # 学习分析
│   │   └── ui/                 # 基础UI组件
│   ├── hooks/                  # 自定义Hooks
│   │   ├── useAuth.ts
│   │   ├── useClassroom.ts
│   │   ├── useWebSocket.ts
│   │   ├── useAudioRecorder.ts
│   │   └── useVoiceActivity.ts
│   ├── stores/                 # Zustand stores
│   │   ├── authStore.ts
│   │   ├── classroomStore.ts
│   │   └── uiStore.ts
│   ├── types/                  # TypeScript类型定义
│   │   ├── api.ts
│   │   ├── classroom.ts
│   │   ├── message.ts
│   │   └── user.ts
│   ├── utils/                  # 工具函数
│   │   ├── audio.ts
│   │   ├── format.ts
│   │   └── validation.ts
│   ├── pages/                  # 页面组件
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Classroom.tsx
│   │   ├── Profile.tsx
│   │   └── Analytics.tsx
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 核心组件设计

### 1. 认证模块

#### 1.1 LoginForm
**位置**: `src/components/auth/LoginForm.tsx`

**功能**: 用户登录表单

**Props**:
```typescript
interface LoginFormProps {
  onSuccess?: () => void;
  redirectTo?: string;
}
```

**组件代码示例**:
```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';

const loginSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(6, '密码至少6位'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm({ onSuccess, redirectTo = '/dashboard' }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    await login(data.email, data.password);
    onSuccess?.();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          邮箱
        </label>
        <input
          {...register('email')}
          type="email"
          className="mt-1 block w-full rounded-md border px-3 py-2"
          placeholder="your@email.com"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          密码
        </label>
        <input
          {...register('password')}
          type="password"
          className="mt-1 block w-full rounded-md border px-3 py-2"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        {isLoading ? '登录中...' : '登录'}
      </button>
    </form>
  );
}
```

#### 1.2 RegisterForm
**位置**: `src/components/auth/RegisterForm.tsx`

**功能**: 用户注册表单

---

### 2. 教室模块

#### 2.1 ClassroomCard
**位置**: `src/components/classroom/ClassroomCard.tsx`

**功能**: 显示单个教室信息卡片

**Props**:
```typescript
interface ClassroomCardProps {
  classroom: Classroom;
  onJoin?: (id: string) => void;
  onCancel?: (id: string) => void;
  variant?: 'grid' | 'list';
}
```

**组件代码示例**:
```tsx
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Calendar, Clock, User, Book } from 'react-icons/fi';
import { Classroom } from '@/types/classroom';

export function ClassroomCard({
  classroom,
  onJoin,
  onCancel,
  variant = 'grid'
}: ClassroomCardProps) {
  const statusColors = {
    scheduled: 'bg-blue-100 text-blue-800',
    active: 'bg-green-100 text-green-800',
    completed: 'bg-gray-100 text-gray-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm hover:shadow-md transition">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <img
            src={classroom.ai_teacher.avatar_url}
            alt={classroom.ai_teacher.display_name}
            className="w-12 h-12 rounded-full"
          />
          <div>
            <h3 className="font-semibold text-lg">{classroom.name}</h3>
            <p className="text-sm text-gray-600">
              {classroom.ai_teacher.display_name}
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[classroom.status]}`}>
          {classroom.status}
        </span>
      </div>

      {/* Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Book className="w-4 h-4" />
          <span>{classroom.subject} - {classroom.lesson_topic}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="w-4 h-4" />
          <span>
            {format(new Date(classroom.scheduled_start_at), 'PPP', { locale: zhCN })}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span>{classroom.duration_minutes} 分钟</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        {classroom.status === 'scheduled' && (
          <>
            <button
              onClick={() => onJoin?.(classroom.id)}
              className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              进入教室
            </button>
            <button
              onClick={() => onCancel?.(classroom.id)}
              className="px-4 py-2 rounded-md border border-gray-300 hover:bg-gray-50"
            >
              取消
            </button>
          </>
        )}
        {classroom.status === 'active' && (
          <button
            onClick={() => onJoin?.(classroom.id)}
            className="flex-1 rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700 animate-pulse"
          >
            继续上课
          </button>
        )}
        {classroom.status === 'completed' && (
          <button className="flex-1 rounded-md border px-4 py-2 hover:bg-gray-50">
            查看回放
          </button>
        )}
      </div>
    </div>
  );
}
```

#### 2.2 ClassroomList
**位置**: `src/components/classroom/ClassroomList.tsx`

**功能**: 教室列表容器

**组件代码示例**:
```tsx
import { useQuery } from '@tanstack/react-query';
import { classroomsApi } from '@/api/classrooms';
import { ClassroomCard } from './ClassroomCard';
import { Loader } from '@/components/ui/Loader';

export function ClassroomList({ status }: { status?: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['classrooms', status],
    queryFn: () => classroomsApi.getClassrooms({ status }),
  });

  if (isLoading) {
    return <Loader />;
  }

  if (!data?.items.length) {
    return (
      <div className="text-center py-12 text-gray-500">
        暂无教室
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.items.map((classroom) => (
        <ClassroomCard key={classroom.id} classroom={classroom} />
      ))}
    </div>
  );
}
```

#### 2.3 ClassroomView (核心组件)
**位置**: `src/components/classroom/ClassroomView.tsx`

**功能**: 教室主视图，包含音视频通话、消息、白板等

**组件结构**:
```tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useClassroom } from '@/hooks/useClassroom';
import { useWebSocket } from '@/hooks/useWebSocket';
import { VideoPanel } from './VideoPanel';
import { MessagePanel } from './MessagePanel';
import { WhiteboardPanel } from './WhiteboardPanel';
import { ControlBar } from './ControlBar';
import { AITeacherAvatar } from './AITeacherAvatar';

export function ClassroomView() {
  const { classroomId } = useParams();
  const { classroom, startSession, endSession } = useClassroom(classroomId!);
  const { messages, sendMessage, isConnected } = useWebSocket(classroomId!);

  const [activePanel, setActivePanel] = useState<'messages' | 'whiteboard' | 'resources'>('messages');
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(false);

  useEffect(() => {
    startSession();
    return () => {
      endSession();
    };
  }, [classroomId]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img
              src={classroom?.ai_teacher.avatar_url}
              alt={classroom?.ai_teacher.display_name}
              className="w-10 h-10 rounded-full"
            />
            <div>
              <h1 className="font-semibold text-lg">{classroom?.name}</h1>
              <p className="text-sm text-gray-600">{classroom?.lesson_topic}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`flex items-center gap-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              <span className="w-2 h-2 rounded-full bg-current"></span>
              {isConnected ? '已连接' : '连接中...'}
            </span>
            <button
              onClick={endSession}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              结束课程
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Video/Avatar */}
        <div className="flex-1 flex items-center justify-center bg-gray-900 relative">
          <AITeacherAvatar
            teacher={classroom?.ai_teacher}
            isSpeaking={false}
          />

          {/* Control Bar */}
          <ControlBar
            isMuted={isMuted}
            isVideoEnabled={isVideoEnabled}
            onToggleMute={() => setIsMuted(!isMuted)}
            onToggleVideo={() => setIsVideoEnabled(!isVideoEnabled)}
          />
        </div>

        {/* Right Panel - Messages/Whiteboard/Resources */}
        <div className="w-96 bg-white border-l flex flex-col">
          {/* Panel Tabs */}
          <div className="flex border-b">
            <button
              onClick={() => setActivePanel('messages')}
              className={`flex-1 px-4 py-3 text-sm font-medium ${
                activePanel === 'messages'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              对话
            </button>
            <button
              onClick={() => setActivePanel('whiteboard')}
              className={`flex-1 px-4 py-3 text-sm font-medium ${
                activePanel === 'whiteboard'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              白板
            </button>
            <button
              onClick={() => setActivePanel('resources')}
              className={`flex-1 px-4 py-3 text-sm font-medium ${
                activePanel === 'resources'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              资源
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-hidden">
            {activePanel === 'messages' && (
              <MessagePanel
                messages={messages}
                onSendMessage={sendMessage}
              />
            )}
            {activePanel === 'whiteboard' && (
              <WhiteboardPanel classroomId={classroomId!} />
            )}
            {activePanel === 'resources' && (
              <div className="p-4">资源面板</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### 2.4 MessagePanel
**位置**: `src/components/classroom/MessagePanel.tsx`

**功能**: 消息面板，显示对话历史和输入框

**组件代码示例**:
```tsx
import { useRef, useEffect, useState } from 'react';
import { Send, Mic, MicOff } from 'react-icons/fi';
import { Message } from '@/types/message';
import { MessageBubble } from './MessageBubble';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';

interface MessagePanelProps {
  messages: Message[];
  onSendMessage: (content: string, type: 'text' | 'audio') => void;
}

export function MessagePanel({ messages, onSendMessage }: MessagePanelProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
    onRecordingComplete: (audioBlob) => {
      onSendMessage(audioBlob, 'audio');
    },
  });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendText = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue, 'text');
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息..."
            className="flex-1 resize-none rounded-md border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
          <div className="flex flex-col gap-2">
            <button
              onClick={handleSendText}
              disabled={!inputValue.trim()}
              className="p-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-2 rounded-md ${
                isRecording
                  ? 'bg-red-600 text-white animate-pulse'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### 2.5 MessageBubble
**位置**: `src/components/classroom/MessageBubble.tsx`

**功能**: 单条消息气泡

**组件代码示例**:
```tsx
import { format } from 'date-fns';
import { User, Bot, Play, Pause } from 'react-icons/fi';
import { Message } from '@/types/message';
import { useState } from 'react';

export function MessageBubble({ message }: { message: Message }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const isStudent = message.role === 'student';

  const playAudio = () => {
    if (message.audio_url) {
      const audio = new Audio(message.audio_url);
      audio.play();
      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
    }
  };

  return (
    <div className={`flex gap-3 ${isStudent ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isStudent ? 'bg-blue-600' : 'bg-green-600'
      }`}>
        {isStudent ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${isStudent ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`rounded-lg px-4 py-2 ${
          isStudent ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-900'
        }`}>
          {message.content && (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          )}

          {message.audio_url && (
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={playAudio}
                className="p-1 rounded-full hover:bg-white/20"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <div className="flex-1 h-1 bg-white/30 rounded-full">
                <div className="h-full bg-white rounded-full" style={{ width: '0%' }}></div>
              </div>
              <span className="text-xs opacity-75">
                {message.audio_duration_seconds}s
              </span>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-gray-500 mt-1">
          {format(new Date(message.timestamp), 'HH:mm')}
        </span>

        {/* Processing Time (for AI messages) */}
        {!isStudent && message.processing_time_ms && (
          <span className="text-xs text-gray-400">
            响应时间: {message.processing_time_ms}ms
          </span>
        )}
      </div>
    </div>
  );
}
```

#### 2.6 AITeacherAvatar
**位置**: `src/components/classroom/AITeacherAvatar.tsx`

**功能**: AI教师头像动画

**组件代码示例**:
```tsx
import { motion } from 'framer-motion';
import { AITeacher } from '@/types/classroom';

interface AITeacherAvatarProps {
  teacher?: AITeacher;
  isSpeaking: boolean;
}

export function AITeacherAvatar({ teacher, isSpeaking }: AITeacherAvatarProps) {
  return (
    <div className="relative">
      {/* Avatar */}
      <motion.div
        animate={{
          scale: isSpeaking ? [1, 1.05, 1] : 1,
        }}
        transition={{
          duration: 0.5,
          repeat: isSpeaking ? Infinity : 0,
        }}
        className="relative"
      >
        <img
          src={teacher?.avatar_url}
          alt={teacher?.display_name}
          className="w-64 h-64 rounded-full border-4 border-white shadow-2xl"
        />

        {/* Speaking Indicator */}
        {isSpeaking && (
          <motion.div
            animate={{
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
            }}
            className="absolute inset-0 rounded-full border-4 border-green-500"
          />
        )}
      </motion.div>

      {/* Teacher Info */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full mt-4 text-center">
        <h3 className="text-white text-xl font-semibold">{teacher?.display_name}</h3>
        <p className="text-gray-300 text-sm">{teacher?.teaching_style} 教学风格</p>
      </div>

      {/* Voice Wave Animation */}
      {isSpeaking && (
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full mt-16 flex gap-1">
          {[...Array(5)].map((_, i) => (
            <motion.div
              key={i}
              animate={{
                height: [10, 30, 10],
              }}
              transition={{
                duration: 0.5,
                repeat: Infinity,
                delay: i * 0.1,
              }}
              className="w-1 bg-green-500 rounded-full"
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 2.7 ControlBar
**位置**: `src/components/classroom/ControlBar.tsx`

**功能**: 教室控制栏（麦克风、摄像头、结束等）

**组件代码示例**:
```tsx
import { Mic, MicOff, Video, VideoOff, PhoneOff } from 'react-icons/fi';

interface ControlBarProps {
  isMuted: boolean;
  isVideoEnabled: boolean;
  onToggleMute: () => void;
  onToggleVideo: () => void;
  onEndSession?: () => void;
}

export function ControlBar({
  isMuted,
  isVideoEnabled,
  onToggleMute,
  onToggleVideo,
  onEndSession,
}: ControlBarProps) {
  return (
    <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex gap-4">
      {/* Microphone */}
      <button
        onClick={onToggleMute}
        className={`p-4 rounded-full ${
          isMuted ? 'bg-red-600' : 'bg-gray-700'
        } hover:bg-opacity-80 transition`}
      >
        {isMuted ? (
          <MicOff className="w-6 h-6 text-white" />
        ) : (
          <Mic className="w-6 h-6 text-white" />
        )}
      </button>

      {/* Video */}
      <button
        onClick={onToggleVideo}
        className={`p-4 rounded-full ${
          !isVideoEnabled ? 'bg-red-600' : 'bg-gray-700'
        } hover:bg-opacity-80 transition`}
      >
        {isVideoEnabled ? (
          <Video className="w-6 h-6 text-white" />
        ) : (
          <VideoOff className="w-6 h-6 text-white" />
        )}
      </button>

      {/* End Session */}
      {onEndSession && (
        <button
          onClick={onEndSession}
          className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition"
        >
          <PhoneOff className="w-6 h-6 text-white" />
        </button>
      )}
    </div>
  );
}
```

---

### 3. 仪表盘模块

#### 3.1 Dashboard
**位置**: `src/pages/Dashboard.tsx`

**功能**: 学生主仪表盘

**组件代码示例**:
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ClassroomList } from '@/components/classroom/ClassroomList';
import { LearningProgress } from '@/components/learning/LearningProgress';
import { UpcomingSessions } from '@/components/dashboard/UpcomingSessions';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { QuickStats } from '@/components/dashboard/QuickStats';

export function Dashboard() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">我的学习</h1>

      {/* Quick Stats */}
      <QuickStats />

      {/* Upcoming Sessions */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">即将开始的课程</h2>
        <UpcomingSessions />
      </section>

      {/* Tabs */}
      <Tabs defaultValue="active" className="mb-8">
        <TabsList>
          <TabsTrigger value="active">进行中</TabsTrigger>
          <TabsTrigger value="scheduled">已预约</TabsTrigger>
          <TabsTrigger value="completed">已完成</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-6">
          <ClassroomList status="active" />
        </TabsContent>

        <TabsContent value="scheduled" className="mt-6">
          <ClassroomList status="scheduled" />
        </TabsContent>

        <TabsContent value="completed" className="mt-6">
          <ClassroomList status="completed" />
        </TabsContent>
      </Tabs>

      {/* Learning Progress */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">学习进度</h2>
        <LearningProgress />
      </section>

      {/* Recent Activity */}
      <section>
        <h2 className="text-xl font-semibold mb-4">最近活动</h2>
        <RecentActivity />
      </section>
    </div>
  );
}
```

#### 3.2 QuickStats
**位置**: `src/components/dashboard/QuickStats.tsx`

**功能**: 快速统计卡片

**组件代码示例**:
```tsx
import { useQuery } from '@tanstack/react-query';
import { learningApi } from '@/api/learning';
import { BookOpen, Clock, TrendingUp, Award } from 'react-icons/fi';

export function QuickStats() {
  const { data } = useQuery({
    queryKey: ['learning-statistics'],
    queryFn: () => learningApi.getStatistics({ period: 'month' }),
  });

  const stats = [
    {
      label: '本月课程',
      value: data?.total_sessions || 0,
      icon: BookOpen,
      color: 'bg-blue-500',
    },
    {
      label: '学习时长',
      value: `${Math.floor((data?.total_duration_minutes || 0) / 60)}小时`,
      icon: Clock,
      color: 'bg-green-500',
    },
    {
      label: '平均分数',
      value: data?.average_score || 0,
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
    {
      label: '获得徽章',
      value: 8,
      icon: Award,
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {stats.map((stat) => (
        <div key={stat.label} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
              <p className="text-2xl font-bold">{stat.value}</p>
            </div>
            <div className={`${stat.color} p-3 rounded-full`}>
              <stat.icon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

### 4. 学习分析模块

#### 4.1 LearningProgress
**位置**: `src/components/learning/LearningProgress.tsx`

**功能**: 学习进度可视化

**组件代码示例**:
```tsx
import { useQuery } from '@tanstack/react-query';
import { learningApi } from '@/api/learning';
import { ProgressBar } from '@/components/ui/ProgressBar';

export function LearningProgress() {
  const { data } = useQuery({
    queryKey: ['learning-progress'],
    queryFn: () => learningApi.getProgress(),
  });

  if (!data?.progress.length) {
    return <div className="text-center py-8 text-gray-500">暂无学习数据</div>;
  }

  return (
    <div className="space-y-6">
      {data.progress.map((subject) => (
        <div key={subject.subject} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold capitalize">{subject.subject}</h3>
            <span className="text-sm text-gray-600">
              {subject.total_sessions} 节课 · {subject.total_duration_minutes} 分钟
            </span>
          </div>

          <ProgressBar
            value={subject.progress_percentage}
            className="mb-4"
          />

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-xs text-gray-600 mb-1">当前水平</p>
              <p className="font-medium capitalize">{subject.current_level}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">平均分数</p>
              <p className="font-medium">{subject.average_session_score}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">已掌握主题</p>
              <p className="font-medium">{subject.topics_mastered.length}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-600 mb-2">已掌握</p>
              <div className="flex flex-wrap gap-1">
                {subject.topics_mastered.map((topic) => (
                  <span key={topic} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-2">学习中</p>
              <div className="flex flex-wrap gap-1">
                {subject.topics_in_progress.map((topic) => (
                  <span key={topic} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

### 5. AI教师选择模块

#### 5.1 TeacherSelector
**位置**: `src/components/classroom/TeacherSelector.tsx`

**功能**: AI教师选择器

**组件代码示例**:
```tsx
import { useQuery } from '@tanstack/react-query';
import { teachersApi } from '@/api/teachers';
import { TeacherCard } from './TeacherCard';

interface TeacherSelectorProps {
  subject?: string;
  onSelect: (teacherId: string) => void;
  selectedId?: string;
}

export function TeacherSelector({ subject, onSelect, selectedId }: TeacherSelectorProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['ai-teachers', subject],
    queryFn: () => teachersApi.getTeachers({ subject }),
  });

  if (isLoading) {
    return <div>加载中...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data?.items.map((teacher) => (
        <TeacherCard
          key={teacher.id}
          teacher={teacher}
          isSelected={teacher.id === selectedId}
          onSelect={() => onSelect(teacher.id)}
        />
      ))}
    </div>
  );
}
```

---

## 自定义Hooks

### useWebSocket
**位置**: `src/hooks/useWebSocket.ts`

**功能**: WebSocket连接管理

**代码示例**:
```typescript
import { useEffect, useRef, useState } from 'use';
import { useAuthStore } from '@/stores/authStore';
import { Message, WebSocketMessage } from '@/types/message';

export function useWebSocket(classroomId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const { token } = useAuthStore();

  useEffect(() => {
    const ws = new WebSocket(
      `wss://api.aiteaching.example.com/ws/classrooms/${classroomId}?token=${token}`
    );

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);

      if (data.event === 'ai_text_response' || data.event === 'message_received') {
        setMessages((prev) => [...prev, data.data as Message]);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [classroomId, token]);

  const sendMessage = (content: string, type: 'text' | 'audio' = 'text') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          event: type === 'text' ? 'send_text' : 'send_audio',
          data: { content },
          message_id: `client_${Date.now()}`,
        })
      );
    }
  };

  return {
    messages,
    isConnected,
    sendMessage,
  };
}
```

### useAudioRecorder
**位置**: `src/hooks/useAudioRecorder.ts`

**功能**: 音频录制

**代码示例**:
```typescript
import { useState, useRef } from 'react';

interface UseAudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
}

export function useAudioRecorder({ onRecordingComplete }: UseAudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        onRecordingComplete(audioBlob);
        chunksRef.current = [];
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  return {
    isRecording,
    startRecording,
    stopRecording,
  };
}
```

---

## 状态管理 (Zustand)

### authStore
**位置**: `src/stores/authStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types/user';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
      updateUser: (userData) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        })),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

---

## 性能优化

1. **代码分割**: 使用React.lazy和Suspense进行路由级代码分割
2. **虚拟滚动**: 长消息列表使用react-window
3. **图片懒加载**: 使用react-lazy-load-image-component
4. **Memo化**: 使用React.memo避免不必要的重渲染
5. **WebSocket优化**: 消息缓冲和批量处理
6. **音频优化**: 使用Web Audio API进行音频处理和缓存

---

## 响应式设计

- **移动端优先**: 使用Tailwind的响应式断点
- **自适应布局**: 支持桌面、平板、手机
- **触摸优化**: 支持手势操作和触摸事件
- **PWA支持**: 支持离线使用和安装到主屏幕

---

## 可访问性 (A11y)

- ARIA标签和角色
- 键盘导航支持
- 屏幕阅读器优化
- 高对比度模式
- 焦点管理
