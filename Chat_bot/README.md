# AI Chat Bot

A modern AI assistant powered by Llama-2-7B with a beautiful web interface.

## Features

- 🤖 **AI-Powered**: Uses Llama-2-7B model for intelligent responses
- 💬 **Real-time Chat**: Interactive chat interface with typing indicators
- 📱 **Modern UI**: Clean, responsive chat interface
- 💾 **Session Management**: Maintains chat history per session
- 🚀 **Easy Setup**: Automated model download and dependency installation

## Quick Start

### Complete Setup (Recommended)
```bash
python setup.py
python start_chatbot.py
```

## Model Download

The setup script automatically tries multiple methods to get the model:

1. **Copy from existing AIMap** (if available) - Fastest
2. **Download from Hugging Face** - Automatic
3. **Download using curl** - Fallback
4. **Manual instructions** - If all else fails

The model file (`llama-2-7b-chat-hf-q2_k.gguf`, 2.5GB) is required but not included in git due to size.

### Access the UI
- Open your browser to `http://localhost:5001`
- Start chatting with your AI assistant!

## File Structure

```
Chat_bot/
├── app/
│   ├── simple_app.py          # Flask application
│   └── templates/
│       └── index.html         # Chat UI
├── rag_model/
│   ├── foundation_model/
│   │   └── llama-2-7b-chat-hf-q2_k.gguf  # Llama model
│   └── src_gpt/
│       └── interactive_chat.py            # Chat bot logic
├── requirements.txt           # Dependencies
└── README.md                 # This file
```

## Usage

The chat bot is specialized in:
- Semiconductor manufacturing processes
- Etching techniques (plasma, wet, dry)
- Photolithography
- Material science
- Process optimization

Ask questions like:
- "What is plasma etching?"
- "Explain the difference between wet and dry etching"
- "How does photolithography work?"
- "What are the advantages of ICP etching?"
