"""
Local memory plugin for Cortex SDK.
Provides in-memory storage backend (default).
"""

from typing import List, Optional, Dict
from cortex.utils.schema import Memory
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class LocalMemoryPlugin:
    """
    Local in-memory storage plugin.
    Uses dictionaries for fast access but no persistence.
    """
    
    def __init__(self):
        """Initialize local memory plugin."""
        self.memories: Dict[str, Memory] = {}
        self.logger = get_logger(__name__)
        self.logger.info("Initialized LocalMemoryPlugin")
    
    def store_memory(self, memory: Memory) -> bool:
        """
        Store a memory.
        
        Args:
            memory: Memory to store
            
        Returns:
            True if stored successfully
        """
        try:
            self.memories[memory.id] = memory
            self.logger.debug(f"Stored memory: {memory.id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}", exc_info=True)
            return False
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object or None
        """
        return self.memories.get(memory_id)
    
    def update_memory(self, memory: Memory) -> bool:
        """
        Update a memory.
        
        Args:
            memory: Updated memory object
            
        Returns:
            True if updated successfully
        """
        if memory.id in self.memories:
            self.memories[memory.id] = memory
            return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully
        """
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False
    
    def search_memories(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Memory]:
        """
        Search memories (returns all for local plugin).
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of memories
        """
        # Local plugin just returns all memories
        # Actual similarity computation is done by MemoryManager
        return list(self.memories.values())
    
    def clear(self):
        """Clear all memories."""
        self.memories.clear()
        self.logger.info("Cleared all memories from local storage")
    
    def get_count(self) -> int:
        """Get number of stored memories."""
        return len(self.memories)

