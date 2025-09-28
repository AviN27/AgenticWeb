# 🎯 AgenticWeb - Intelligent Web Automation Platform

A modular, event-driven microservices system built with Kafka, Redis, FastAPI, and Python asyncio. This platform powers multi-domain agentic automation through LLM-driven reasoning and intelligent orchestration. Currently implemented as a user-centric automation solution for Grab's services (ride booking, food & grocery orders).

---

## 🚀 Core Components

1. **App Interface** (`services/app_interface`)

   * **WebSocket Endpoints** for voice (`/ws/mic`) and text (`/ws/text`) ingestion
   * Pushes user transcripts to Kafka (`transcript` topic)

2. **Reasoning Service** (`services/reasoning`)

   * **Consumes** `transcript` topic
   * **LLM Orchestration**: Gemini Pro via LangChain
   * **Slot Filling & Clarification**: Redis-based state tracker
   * **Context Enrichment**: Static (RedisJSON) + Semantic (Vector DB)
   * **Publishes** tool calls to `agent.cmd`

3. **Action Router** (`services/router`)

   * **Consumes** `agent.cmd`
   * **HTTP → Kafka Bridge**: Forwards commands to Adapter Gateway, returns results to Kafka (`agent.out.*`)

4. **Adapter Gateway** (`services/adapters`)

   * **FastAPI** unified API on port 8100
   * Domain routers: `/ride`, `/food`, `/mart`, `/payment`, `/location`
   * Returns mocked responses for each domain

5. **Domain Agents** (`services/agents`)

   * **Listen** on `agent.cmd` for their tool (e.g. `order_food`)
   * **Mock** external call, publish to `agent.out.<domain>`

6. **State Tracker** (`services/state_tracker`)

   * **Listens** on all `agent.*` topics
   * **Updates** Redis with per-`trace_id` status and final payload

7. **Error Agent** (`services/error_agent`)

   * **Consumes** `agent.error` (DLQ)
   * **Logs** or notifies errors for debugging

---

## 🔄 Data Flow

```plaintext
[Frontend] → WebSocket/API → [App Interface]
        └─> Kafka: transcript → [Reasoning] → [clarify.agent & clarify.input] → Redis
                         └─> agent.cmd → [Action Router]
                                      └─> HTTP → [Adapters]
                                               └─> agent.out.* → [State Tracker] [mart, ride, food]
        [State Tracker] updates Redis → UI polls/subscribes for status
        [Error Agent] logs failures from agent.error
```

---

## 📦 Topics & Endpoints
```
| Component     | Input Topic / API          | Output Topic / API                        |      |        |
| ------------- | -------------------------- | ----------------------------------------- | ---- | ------ |
| App Interface | WS `/ws/mic`, `/ws/text`   | Kafka `transcript`                        |      |        |
| Reasoning     | Kafka `transcript`         | Kafka `agent.cmd`, `agent.error`          |      |        |
| Action Router | Kafka `agent.cmd`          | Kafka `agent.out.*`                       |      |        |
| Adapters      | HTTP `/ride`, `/food`, ... | Kafka `agent.out.*`                       |      |        |
| Domain Agents | Kafka `agent.cmd`          | Kafka `agent.out.ride`, `agent.out.food`, `agent.out.mart` |
| State Tracker | Kafka `agent.*`            | Redis `state:{trace_id}` & `agent.status` |      |        |
| Error Agent   | Kafka `agent.error`        | Logs / Notifications                      |      |        |
```

---

## 🏗️ Architecture Overview

### Backend Services
- **Microservices Architecture** - Event-driven design with Kafka messaging
- **AI-Powered Reasoning** - LLM orchestration for intelligent decision making
- **Domain-Specific Agents** - Specialized agents for different service domains
- **Real-time Communication** - WebSocket interfaces for live interactions
- **State Management** - Redis-based state tracking and context enrichment

### Frontend Interface
- **Modern React Application** - Material-UI based chat interface
- **Real-time Updates** - WebSocket connection for live agent interactions
- **Responsive Design** - Mobile-friendly interface with dark theme
- **Agent Visualization** - Visual indicators for different agent types

---

## 🔧 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- Redis
- Kafka (Redpanda recommended)

### Backend Setup

1. **Start Redpanda** (Kafka) and Redis Stack

2. **Adapters Gateway**:
   ```bash
   uvicorn services.adapters.main:app --port 8100
   ```

3. **Static Context API**:
   ```bash
   uvicorn services.context.static:app --port 8001
   ```

4. **Semantic Context API**:
   ```bash
   uvicorn services.context.semantic:app --port 8002
   ```

5. **Reasoning Service**:
   ```bash
   uvicorn services.reasoning.main:app --port 8201
   ```

6. **Action Router**:
   ```bash
   uvicorn services.router.main:app --port 8300
   ```

7. **Domain Agents & State Tracker & Error Agent**:
   ```bash
   # Each in its own terminal
   python services/agents/ride_agent.py
   python services/agents/food_agent.py
   python services/agents/mart_agent.py
   python services/state_tracker/main.py
   python services/error_agent/main.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd Frontend/grabsense
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.12
- **Message Queue**: Kafka (Redpanda)
- **Cache**: Redis
- **AI/LLM**: Google Generative AI, LangChain
- **Vector DB**: Pinecone
- **Voice Processing**: Whisper

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite
- **UI Library**: Material-UI
- **Styling**: Emotion
- **Real-time**: WebSocket API

---

## 📈 Next Steps

* Integrate real external APIs in Adapters
* Harden slot-filling & clarify flows
* Add observability (metrics & tracing)
* Extend multi-modal UI clients (web, mobile, watch)
* Customize for additional domains and use cases

---

## 📝 Project Structure

```
AgenticWeb/
├── Backend/                 # Python microservices
│   ├── services/            # Core services and agents
│   ├── adapters/            # External API integrations
│   ├── tools/               # Utility tools
│   └── infra/               # Infrastructure configs
├── Frontend/                # React web interface
│   └── grabsense/           # Chat interface application
└── README.md                # This file
```

---

⭐ **AgenticWeb** — enabling seamless agentic automation experiences via AI-powered orchestration. Currently implemented for Grab's user-centric automation needs. Feedback and contributions welcome!