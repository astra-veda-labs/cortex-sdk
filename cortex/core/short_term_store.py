"""
Short-term memory store for Cortex SDK.
Manages recent, frequently accessed memories with fast retrieval.
"""

from typing import List, Optional, Dict
from collections import OrderedDict
from datetime import datetime
from cortex.utils.schema import Memory, MemoryType
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class ShortTermStore:
    """
    Short-term memory storage using LRU cache strategy.
    Optimized for fast access and recent memories.
    """
    
    def __init__(self, capacity: int = 1000):
        """
        Initialize short-term store.
        
        Args:
            capacity: Maximum number of memories to store
        """
        self.capacity = capacity
        self.memories: OrderedDict[str, Memory] = OrderedDict()
        self.logger = get_logger(__name__)
        self.logger.info(f"Initialized ShortTermStore with capacity: {capacity}")
    
    def add(self, memory: Memory) -> bool:
        """
        Add a memory to short-term store.
        
        Args:
            memory: Memory to add
            
        Returns:
            True if added successfully
        """
        try:
            # Ensure it's marked as short-term
            memory.memory_type = MemoryType.SHORT_TERM
            
            # Remove if already exists (to update position)
            if memory.id in self.memories:
                del self.memories[memory.id]
            
            # Add to end (most recent)
            self.memories[memory.id] = memory
            
            # Evict oldest if over capacity
            if len(self.memories) > self.capacity:
                oldest_id = next(iter(self.memories))
                removed = self.memories.pop(oldest_id)
                self.logger.debug(f"Evicted oldest memory: {oldest_id}")
            
            self.logger.debug(f"Added memory to short-term store: {memory.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add memory: {e}", exc_info=True)
            return False
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object or None
        """
        memory = self.memories.get(memory_id)
        
        if memory:
            # Move to end (mark as recently accessed)
            self.memories.move_to_end(memory_id)
            memory.update_access()
            self.logger.debug(f"Retrieved memory from short-term store: {memory_id}")
        
        return memory
    
    def remove(self, memory_id: str) -> bool:
        """
        Remove a memory from store.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if removed successfully
        """
        if memory_id in self.memories:
            del self.memories[memory_id]
            self.logger.debug(f"Removed memory from short-term store: {memory_id}")
            return True
        return False
    
    def update(self, memory: Memory) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory: Updated memory object
            
        Returns:
            True if updated successfully
        """
        if memory.id in self.memories:
            memory.updated_at = datetime.utcnow()
            self.memories[memory.id] = memory
            self.memories.move_to_end(memory.id)
            self.logger.debug(f"Updated memory in short-term store: {memory.id}")
            return True
        return False
    
    def get_all(self) -> List[Memory]:
        """
        Get all memories in store.
        
        Returns:
            List of all memories
        """
        return list(self.memories.values())
    
    def search(
        self,
        tags: Optional[List[str]] = None,
        min_relevance: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Search memories by criteria.
        
        Args:
            tags: Filter by tags
            min_relevance: Minimum relevance score
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        results = []
        
        for memory in reversed(self.memories.values()):  # Most recent first
            # Check if expired
            if memory.is_expired():
                continue
            
            # Filter by tags
            if tags and not any(tag in memory.tags for tag in tags):
                continue
            
            # Filter by relevance
            if min_relevance and memory.relevance_score < min_relevance:
                continue
            
            results.append(memory)
            
            # Check limit
            if limit and len(results) >= limit:
                break
        
        return results
    
    def clear(self):
        """Clear all memories from store."""
        count = len(self.memories)
        self.memories.clear()
        self.logger.info(f"Cleared {count} memories from short-term store")
    
    def get_expired(self) -> List[Memory]:
        """
        Get all expired memories.
        
        Returns:
            List of expired memories
        """
        return [m for m in self.memories.values() if m.is_expired()]
    
    def remove_expired(self) -> int:
        """
        Remove all expired memories.
        
        Returns:
            Number of memories removed
        """
        expired_ids = [m.id for m in self.get_expired()]
        
        for mem_id in expired_ids:
            self.remove(mem_id)
        
        if expired_ids:
            self.logger.info(f"Removed {len(expired_ids)} expired memories")
        
        return len(expired_ids)
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the store.
        
        Returns:
            Dictionary of statistics
        """
        memories_list = list(self.memories.values())
        
        stats = {
            'total_memories': len(memories_list),
            'capacity': self.capacity,
            'utilization': len(memories_list) / self.capacity if self.capacity > 0 else 0,
            'expired_count': len(self.get_expired()),
        }
        
        if memories_list:
            stats.update({
                'oldest_memory': min(m.created_at for m in memories_list),
                'newest_memory': max(m.created_at for m in memories_list),
                'avg_relevance': sum(m.relevance_score for m in memories_list) / len(memories_list),
                'total_accesses': sum(m.access_count for m in memories_list),
            })
        
        return stats
    
    def is_full(self) -> bool:
        """Check if store is at capacity."""
        return len(self.memories) >= self.capacity
    
    def get_oldest(self) -> Optional[Memory]:
        """Get the oldest memory in store."""
        if self.memories:
            oldest_id = next(iter(self.memories))
            return self.memories[oldest_id]
        return None
    
    def get_newest(self) -> Optional[Memory]:
        """Get the newest memory in store."""
        if self.memories:
            newest_id = next(reversed(self.memories))
            return self.memories[newest_id]
        return None

