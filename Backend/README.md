# AgenticWeb Backend

A flexible microservices-based backend system for agentic web automation, featuring AI-powered agents that can handle complex multi-step workflows across different domains. Currently implemented as a solution for Grab's ride booking, food ordering, mart shopping, and payment processing services.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to backend directory:**
   ```bash
   cd Backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   uvicorn services.gateway.main:app --reload
   ```

## 🏗️ Architecture

The backend consists of multiple microservices organized as follows:

### Core Services
- **Gateway** - Main entry point and request routing
- **Router** - Intelligent request routing to appropriate agents
- **Reasoning** - AI-powered decision making and context processing

### Domain-Specific Agents
*Current Grab Implementation:*
- **Ride Agent** - Handles ride booking and management
- **Food Agent** - Manages food ordering and delivery
- **Mart Agent** - Handles grocery/shopping orders
- **Payment Agent** - Processes payments and transactions
- **Error Agent** - Handles error scenarios and fallbacks

*The agent architecture is designed to be easily extensible for any domain or use case.*

### Interface Services
- **App Interface** - WebSocket connections for real-time communication
  - `chat_ws.py` - Chat interface
  - `mic_ws.py` - Microphone/voice interface
  - `text_ws.py` - Text input interface

### Supporting Services
- **Voice to Prompt** - Converts voice input to text prompts
- **Context** - Manages user context and session state
- **State Tracker** - Tracks conversation and user state
- **Suggestions** - Provides intelligent suggestions
- **Clarify Agent** - Handles clarification requests

### Adapters
External API integrations (Grab-specific):
- `ride_api.py` - Ride service APIs
- `food_api.py` - Food service APIs
- `mart_api.py` - Mart/shopping APIs
- `payment_api.py` - Payment processing APIs
- `location_api.py` - Location services

*Adapters can be customized for any external service or API integration.*

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.12
- **Voice Processing:** Whisper (faster-whisper)
- **AI/LLM:** Google Generative AI, LangChain
- **Vector Database:** Pinecone
- **Caching:** Redis
- **Message Queue:** Kafka (aiokafka)
- **WebSocket:** FastAPI WebSocket support

## 📁 Project Structure

```
Backend/
├── services/
│   ├── adapters/          # External API integrations
│   ├── app_interface/     # WebSocket interfaces
│   ├── clarify_agent/     # Clarification handling
│   ├── context/           # Context management
│   ├── error_agent/       # Error handling
│   ├── food_agent/        # Food ordering service
│   ├── gateway/           # Main gateway service
│   ├── mart_agent/        # Shopping service
│   ├── reasoning/         # AI reasoning engine
│   ├── ride_agent/        # Ride booking service
│   ├── router/            # Request routing
│   ├── state_tracker/     # State management
│   ├── suggestions/       # Suggestion engine
│   └── voice_to_prompt/   # Voice processing
├── tools/                 # Utility tools
├── infra/                 # Infrastructure configs
└── scripts/               # Helper scripts
```

## 🔧 Configuration

The system uses environment variables for configuration. Key settings include:
- API keys for external services
- Database connection strings
- Redis configuration
- WebSocket settings

## 🚦 API Endpoints

The main gateway service exposes:
- WebSocket endpoints for real-time communication
- REST API endpoints for service interactions
- Health check endpoints

## 🤝 Contributing

1. Follow the existing code structure and patterns
2. Add appropriate error handling
3. Include type hints for better code clarity
4. Test your changes thoroughly

## 📝 Notes

- This is a flexible agentic web automation framework
- Currently implemented as a GrabHackPS2 hackathon project
- The system is designed for rapid prototyping and demonstration
- Some services may use mock data for demonstration purposes
- The architecture supports easy customization for different domains and use cases