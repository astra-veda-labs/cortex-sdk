"""
Long-term memory store for Cortex SDK.
Manages persistent memories with efficient storage and retrieval.
"""

from typing import List, Optional, Dict
from datetime import datetime
from cortex.utils.schema import Memory, MemoryType
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class LongTermStore:
    """
    Long-term memory storage for persistent memories.
    Uses dictionary-based storage with indexing for efficient retrieval.
    """
    
    def __init__(self, capacity: int = 10000):
        """
        Initialize long-term store.
        
        Args:
            capacity: Maximum number of memories to store
        """
        self.capacity = capacity
        self.memories: Dict[str, Memory] = {}
        self.tag_index: Dict[str, List[str]] = {}  # tag -> [memory_ids]
        self.time_index: List[tuple] = []  # [(timestamp, memory_id)]
        self.logger = get_logger(__name__)
        self.logger.info(f"Initialized LongTermStore with capacity: {capacity}")
    
    def add(self, memory: Memory) -> bool:
        """
        Add a memory to long-term store.
        
        Args:
            memory: Memory to add
            
        Returns:
            True if added successfully
        """
        try:
            # Ensure it's marked as long-term
            memory.memory_type = MemoryType.LONG_TERM
            
            # Check capacity
            if len(self.memories) >= self.capacity and memory.id not in self.memories:
                self.logger.warning("Long-term store at capacity")
                # Could implement eviction strategy here
                return False
            
            # Store memory
            self.memories[memory.id] = memory
            
            # Update tag index
            for tag in memory.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                if memory.id not in self.tag_index[tag]:
                    self.tag_index[tag].append(memory.id)
            
            # Update time index
            self.time_index.append((memory.created_at, memory.id))
            self.time_index.sort(key=lambda x: x[0])
            
            self.logger.debug(f"Added memory to long-term store: {memory.id}")
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
            memory.update_access()
            self.logger.debug(f"Retrieved memory from long-term store: {memory_id}")
        
        return memory
    
    def remove(self, memory_id: str) -> bool:
        """
        Remove a memory from store.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if removed successfully
        """
        if memory_id not in self.memories:
            return False
        
        memory = self.memories[memory_id]
        
        # Remove from memory store
        del self.memories[memory_id]
        
        # Remove from tag index
        for tag in memory.tags:
            if tag in self.tag_index and memory_id in self.tag_index[tag]:
                self.tag_index[tag].remove(memory_id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
        
        # Remove from time index
        self.time_index = [(t, mid) for t, mid in self.time_index if mid != memory_id]
        
        self.logger.debug(f"Removed memory from long-term store: {memory_id}")
        return True
    
    def update(self, memory: Memory) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory: Updated memory object
            
        Returns:
            True if updated successfully
        """
        if memory.id not in self.memories:
            return False
        
        old_memory = self.memories[memory.id]
        
        # Update tag index if tags changed
        old_tags = set(old_memory.tags)
        new_tags = set(memory.tags)
        
        # Remove from old tags
        for tag in old_tags - new_tags:
            if tag in self.tag_index and memory.id in self.tag_index[tag]:
                self.tag_index[tag].remove(memory.id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
        
        # Add to new tags
        for tag in new_tags - old_tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            if memory.id not in self.tag_index[tag]:
                self.tag_index[tag].append(memory.id)
        
        # Update memory
        memory.updated_at = datetime.utcnow()
        self.memories[memory.id] = memory
        
        self.logger.debug(f"Updated memory in long-term store: {memory.id}")
        return True
    
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
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """
        Search memories by criteria.
        
        Args:
            tags: Filter by tags
            min_relevance: Minimum relevance score
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        results = []
        
        # Get candidate memory IDs based on tags
        if tags:
            candidate_ids = set()
            for tag in tags:
                if tag in self.tag_index:
                    candidate_ids.update(self.tag_index[tag])
            candidates = [self.memories[mid] for mid in candidate_ids if mid in self.memories]
        else:
            candidates = list(self.memories.values())
        
        # Sort by creation time (newest first)
        candidates.sort(key=lambda m: m.created_at, reverse=True)
        
        for memory in candidates:
            # Check if expired
            if memory.is_expired():
                continue
            
            # Filter by relevance
            if min_relevance and memory.relevance_score < min_relevance:
                continue
            
            # Filter by date range
            if start_date and memory.created_at < start_date:
                continue
            if end_date and memory.created_at > end_date:
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
        self.tag_index.clear()
        self.time_index.clear()
        self.logger.info(f"Cleared {count} memories from long-term store")
    
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
    
    def get_by_tags(self, tags: List[str]) -> List[Memory]:
        """
        Get memories with specific tags.
        
        Args:
            tags: List of tags to search for
            
        Returns:
            List of memories with any of the tags
        """
        memory_ids = set()
        for tag in tags:
            if tag in self.tag_index:
                memory_ids.update(self.tag_index[tag])
        
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
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
            'total_tags': len(self.tag_index),
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
    
    def get_oldest(self, n: int = 1) -> List[Memory]:
        """
        Get the n oldest memories.
        
        Args:
            n: Number of memories to get
            
        Returns:
            List of oldest memories
        """
        sorted_by_time = sorted(self.memories.values(), key=lambda m: m.created_at)
        return sorted_by_time[:n]
    
    def get_newest(self, n: int = 1) -> List[Memory]:
        """
        Get the n newest memories.
        
        Args:
            n: Number of memories to get
            
        Returns:
            List of newest memories
        """
        sorted_by_time = sorted(self.memories.values(), key=lambda m: m.created_at, reverse=True)
        return sorted_by_time[:n]
    
    def get_low_relevance(self, threshold: float = 0.3, limit: Optional[int] = None) -> List[Memory]:
        """
        Get memories with low relevance scores.
        
        Args:
            threshold: Relevance threshold
            limit: Maximum results
            
        Returns:
            List of low relevance memories
        """
        low_relevance = [m for m in self.memories.values() if m.relevance_score < threshold]
        low_relevance.sort(key=lambda m: m.relevance_score)
        
        if limit:
            return low_relevance[:limit]
        return low_relevance

