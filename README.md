# Cortex SDK

A powerful Python SDK for intelligent memory management with support for short-term and long-term storage, semantic search, summarization, and flexible backend plugins.

## Features

- **Multi-tier Memory Architecture**: Short-term, long-term, and file-based storage
- **Semantic Search**: Built-in embedding engine for intelligent memory retrieval
- **Automatic Summarization**: Compress and distill important information
- **Forgetting Mechanisms**: Configurable memory retention and cleanup
- **Pluggable Backends**: Support for PostgreSQL (pgvector), SQLite, and in-memory storage
- **Easy-to-use API**: Simple, intuitive interfaces for memory operations
- **CLI Support**: Command-line interface for memory management

## Test Application: AI Chat Bot

The Cortex SDK includes a **test application** - an AI Chat Bot powered by Llama-2-7B that demonstrates Cortex's memory management capabilities.

### Why This Matters
This chatbot showcases how to integrate Cortex SDK into real applications, demonstrating:
- **In-memory storage** for fast conversation access
- **Semantic search** for context-aware responses
- **Session management** with automatic cleanup
- **Memory statistics** for monitoring
- **Conversation summarization** using Cortex's built-in features

### Features
- 🤖 **AI-Powered**: Uses Llama-2-7B model for intelligent responses
- 🧠 **Cortex Integration**: Demonstrates real-world Cortex SDK usage
- 💬 **Real-time Chat**: Interactive chat interface with typing indicators
- 📱 **Modern UI**: Clean, responsive chat interface
- 💾 **Intelligent Memory**: Context-aware conversation with semantic search
- 🚀 **Easy Setup**: Automated Cortex SDK and model installation

### Quick Start
```bash
cd Chat_bot
python setup.py  # Installs Cortex SDK + dependencies + downloads model
python start_chatbot.py
```

Access the chat bot at `http://localhost:5001`

![AI Assistant Chat Interface](Chat_bot/screenshot.png)

**Note**: This is a demonstration of Cortex SDK's capabilities. The Cortex SDK itself is separate and can be used independently in any Python project.

For detailed setup instructions and API documentation, see [Chat_bot/README.md](Chat_bot/README.md)

## Installation

```bash
pip install cortex-sdk
```

## Quick Start

```python
from cortex import MemoryManager

# Initialize memory manager
memory = MemoryManager(backend="local")

# Store memories
memory.remember("The user prefers Python for data science tasks")
memory.remember("Project deadline is next Friday")

# Recall memories
results = memory.recall("What does the user prefer for data science?")
print(results)

# Get summary of memories
summary = memory.summarize(topic="project information")
print(summary)

# Forget old or irrelevant memories
memory.forget(older_than_days=30, relevance_threshold=0.3)
```

## Architecture

![Cortex SDK Architecture](docs/User_interaction-New_architecture.jpg)

```
┌─────────────────────────────────────────┐
│         Memory Manager                   │
│  (Main Orchestrator)                     │
└─────────────────┬───────────────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
┌──────▼───────┐    ┌───────▼────────┐
│ Short-term   │    │  Long-term     │
│   Store      │    │    Store       │
│  (Recent)    │    │  (Persistent)  │
└──────┬───────┘    └───────┬────────┘
       │                    │
       └──────────┬─────────┘
                  │
       ┌──────────▼──────────┐
       │  Embedding Engine   │
       │    Summarizer       │
       │  Forget Engine      │
       └─────────────────────┘
```

## Backend Plugins

### Local Memory (Default)
```python
memory = MemoryManager(backend="local")
```

### PostgreSQL with pgvector
```python
memory = MemoryManager(
    backend="pgvector",
    connection_string="postgresql://user:pass@localhost/db"
)
```

### SQLite
```python
memory = MemoryManager(
    backend="sqlite",
    db_path="./cortex_memory.db"
)
```

## Advanced Usage

### Custom Configuration
```python
from cortex.api.config import MemoryConfig

config = MemoryConfig(
    short_term_capacity=1000,
    long_term_capacity=10000,
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    summarization_model="facebook/bart-large-cnn",
    forget_threshold=0.2,
    auto_summarize=True
)

memory = MemoryManager(config=config)
```

### File Storage
```python
# Store files with metadata
memory.store_file(
    file_path="./document.pdf",
    metadata={"type": "documentation", "project": "alpha"}
)

# Retrieve files
files = memory.recall_files(query="documentation for project alpha")
```

### CLI Usage
```bash
# Initialize Cortex
cortex init --backend sqlite

# Store a memory
cortex remember "Important meeting on Monday at 10 AM"

# Recall memories
cortex recall "What meetings do I have?"

# Summarize memories
cortex summarize --topic "meetings"

# Forget old memories
cortex forget --older-than 30d
```

## Examples

See the `examples/` directory for:
- `chat_memory_example.ipynb`: Interactive notebook for chat-based memory
- `summarization_example.py`: Memory summarization use cases

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/cortex-sdk.git
cd cortex-sdk

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Requirements

- Python 3.8+
- torch (for embeddings)
- transformers (for embeddings and summarization)
- numpy
- Optional: psycopg2 (for PostgreSQL), sentence-transformers

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the GitHub issue tracker.

