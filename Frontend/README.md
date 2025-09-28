# AgenticWeb Frontend

A modern React-based web interface for agentic web automation systems, providing real-time communication and interaction capabilities with AI-powered agents. Currently implemented as a chat interface for Grab's agentic automation services.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd Frontend/grabsense
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5173` (or the port shown in terminal)

## 🏗️ Architecture

The frontend is built as a single-page application with the following key components:

### Core Components
- **ChatWindow** - Real-time message display with agent-specific icons
- **ChatInput** - User input interface for sending messages
- **App** - Main application container with Material-UI theming

### Key Features
- **Real-time Communication** - WebSocket connection for live agent interactions
- **Agent Type Recognition** - Visual indicators for different agent types (ride, food, mart, etc.)
- **Responsive Design** - Mobile-friendly interface with dark theme
- **Message History** - Persistent conversation display with auto-scroll

## 🛠️ Tech Stack

- **Framework:** React 19
- **Build Tool:** Vite
- **UI Library:** Material-UI (MUI)
- **Styling:** Emotion (CSS-in-JS)
- **Real-time:** WebSocket API
- **Icons:** Material Icons

## 📁 Project Structure

```
Frontend/grabsense/
├── src/
│   ├── components/
│   │   ├── ChatWindow.jsx    # Message display component
│   │   └── ChatInput.jsx     # Input interface
│   ├── hooks/
│   │   └── useWebSocket.js   # WebSocket connection hook
│   ├── App.jsx               # Main application component
│   ├── App.css               # Global styles
│   ├── index.css             # Base styles
│   └── main.jsx              # Application entry point
├── public/                   # Static assets
├── package.json              # Dependencies and scripts
└── vite.config.js           # Vite configuration
```

## 🔧 Configuration

The application connects to the backend via WebSocket. Key configuration:

- **WebSocket URL:** `ws://localhost:8003/ws/chat`
- **Theme:** Dark mode with custom color palette
- **Responsive:** Mobile-first design approach

## 🎨 UI Features

### Message Types
The interface recognizes and displays different types of agent messages:
- **User Messages** - User input with person icon
- **Ride Agent** - Car icon for transportation services
- **Food Agent** - Restaurant icon for food delivery
- **Mart Agent** - Shopping cart icon for grocery/shopping
- **Clarification** - Help icon for clarification requests
- **System** - Default agent icon for general messages

### Visual Design
- **Dark Theme** - Modern dark interface with green accent colors
- **Material Design** - Clean, consistent UI components
- **Responsive Layout** - Adapts to different screen sizes
- **Auto-scroll** - Automatically scrolls to latest messages

## 🚦 WebSocket Integration

The frontend connects to the backend via WebSocket to receive real-time updates:

```javascript
// WebSocket connection
const WS_URL = "ws://localhost:8003/ws/chat";

// Message handling
const { messages, connectionStatus } = useWebSocket(WS_URL);
```

## 🔄 Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Adding New Agent Types
To add support for new agent types:

1. Add icon import in `ChatWindow.jsx`
2. Update `getMessageType()` function
3. Add case in `getIcon()` function
4. Update styling for new message type

## 🤝 Contributing

1. Follow React best practices and hooks patterns
2. Maintain consistent Material-UI theming
3. Ensure responsive design for mobile devices
4. Test WebSocket connectivity thoroughly

## 📝 Notes

- This is a flexible frontend interface for agentic web automation
- Currently implemented as a GrabHackPS2 hackathon project
- The interface is designed to be easily extensible for different agent types
- Real-time communication enables seamless user-agent interactions