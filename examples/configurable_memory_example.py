#!/usr/bin/env python3
"""
Cortex SDK Configurable Memory Example

This example demonstrates how to use the Cortex SDK with different backends
and configuration switching.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cortex.core.configurable_memory_manager import ConfigurableMemoryManager
from cortex.config.backend_config import BackendType, get_cortex_config
from cortex.backends.base_backend import MemoryType, MemoryPriority


def demonstrate_in_memory():
    """Demonstrate in-memory backend"""
    print("🔧 Testing In-Memory Backend")
    print("=" * 40)
    
    # Initialize with in-memory backend
    memory_manager = ConfigurableMemoryManager()
    
    if not memory_manager.is_initialized():
        print("❌ Failed to initialize memory manager")
        return
    
    print("✅ Memory manager initialized")
    
    # Store some memories
    memories = [
        ("User likes Python programming", {"session_id": "user123", "topic": "programming"}),
        ("User works at Google", {"session_id": "user123", "topic": "work"}),
        ("User's favorite color is blue", {"session_id": "user123", "topic": "personal"}),
    ]
    
    for content, metadata in memories:
        success = memory_manager.store_memory(
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.MEDIUM,
            metadata=metadata
        )
        print(f"  Stored: {content[:30]}... {'✅' if success else '❌'}")
    
    # Recall memories
    print("\n🔍 Recalling memories...")
    results = memory_manager.recall(
        query="What does the user like?",
        limit=3
    )
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.memory.content} (similarity: {result.similarity:.2f})")
    
    # Get backend info
    info = memory_manager.get_backend_info()
    print(f"\n📊 Backend Info: {info['type']} - {info['total_memories']} memories")
    
    print()


def demonstrate_backend_switching():
    """Demonstrate backend switching"""
    print("🔄 Testing Backend Switching")
    print("=" * 40)
    
    # Get configuration
    config = get_cortex_config()
    
    # Show current status
    print("Current configuration:")
    backend_info = config.get_backend_info()
    print(f"  Default backend: {backend_info['default_backend']}")
    print(f"  Active backends: {len(backend_info['active_backends'])}")
    
    # Try switching to Chroma (if available)
    try:
        print("\n🔄 Switching to Chroma backend...")
        config.switch_to_chroma(persistent=False, collection_name="test_memories")
        print("✅ Switched to Chroma backend")
        
        # Show updated status
        backend_info = config.get_backend_info()
        print(f"  New default backend: {backend_info['default_backend']}")
        
    except Exception as e:
        print(f"❌ Failed to switch to Chroma: {e}")
        print("  (Chroma may not be installed. Install with: pip install cortex-sdk[chroma])")
    
    # Switch back to in-memory
    print("\n🔄 Switching back to in-memory...")
    config.switch_to_in_memory()
    print("✅ Switched back to in-memory")
    
    print()


def demonstrate_configuration_management():
    """Demonstrate configuration management"""
    print("⚙️ Testing Configuration Management")
    print("=" * 40)
    
    # Get configuration
    config = get_cortex_config()
    
    # Show all backends
    backend_info = config.get_backend_info()
    print("Available backends:")
    for backend in backend_info["available_backends"]:
        status = "✅ ENABLED" if backend["enabled"] else "❌ DISABLED"
        print(f"  {backend['type']}: {status}")
        if backend["config"]:
            print(f"    Config: {backend['config']}")
    
    # Enable Chroma backend
    print("\n🔧 Enabling Chroma backend...")
    config.enable_backend(BackendType.CHROMA, {
        "persistent": False,
        "collection_name": "example_memories"
    })
    print("✅ Chroma backend enabled")
    
    # Show updated status
    backend_info = config.get_backend_info()
    active_backends = [b["type"] for b in backend_info["active_backends"]]
    print(f"  Active backends: {active_backends}")
    
    # Save configuration
    config.save_config()
    print("💾 Configuration saved")
    
    print()


def main():
    """Main demonstration function"""
    print("🧠 Cortex SDK Configurable Memory Demo")
    print("=" * 50)
    print()
    
    try:
        # Test in-memory backend
        demonstrate_in_memory()
        
        # Test backend switching
        demonstrate_backend_switching()
        
        # Test configuration management
        demonstrate_configuration_management()
        
        print("✅ All demonstrations completed successfully!")
        print()
        print("Next steps:")
        print("  1. Install additional backends: pip install cortex-sdk[chroma,qdrant]")
        print("  2. Use CLI: cortex-cli status")
        print("  3. Switch backends: cortex-cli switch chroma")
        print("  4. Check documentation: docs/PACKAGING_AND_RELEASE_GUIDE.md")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
