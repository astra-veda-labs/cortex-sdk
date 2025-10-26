# 🔧 Configurable Backend System for Cortex SDK

## 📋 **System Overview**

The Cortex SDK now includes a comprehensive configurable backend system that allows seamless switching between different storage backends using configuration files and CLI commands.

---

## 🏗️ **Architecture**

### **Backend Abstraction Layer:**
```
Cortex SDK
├── Core Memory Manager
├── Backend Abstraction
│   ├── BaseBackend (Interface)
│   ├── InMemoryBackend (Default)
│   ├── ChromaBackend (Recommended)
│   ├── QdrantBackend (Production)
│   ├── LanceBackend (Performance)
│   └── WeaviateBackend (Enterprise)
├── Configuration System
│   ├── JSON Configuration
│   ├── CLI Interface
│   └── Programmatic API
└── Examples & Documentation
```

### **Configuration Flow:**
```
User → CLI/API → cortex_config.json → Backend Selection → Memory Operations
```

---

## 🚀 **Quick Start**

### **1. Basic Usage**
```python
from cortex.core.configurable_memory_manager import ConfigurableMemoryManager

# Initialize with default configuration
memory_manager = ConfigurableMemoryManager()

# Store memory
memory_manager.store_memory(
    content="User likes Python programming",
    metadata={"session_id": "user123"}
)

# Recall memories
results = memory_manager.recall("What does the user like?")
```

### **2. CLI Configuration**
```bash
# Show current status
cortex-cli status

# Switch to Chroma
cortex-cli switch chroma --persistent true

# Switch to Qdrant
cortex-cli switch qdrant --host localhost --port 6333

# Switch back to in-memory
cortex-cli switch in_memory
```

### **3. Programmatic Configuration**
```python
from cortex.config.backend_config import BackendType

# Switch backends programmatically
memory_manager.switch_backend(
    BackendType.CHROMA,
    {"persistent": True, "collection_name": "my_memories"}
)
```

---

## 🔧 **Backend Options**

### **1. In-Memory Backend (Default)**
- **Use Case**: Development, testing, small datasets
- **Performance**: Fastest (1-5ms queries)
- **Memory**: High usage, not persistent
- **Setup**: Instant

```json
{
  "in_memory": {
    "enabled": true,
    "config": {
      "capacity": 1000,
      "persistent": false
    }
  }
}
```

### **2. Chroma Backend (Recommended)**
- **Use Case**: General purpose, easy setup
- **Performance**: Good (10-50ms queries)
- **Memory**: Medium usage, optional persistence
- **Setup**: 5 minutes

```json
{
  "chroma": {
    "enabled": false,
    "config": {
      "persistent": false,
      "collection_name": "cortex_memories",
      "similarity_threshold": 0.5,
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    }
  }
}
```

### **3. Qdrant Backend (Production)**
- **Use Case**: Production scale, high performance
- **Performance**: Excellent (5-30ms queries)
- **Memory**: Low usage, persistent
- **Setup**: 15 minutes

```json
{
  "qdrant": {
    "enabled": false,
    "config": {
      "host": "localhost",
      "port": 6333,
      "collection_name": "cortex_memories",
      "similarity_threshold": 0.5,
      "vector_size": 384
    }
  }
}
```

### **4. Lance Backend (Performance)**
- **Use Case**: Ultra-fast queries, minimal memory
- **Performance**: Fastest (2-20ms queries)
- **Memory**: Very low usage, persistent
- **Setup**: 10 minutes

```json
{
  "lance": {
    "enabled": false,
    "config": {
      "path": "./cortex_vectors.lance",
      "similarity_threshold": 0.5,
      "vector_size": 384
    }
  }
}
```

### **5. Weaviate Backend (Enterprise)**
- **Use Case**: Enterprise features, advanced search
- **Performance**: Good (20-100ms queries)
- **Memory**: High usage, persistent
- **Setup**: 30 minutes

```json
{
  "weaviate": {
    "enabled": false,
    "config": {
      "url": "http://localhost:8080",
      "class_name": "CortexMemory",
      "similarity_threshold": 0.5
    }
  }
}
```

---

## 📦 **Installation & Setup**

### **1. Basic Installation**
```bash
# Install Cortex SDK
pip install cortex-sdk

# Or from source
pip install -e .
```

### **2. Backend-Specific Installation**
```bash
# Install with specific backends
pip install cortex-sdk[chroma]
pip install cortex-sdk[qdrant]
pip install cortex-sdk[lance]
pip install cortex-sdk[weaviate]

# Install all backends
pip install cortex-sdk[all]
```

### **3. Development Installation**
```bash
# Install in development mode
pip install -e .

# With specific backends
pip install -e .[chroma,qdrant]
```

---

## 🔄 **Backend Switching**

