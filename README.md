# 🚀 Realtime Chat Application (Production-Style)

A full-stack realtime chat application built with FastAPI, PostgreSQL, Redis, and React — designed with production-level architecture including WebSockets, Pub/Sub, offline sync, and delivery tracking.

---

## ✨ Features

### 🔐 Authentication
- JWT-based authentication
- Register / Login
- Secure protected routes

### 💬 Chat System
- 1:1 direct messaging
- Group chat support
- Conversation management

### ⚡ Realtime Messaging
- WebSocket-based communication
- Redis Pub/Sub for multi-instance scalability
- Instant message delivery

### 📦 Message Handling
- Persistent message storage (PostgreSQL)
- Offline message delivery
- Reconnect sync for missed messages

### 📊 Message Status
- Sent ✓
- Delivered ✓✓
- Read ✓✓ (read)
- Per-user delivery tracking

### 🟢 Presence System
- Online / Offline detection
- Redis TTL-based presence
- Heartbeat mechanism

### ✍️ Typing Indicators
- Realtime typing events
- Debounced to prevent spam

### 🔒 Rate Limiting
- Redis-based rate limiting
- Spam protection

### 🧠 Advanced Features
- Unread message count
- Conversation ordering by activity
- Idempotent message sending

---

## 🏗️ Architecture

    Client (React)
        ↓
    WebSocket / REST API
        ↓
    FastAPI Backend
        ↓
    PostgreSQL (persistent data)
    Redis (cache, pub/sub, presence)

---

## 🔁 Message Flow

    User sends message →
    Save to DB →
    Send back to sender (instant) →
    Publish to Redis →
    Other instances receive →
    Deliver to recipients

---

## 🧰 Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy (Async ORM)
- PostgreSQL
- Redis
- WebSockets

### Frontend
- React (Vite + TypeScript)
- Tailwind CSS
- Axios

### DevOps
- Docker & Docker Compose

---

## 🗄️ Database Design

### Core Tables
- users
- conversations
- conversation_members
- messages
- message_deliveries

### Key Concepts
- Per-user delivery tracking
- Cursor-based pagination
- Idempotent message handling

---

## ⚡ Redis Usage

- Pub/Sub for WebSocket scaling
- Presence tracking (TTL)
- Rate limiting counters

---

## 🔌 WebSocket Events

### Client → Server
- message.send
- typing.start
- typing.stop
- message.read
- heartbeat

### Server → Client
- message.new
- messages.sync
- typing.start
- typing.stop
- presence.update
- heartbeat.ack

---

## 🖥️ Local Setup

### 1. Clone repo

    git clone https://github.com/YOUR_USERNAME/realtime-chat-fastapi-react.git
    cd realtime-chat-fastapi-react

### 2. Backend setup

    docker compose up --build

Backend runs on:
http://localhost:8000

### 3. Frontend setup

    cd frontend
    npm install
    npm run dev

Frontend runs on:
http://localhost:5173

### 4. Environment Variables

Create `.env`:

    DATABASE_URL=postgresql+asyncpg://chat_user:chat_pass@postgres:5432/chat_db
    REDIS_URL=redis://redis:6379/0
    SECRET_KEY=your-secret

---

## 📸 Screenshots

Add:
- Login page
- Chat UI
- Typing indicator
- Read receipts
- Group members view

---

## 🚀 Deployment

- Backend → Render / Railway / AWS
- Frontend → Vercel / Netlify

---

## 🧠 What I Learned

- Designing realtime systems with WebSockets
- Handling distributed state using Redis Pub/Sub
- Building idempotent APIs
- Managing offline message delivery
- Structuring scalable backend architecture

---

## 💼 Resume Highlights

- Built a production-style realtime chat system using FastAPI, PostgreSQL, and Redis
- Implemented WebSocket-based messaging with Redis Pub/Sub for horizontal scalability
- Designed per-user message delivery tracking with read receipts and offline sync
- Added rate limiting and presence tracking using Redis

---

## 🏴‍☠️ Author

Sai Teja