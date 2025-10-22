"""
Cortex SDK - Intelligent Memory Management System

A powerful Python SDK for managing short-term and long-term memory with
semantic search, summarization, and flexible backend plugins.
"""

from cortex.core.memory_manager import MemoryManager
from cortex.api.memory import Memory, MemorySearch
from cortex.api.config import MemoryConfig

__version__ = "0.1.0"
__all__ = ["MemoryManager", "Memory", "MemorySearch", "MemoryConfig"]