### **1. CLI Switching**
```bash
# Show current status
cortex-cli status

# Switch to different backends
cortex-cli switch in_memory
cortex-cli switch chroma --persistent true
cortex-cli switch qdrant --host localhost --port 6333
cortex-cli switch lance --path ./vectors.lance

# Enable/disable backends
cortex-cli enable chroma --persistent true
cortex-cli disable qdrant

# Reset to defaults
cortex-cli reset
```

### **2. Programmatic Switching**
```python
from cortex.core.configurable_memory_manager import ConfigurableMemoryManager
from cortex.config.backend_config import BackendType

# Initialize
memory_manager = ConfigurableMemoryManager()

# Switch to Chroma
memory_manager.switch_backend(
    BackendType.CHROMA,
    {"persistent": True, "collection_name": "my_memories"}
)

# Switch to Qdrant
memory_manager.switch_backend(
    BackendType.QDRANT,
    {"host": "localhost", "port": 6333}
)
```

### **3. Configuration File Switching**
```python
from cortex.config.backend_config import get_cortex_config

# Get configuration
config = get_cortex_config()

# Switch to Chroma
config.switch_to_chroma(persistent=True)

# Switch to Qdrant
config.switch_to_qdrant(host="localhost", port=6333)

# Save configuration
config.save_config()
```

---

## 📊 **Performance Comparison**

| Backend | Setup Time | Query Latency | Memory Usage | Persistence | Scalability |
|---------|-------------|---------------|--------------|-------------|-------------|
| **In-Memory** | 0ms | 1-5ms | High | ❌ | Limited |
| **Chroma** | 5min | 10-50ms | Medium | ✅ | Good |
| **Qdrant** | 15min | 5-30ms | Low | ✅ | Excellent |
| **Lance** | 10min | 2-20ms | Very Low | ✅ | Good |
| **Weaviate** | 30min | 20-100ms | High | ✅ | Excellent |

---

## 🎯 **Use Case Recommendations**

### **Development & Testing**
```bash
# Use in-memory for fast iteration
cortex-cli switch in_memory
```

### **General Purpose**
```bash
# Use Chroma for easy setup
cortex-cli switch chroma --persistent false
```

### **Production Scale**
```bash
# Use Qdrant for production
cortex-cli switch qdrant --host qdrant.example.com --port 6333
```

### **Maximum Performance**
```bash
# Use Lance for ultra-fast queries
cortex-cli switch lance --path /data/vectors.lance
```

### **Enterprise Features**
```bash
# Use Weaviate for advanced features
cortex-cli switch weaviate --url http://weaviate.example.com:8080
```

---

## 🧪 **Testing**

### **1. Run Example**
```bash
# Test the configuration system
python examples/configurable_memory_example.py
```

### **2. Test CLI**
```bash
# Test CLI commands
cortex-cli status
cortex-cli switch chroma
cortex-cli switch in_memory
```

### **3. Test Backend Switching**
```python
# Test programmatic switching
from cortex.core.configurable_memory_manager import ConfigurableMemoryManager

memory_manager = ConfigurableMemoryManager()
print(f"Initialized: {memory_manager.is_initialized()}")
print(f"Backend info: {memory_manager.get_backend_info()}")
```

---

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Backend Not Available**
   ```bash
   # Install missing backend
   pip install cortex-sdk[chroma]
   ```

2. **Configuration Errors**
   ```bash
   # Reset to defaults
   cortex-cli reset
   ```

3. **Performance Issues**
   ```bash
   # Check backend status
   cortex-cli status
   
   # Switch to faster backend
   cortex-cli switch lance
   ```

### **Debug Information:**
```python
# Get detailed backend info
memory_manager = ConfigurableMemoryManager()
info = memory_manager.get_backend_info()
print(f"Backend: {info['type']}")
print(f"Initialized: {info['initialized']}")
print(f"Total memories: {info.get('total_memories', 0)}")
```

---

## 📚 **Best Practices**

### **1. Configuration Management**
- Use different config files for different environments
- Version control your configuration files
- Use environment variables for sensitive data

### **2. Backend Selection**
- **Development**: In-memory
- **Testing**: Chroma (persistent: false)
- **Production**: Qdrant or Lance
- **Enterprise**: Weaviate

### **3. Performance Optimization**
- Choose the right backend for your use case
- Monitor memory usage and query latency
- Use persistent storage for production

---

## 🎯 **Conclusion**

The Cortex SDK now provides a flexible, configurable memory management system that can adapt to different use cases and environments. The backend switching system allows you to:

- **Start simple** with in-memory storage
- **Scale up** to production databases
- **Optimize** for specific performance requirements
- **Switch easily** between different backends

**Key Benefits:**
- ✅ **Easy Configuration**: JSON-based configuration
- ✅ **CLI Interface**: Simple command-line management
- ✅ **Programmatic API**: Full programmatic control
- ✅ **Multiple Backends**: Choose the right backend for your needs
- ✅ **Seamless Switching**: Change backends without code changes
- ✅ **Performance Optimization**: Optimize for your specific use case

**The configuration system makes it easy to switch between backends without changing your code!** 🚀✅
