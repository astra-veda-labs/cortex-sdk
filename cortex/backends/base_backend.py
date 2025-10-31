"""
Base Backend for Cortex SDK

Abstract base class for all memory backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..utils.schema import Memory, MemoryType, MemoryPriority, MemorySearchResult


class BaseBackend(ABC):
    """Abstract base class for all Cortex memory backends"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the backend"""
        pass
    
    @abstractmethod
    def store_memory(self, memory: Memory) -> bool:
        """Store a memory"""
        pass
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID"""
        pass
    
    @abstractmethod
    def search_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_similarity: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Search memories"""
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        pass
    
    @abstractmethod
    def clear_memories(self, memory_type: Optional[MemoryType] = None) -> bool:
        """Clear memories"""
        pass
    
    @abstractmethod
    def get_memory_count(self, memory_type: Optional[MemoryType] = None) -> int:
        """Get memory count"""
        pass
    
    @abstractmethod
    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend information"""
        pass

