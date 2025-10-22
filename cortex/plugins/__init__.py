"""
Cortex Plugins Module

Backend storage plugins for different database systems.
"""

from cortex.plugins.local_memory_plugin import LocalMemoryPlugin

__all__ = [
    "LocalMemoryPlugin",
]

# Optional plugins (may not be available without dependencies)
try:
    from cortex.plugins.sqlite_plugin import SQLitePlugin
    __all__.append("SQLitePlugin")
except ImportError:
    pass

try:
    from cortex.plugins.pgvector_plugin import PGVectorPlugin
    __all__.append("PGVectorPlugin")
except ImportError:
    pass

