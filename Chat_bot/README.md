# AI Chat Bot with Cortex SDK

A modern AI assistant powered by Llama-2-7B and integrated with Cortex SDK for intelligent memory management.

## Features

- 🤖 **AI-Powered**: Uses Llama-2-7B model for intelligent responses
- 🧠 **Cortex Integration**: Advanced memory management via Cortex SDK
- 💬 **Real-time Chat**: Interactive chat interface with typing indicators
- 📱 **Modern UI**: Clean, responsive chat interface
- 💾 **Intelligent Memory**: Context-aware conversation with semantic search
- 📊 **Memory Stats**: Track conversation history and memory usage
- 🚀 **Easy Setup**: Automated Cortex SDK and model installation

## Cortex SDK Integration

This chatbot serves as a test application for the Cortex SDK, demonstrating:

- **In-Memory Storage**: Fast conversation history using Cortex's local backend
- **Semantic Search**: Retrieve relevant conversation context using embeddings
- **Session Management**: Per-session memory with automatic cleanup
- **Memory Statistics**: Real-time insights into memory usage
- **Conversation Summarization**: Generate summaries using Cortex's summarizer

## Quick Start

### Complete Setup (Recommended)
```bash
python setup.py  # Installs dependencies + Cortex SDK + downloads model
python start_chatbot.py
```

The setup script will:
1. Install Python dependencies
2. Install Cortex SDK in development mode (from parent directory)
3. Download the Llama-2-7B model (2.5GB)

### Access the UI
- Open your browser to `http://localhost:5001`
- Start chatting with your AI assistant!

## API Endpoints

The chatbot provides several Cortex-powered endpoints:

- `POST /chat` - Send a message and get a response
- `GET /chat/history/<session_id>` - Get conversation history
- `GET /chat/summarize/<session_id>` - Get conversation summary (Cortex)
- `DELETE /chat/clear/<session_id>` - Clear session memory
- `GET /memory/stats` - Get Cortex memory statistics
- `GET /health` - Health check

### Example: Chat Request
```bash
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "user123"}'
```

### Example: Get Memory Stats
```bash
curl http://localhost:5001/memory/stats
```

## File Structure

```
Chat_bot/
├── app/
│   ├── simple_app.py          # Flask application with Cortex
│   └── templates/
│       └── index.html         # Chat UI
├── rag_model/
│   ├── foundation_model/
│   │   └── llama-2-7b-chat-hf-q2_k.gguf  # Llama model (2.5GB)
│   └── src_gpt/
│       └── cortex_chat.py     # Cortex-powered chatbot
├── setup.py                   # Complete setup script
├── start_chatbot.py           # Start server script
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## How It Works

### Architecture

```
User → Flask API → CortexChatBot → Llama-2-7B Model
                        ↓
                   Cortex SDK
                        ↓
          ┌──────────────────────────┐
          │    Memory Manager        │
          ├──────────────────────────┤
          │ • Short-term Store       │
          │ • Embedding Engine       │
          │ • Semantic Search        │
          │ • Summarization          │
          └──────────────────────────┘
```

###  Memory Flow

1. **User sends message** → Stored in Cortex short-term memory with embeddings
2. **Context retrieval** → Semantic search finds relevant past messages
3. **Response generation** → Llama model uses context for better answers
4. **Response stored** → Bot response saved to memory for future context

## Testing

### Automated Test Suite

Run comprehensive integration tests to verify Cortex SDK functionality:

```bash
python test_chatbot_cortex.py
```

**Test Coverage**:
1. ✅ **Server Health** - Check if chatbot and Cortex are running
2. ✅ **Basic Conversation** - Simple question/answer
3. ✅ **Context Recall** - Test memory retrieval (e.g., "What's my favorite color?")
4. ✅ **Semantic Search** - Test similar questions find same context
5. ✅ **Conversation History** - API endpoint for history retrieval
6. ✅ **Memory Statistics** - Cortex memory usage stats
7. ✅ **Multi-turn Conversation** - Context maintained across turns
8. ✅ **Session Isolation** - Different sessions don't share memory
9. ✅ **Cortex Features** - Summarization and advanced features

### Manual Testing

Test conversation memory manually:

```bash
# Terminal 1: Start the chatbot
python start_chatbot.py

# Terminal 2: Test with curl
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is Alice and I love Python", "session_id": "test001"}'

# Ask a follow-up question
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?", "session_id": "test001"}'

# The bot should recall "Alice" from previous message!
```

### Test Scenarios

**Scenario 1: Memory Recall**
```
User: "My favorite color is blue"
Bot: [acknowledges]
User: "What's my favorite color?"
Bot: "Your favorite color is blue" ✓
```

**Scenario 2: Semantic Search**
```
User: "I work at Google"
Bot: [acknowledges]
User: "Where do I work?"     → Should mention Google ✓
User: "What's my company?"   → Should mention Google ✓
User: "My workplace?"        → Should mention Google ✓
```

**Scenario 3: Session Isolation**
```
Session A: "My name is Alice"
Session B: "What's my name?" → Should NOT know "Alice" ✓
```

## Development

This chatbot is a **test application** for the Cortex SDK. It demonstrates:
- Using Cortex as an external Python package
- In-memory backend for fast access
- Semantic search for intelligent context retrieval
- Session-based memory management
- Memory statistics and monitoring

To modify or extend:
- See `cortex_chat.py` for Cortex integration
- See `simple_app.py` for API endpoints
- See `test_chatbot_cortex.py` for test suite
- Cortex SDK is installed in development mode from `../`
