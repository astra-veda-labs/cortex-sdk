# 🔧 YAML Configuration API for Cortex SDK

## 📋 **Overview**

The Cortex SDK now uses a simple YAML-based configuration system for switching between in-memory and Chroma backends. This provides an easy way to configure the SDK without complex setup.

---

## 🚀 **Quick Start**

### **1. Configuration File (`cortex_config.yaml`)**
```yaml
# Cortex SDK Configuration
# Switch between in-memory and Chroma backends

# Current backend: in_memory | chroma
backend: in_memory

# Backend configurations
backends:
  in_memory:
    enabled: true
    config:
      capacity: 1000
      persistent: false
  
  chroma:
    enabled: false
    config:
      persistent: false
      collection_name: "cortex_memories"
      similarity_threshold: 0.5
      embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

### **2. Programmatic Usage**
```python
from cortex.config.yaml_config import get_yaml_config

# Get configuration
config = get_yaml_config()

# Switch to in-memory
config.switch_to_in_memory()

# Switch to Chroma
config.switch_to_chroma(persistent=True, collection_name="my_memories")

# Get current backend
current_backend = config.get_current_backend()
print(f"Current backend: {current_backend}")
```

### **3. API Endpoints (Flask Integration)**
```bash
# Get current configuration
GET /config/status

# Switch backend
POST /config/switch
{
  "backend": "chroma",
  "config": {
    "persistent": true,
    "collection_name": "my_memories"
  }
}

# Reset to defaults
POST /config/reset

# Test backend
POST /config/test
{
  "backend": "chroma"
}
```

---

## 🔧 **Backend Options**

### **In-Memory Backend**
- **Use Case**: Development, testing, small datasets
- **Performance**: Fastest (1-5ms queries)
- **Memory**: High usage, not persistent
- **Setup**: Instant

**Configuration:**
```yaml
in_memory:
  enabled: true
  config:
    capacity: 1000
    persistent: false
```

### **Chroma Backend**
- **Use Case**: General purpose, easy setup
- **Performance**: Good (10-50ms queries)
- **Memory**: Medium usage, optional persistence
- **Setup**: 5 minutes

**Configuration:**
```yaml
chroma:
  enabled: true
  config:
    persistent: false
    collection_name: "cortex_memories"
    similarity_threshold: 0.5
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

---

## 📊 **API Reference**

### **YAMLConfig Class**

#### **Methods:**
- `get_current_backend()` → str
- `get_backend_config(backend: str)` → Dict[str, Any]
- `switch_to_in_memory()`
- `switch_to_chroma(persistent: bool, collection_name: str)`
- `is_backend_enabled(backend: str)` → bool
- `get_backend_info()` → Dict[str, Any]

#### **Example:**
```python
from cortex.config.yaml_config import get_yaml_config

config = get_yaml_config()

# Get current backend
backend = config.get_current_backend()
print(f"Current backend: {backend}")

# Switch to Chroma with persistent storage
config.switch_to_chroma(persistent=True, collection_name="production_memories")

# Check if backend is enabled
if config.is_backend_enabled("chroma"):
    print("Chroma backend is enabled")

# Get backend information
info = config.get_backend_info()
print(f"Backend info: {info}")
```

---

## 🎯 **Use Cases**

### **Development**
```yaml
backend: in_memory
backends:
  in_memory:
    enabled: true
    config:
      capacity: 1000
      persistent: false
```

### **Testing**
```yaml
backend: chroma
backends:
  chroma:
    enabled: true
    config:
      persistent: false
      collection_name: "test_memories"
```

### **Production**
```yaml
backend: chroma
backends:
  chroma:
    enabled: true
    config:
      persistent: true
      collection_name: "production_memories"
      similarity_threshold: 0.7
```

---

## 🔄 **Switching Backends**

### **Programmatic Switching:**
```python
from cortex.config.yaml_config import get_yaml_config

config = get_yaml_config()

# Switch to in-memory
config.switch_to_in_memory()

# Switch to Chroma
config.switch_to_chroma(persistent=True, collection_name="my_memories")
```

### **Manual Configuration:**
```yaml
# Edit cortex_config.yaml
backend: chroma

backends:
  in_memory:
    enabled: false
  chroma:
    enabled: true
    config:
      persistent: true
      collection_name: "my_memories"
```

### **API Switching:**
```bash
# Switch to Chroma
curl -X POST http://localhost:5001/config/switch \
  -H "Content-Type: application/json" \
  -d '{"backend": "chroma", "config": {"persistent": true}}'

# Switch to in-memory
curl -X POST http://localhost:5001/config/switch \
  -H "Content-Type: application/json" \
  -d '{"backend": "in_memory"}'
```

---

## 🧪 **Testing**

### **Test Configuration:**
```python
from cortex.config.yaml_config import get_yaml_config

# Test configuration loading
config = get_yaml_config()
print(f"Current backend: {config.get_current_backend()}")

# Test switching
config.switch_to_chroma(persistent=True)
print(f"After switch: {config.get_current_backend()}")

# Test backend info
info = config.get_backend_info()
print(f"Backend info: {info}")
```

### **Test API Endpoints:**
```bash
# Test configuration status
curl http://localhost:5001/config/status

# Test backend switching
curl -X POST http://localhost:5001/config/switch \
  -H "Content-Type: application/json" \
  -d '{"backend": "chroma"}'

# Test reset
curl -X POST http://localhost:5001/config/reset
```

---

## 📚 **Best Practices**

### **1. Configuration Management**
- Use different YAML files for different environments
- Version control your configuration files
- Use environment variables for sensitive data

### **2. Backend Selection**
- **Development**: In-memory (fast, temporary)
- **Testing**: Chroma (persistent: false)
- **Production**: Chroma (persistent: true)

### **3. Performance Optimization**
- Choose the right backend for your use case
- Monitor memory usage and query latency
- Use persistent storage for production

---

## 🎯 **Conclusion**

The YAML configuration system provides a simple, flexible way to manage Cortex SDK backends:

- ✅ **Simple Configuration**: YAML-based configuration
- ✅ **Easy Switching**: Programmatic and API switching
- ✅ **Two Backends**: In-memory and Chroma
- ✅ **Flexible**: Easy to extend with more backends
- ✅ **Production Ready**: Suitable for development and production

**The YAML configuration makes it easy to switch between backends without changing your code!** 🚀✅
