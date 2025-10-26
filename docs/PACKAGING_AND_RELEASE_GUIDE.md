# 📦 Cortex SDK Packaging & Release Guide

## 📋 **Overview**

This guide covers how to package, distribute, and release the Cortex SDK with support for multiple database backends and easy configuration switching.

---

## 🏗️ **Architecture Overview**

### **Backend System:**
```
Cortex SDK
├── Core (Memory Management)
├── Backends (Database Abstraction)
│   ├── In-Memory (Default)
│   ├── Chroma (Recommended)
│   ├── Qdrant (Production)
│   ├── Lance (Performance)
│   └── Weaviate (Enterprise)
├── Configuration (JSON-based)
└── CLI (Command-line interface)
```

### **Configuration Flow:**
```
User → cortex_cli.py → cortex_config.json → Backend Selection → Memory Operations
```

---

## 🚀 **Quick Start**

### **1. Install Cortex SDK**
```bash
# Basic installation (in-memory only)
pip install cortex-sdk

# With specific backend
pip install cortex-sdk[chroma]
pip install cortex-sdk[qdrant]
pip install cortex-sdk[lance]
pip install cortex-sdk[weaviate]

# All backends
pip install cortex-sdk[all]
```

### **2. Configure Backend**
```bash
# Show current configuration
cortex-cli status

# Switch to Chroma
cortex-cli switch chroma

# Switch to Qdrant with custom config
cortex-cli switch qdrant --host localhost --port 6333

# Switch back to in-memory
cortex-cli switch in_memory
```

### **3. Use in Code**
```python
from cortex.core.configurable_memory_manager import ConfigurableMemoryManager
from cortex.config.backend_config import BackendType

# Initialize with configuration
memory_manager = ConfigurableMemoryManager("cortex_config.json")

# Store memory
memory_manager.store_memory(
    content="User likes Python programming",
    metadata={"session_id": "user123", "topic": "programming"}
)

# Recall memories
results = memory_manager.recall(
    query="What does the user like?",
    limit=5
)
```

---

## 🔧 **Backend Configuration**

### **Configuration File (`cortex_config.json`):**
```json
{
  "default_backend": "in_memory",
  "backends": {
    "in_memory": {
      "enabled": true,
      "config": {
        "capacity": 1000,
        "persistent": false
      }
    },
    "chroma": {
      "enabled": false,
      "config": {
        "persistent": false,
        "collection_name": "cortex_memories",
        "similarity_threshold": 0.5,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
      }
    },
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
}
```

### **CLI Commands:**
```bash
# Status
cortex-cli status

# Switch backends
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

---

## 📦 **Packaging Options**

### **1. Development Installation**
```bash
# Install in development mode
pip install -e .

# With specific backends
pip install -e .[chroma,qdrant]
```

### **2. Production Installation**
```bash
# From PyPI (when published)
pip install cortex-sdk[chroma]

# From source
pip install git+https://github.com/your-org/cortex-sdk.git
```

### **3. Docker Installation**
```dockerfile
FROM python:3.9-slim

# Install Cortex SDK
RUN pip install cortex-sdk[chroma]

# Copy configuration
COPY cortex_config.json /app/
WORKDIR /app

# Run your application
CMD ["python", "your_app.py"]
```

---

## 🏷️ **Release Process**

### **1. Version Management**
```python
# In cortex/__init__.py
__version__ = "0.1.0"
```

### **2. Build Package**
```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*
```

### **3. Test Package**
```bash
# Install from local build
pip install dist/cortex_sdk-0.1.0-py3-none-any.whl

# Test installation
python -c "import cortex; print(cortex.__version__)"
```

### **4. Publish to PyPI**
```bash
# Upload to PyPI
twine upload dist/*

# Or to test PyPI first
twine upload --repository testpypi dist/*
```

---

## 🔄 **Backend Switching**

### **Programmatic Switching:**
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

### **Configuration-based Switching:**
```python
# Load from different config file
memory_manager = ConfigurableMemoryManager("production_config.json")

# Or update existing config
memory_manager.config.switch_to_chroma(persistent=True)
memory_manager.config.save_config()
```

---

## 🧪 **Testing**

### **1. Unit Tests**
```bash
# Run tests
python -m pytest tests/

# With coverage
python -m pytest --cov=cortex tests/
```

### **2. Integration Tests**
```bash
# Test with different backends
python tests/test_backends.py

# Test configuration switching
python tests/test_configuration.py
```

### **3. Performance Tests**
```bash
# Benchmark different backends
python tests/benchmark_backends.py
```

---

## 📊 **Performance Comparison**

| Backend | Setup Time | Query Latency | Memory Usage | Scalability |
|---------|-------------|---------------|--------------|-------------|
| **In-Memory** | 0ms | 1-5ms | High | Limited |
| **Chroma** | 5s | 10-50ms | Medium | Good |
| **Qdrant** | 15s | 5-30ms | Low | Excellent |
| **Lance** | 10s | 2-20ms | Very Low | Good |
| **Weaviate** | 30s | 20-100ms | High | Excellent |

---

## 🚀 **Deployment Strategies**

### **1. Development**
```bash
# Use in-memory for fast iteration
cortex-cli switch in_memory
```

### **2. Testing**
```bash
# Use Chroma for testing
cortex-cli switch chroma --persistent false
```

### **3. Production**
```bash
# Use Qdrant for production scale
cortex-cli switch qdrant --host qdrant.example.com --port 6333
```

### **4. High Performance**
```bash
# Use Lance for maximum performance
cortex-cli switch lance --path /data/vectors.lance
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

The Cortex SDK provides a flexible, configurable memory management system that can adapt to different use cases and environments. The backend switching system allows you to:

- **Start simple** with in-memory storage
- **Scale up** to production databases
- **Optimize** for specific performance requirements
- **Switch easily** between different backends

**Choose your backend based on your needs:**
- **In-Memory**: Development and testing
- **Chroma**: General purpose, easy setup
- **Qdrant**: Production scale, high performance
- **Lance**: Maximum performance, minimal memory
- **Weaviate**: Enterprise features, advanced search

**The configuration system makes it easy to switch between backends without changing your code!** 🚀✅
