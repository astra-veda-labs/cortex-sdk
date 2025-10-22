"""
Forget engine for Cortex SDK.
Manages memory cleanup and forgetting based on various criteria.
"""

from typing import List, Optional, Callable
from datetime import datetime, timedelta
from cortex.utils.schema import Memory, ForgetCriteria, MemoryType, MemoryPriority
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class ForgetEngine:
    """
    Handles memory forgetting and cleanup operations.
    Implements various forgetting strategies and policies.
    """
    
    def __init__(self):
        """Initialize forget engine."""
        self.logger = get_logger(__name__)
        self.logger.info("Initialized ForgetEngine")
    
    def should_forget(self, memory: Memory, criteria: ForgetCriteria) -> bool:
        """
        Determine if a memory should be forgotten based on criteria.
        
        Args:
            memory: Memory to evaluate
            criteria: Forgetting criteria
            
        Returns:
            True if memory should be forgotten
        """
        try:
            # Check memory type filter
            if criteria.memory_type and memory.memory_type != criteria.memory_type:
                return False
            
            # Check priority filter
            if criteria.priority and memory.priority != criteria.priority:
                return False
            
            # Check tags filter
            if criteria.tags:
                if not any(tag in memory.tags for tag in criteria.tags):
                    return False
            
            # Check age
            if criteria.older_than_days is not None:
                age_threshold = datetime.utcnow() - timedelta(days=criteria.older_than_days)
                if memory.created_at > age_threshold:
                    return False
            
            # Check relevance
            if criteria.relevance_threshold is not None:
                if memory.relevance_score >= criteria.relevance_threshold:
                    return False
            
            # Check access count
            if criteria.max_access_count is not None:
                if memory.access_count <= criteria.max_access_count:
                    return False
            
            # All criteria matched
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluating forget criteria: {e}", exc_info=True)
            return False
    
    def filter_memories(
        self,
        memories: List[Memory],
        criteria: ForgetCriteria
    ) -> List[Memory]:
        """
        Filter memories that should be forgotten.
        
        Args:
            memories: List of memories to evaluate
            criteria: Forgetting criteria
            
        Returns:
            List of memories to forget
        """
        try:
            to_forget = [m for m in memories if self.should_forget(m, criteria)]
            
            self.logger.info(
                f"Identified {len(to_forget)} memories to forget out of {len(memories)}"
            )
            
            return to_forget
            
        except Exception as e:
            self.logger.error(f"Failed to filter memories: {e}", exc_info=True)
            return []
    
    def forget_expired(self, memories: List[Memory]) -> List[Memory]:
        """
        Get memories that have expired.
        
        Args:
            memories: List of memories to check
            
        Returns:
            List of expired memories
        """
        try:
            expired = [m for m in memories if m.is_expired()]
            
            if expired:
                self.logger.info(f"Found {len(expired)} expired memories")
            
            return expired
            
        except Exception as e:
            self.logger.error(f"Failed to find expired memories: {e}", exc_info=True)
            return []
    
    def forget_low_relevance(
        self,
        memories: List[Memory],
        threshold: float = 0.2,
        preserve_count: int = 0
    ) -> List[Memory]:
        """
        Get memories with low relevance scores.
        
        Args:
            memories: List of memories to evaluate
            threshold: Relevance threshold
            preserve_count: Number of memories to always preserve
            
        Returns:
            List of low relevance memories to forget
        """
        try:
            # Sort by relevance
            sorted_memories = sorted(memories, key=lambda m: m.relevance_score)
            
            # Keep at least preserve_count memories
            candidates = sorted_memories[preserve_count:]
            
            # Filter by threshold
            low_relevance = [m for m in candidates if m.relevance_score < threshold]
            
            if low_relevance:
                self.logger.info(
                    f"Found {len(low_relevance)} low relevance memories (threshold: {threshold})"
                )
            
            return low_relevance
            
        except Exception as e:
            self.logger.error(f"Failed to find low relevance memories: {e}", exc_info=True)
            return []
    
    def forget_old(
        self,
        memories: List[Memory],
        days: int = 30,
        memory_type: Optional[MemoryType] = None
    ) -> List[Memory]:
        """
        Get memories older than specified days.
        
        Args:
            memories: List of memories to evaluate
            days: Age threshold in days
            memory_type: Optional type filter
            
        Returns:
            List of old memories
        """
        try:
            age_threshold = datetime.utcnow() - timedelta(days=days)
            
            old_memories = [
                m for m in memories
                if m.created_at < age_threshold
                and (memory_type is None or m.memory_type == memory_type)
            ]
            
            if old_memories:
                self.logger.info(f"Found {len(old_memories)} memories older than {days} days")
            
            return old_memories
            
        except Exception as e:
            self.logger.error(f"Failed to find old memories: {e}", exc_info=True)
            return []
    
    def forget_least_accessed(
        self,
        memories: List[Memory],
        count: int = 10
    ) -> List[Memory]:
        """
        Get least accessed memories.
        
        Args:
            memories: List of memories to evaluate
            count: Number of memories to forget
            
        Returns:
            List of least accessed memories
        """
        try:
            # Sort by access count
            sorted_memories = sorted(memories, key=lambda m: m.access_count)
            
            # Return least accessed
            least_accessed = sorted_memories[:count]
            
            if least_accessed:
                self.logger.info(f"Identified {len(least_accessed)} least accessed memories")
            
            return least_accessed
            
        except Exception as e:
            self.logger.error(f"Failed to find least accessed memories: {e}", exc_info=True)
            return []
    
    def decay_relevance(
        self,
        memory: Memory,
        decay_rate: float = 0.01,
        min_relevance: float = 0.1
    ) -> float:
        """
        Apply time-based relevance decay to a memory.
        
        Args:
            memory: Memory to decay
            decay_rate: Rate of decay per day
            min_relevance: Minimum relevance score
            
        Returns:
            New relevance score
        """
        try:
            # Calculate days since creation
            days_old = (datetime.utcnow() - memory.created_at).days
            
            # Apply exponential decay
            decay_factor = (1 - decay_rate) ** days_old
            new_relevance = max(memory.relevance_score * decay_factor, min_relevance)
            
            self.logger.debug(
                f"Decayed relevance for memory {memory.id}: "
                f"{memory.relevance_score:.3f} -> {new_relevance:.3f}"
            )
            
            return new_relevance
            
        except Exception as e:
            self.logger.error(f"Failed to decay relevance: {e}", exc_info=True)
            return memory.relevance_score
    
    def apply_decay_to_memories(
        self,
        memories: List[Memory],
        decay_rate: float = 0.01,
        min_relevance: float = 0.1
    ) -> List[Memory]:
        """
        Apply relevance decay to multiple memories.
        
        Args:
            memories: List of memories
            decay_rate: Rate of decay per day
            min_relevance: Minimum relevance score
            
        Returns:
            List of memories with updated relevance
        """
        try:
            updated_memories = []
            
            for memory in memories:
                new_relevance = self.decay_relevance(memory, decay_rate, min_relevance)
                memory.relevance_score = new_relevance
                updated_memories.append(memory)
            
            self.logger.info(f"Applied decay to {len(memories)} memories")
            return updated_memories
            
        except Exception as e:
            self.logger.error(f"Failed to apply decay: {e}", exc_info=True)
            return memories
    
    def forget_by_policy(
        self,
        memories: List[Memory],
        policy: Callable[[Memory], bool]
    ) -> List[Memory]:
        """
        Forget memories based on custom policy function.
        
        Args:
            memories: List of memories to evaluate
            policy: Function that returns True if memory should be forgotten
            
        Returns:
            List of memories to forget
        """
        try:
            to_forget = [m for m in memories if policy(m)]
            
            self.logger.info(
                f"Custom policy identified {len(to_forget)} memories to forget"
            )
            
            return to_forget
            
        except Exception as e:
            self.logger.error(f"Failed to apply custom policy: {e}", exc_info=True)
            return []
    
    def consolidate_similar(
        self,
        memories: List[Memory],
        similarity_threshold: float = 0.9
    ) -> List[str]:
        """
        Identify similar memories that could be consolidated.
        
        Args:
            memories: List of memories to evaluate
            similarity_threshold: Threshold for considering memories similar
            
        Returns:
            List of memory IDs to potentially forget (keep one from each group)
        """
        try:
            # Group similar memories
            groups = []
            processed = set()
            
            for i, mem1 in enumerate(memories):
                if mem1.id in processed:
                    continue
                
                group = [mem1.id]
                processed.add(mem1.id)
                
                # Find similar memories
                for mem2 in memories[i + 1:]:
                    if mem2.id in processed:
                        continue
                    
                    # Check if embeddings exist
                    if mem1.embedding and mem2.embedding:
                        # Compute similarity (simplified)
                        import numpy as np
                        sim = np.dot(mem1.embedding, mem2.embedding)
                        
                        if sim >= similarity_threshold:
                            group.append(mem2.id)
                            processed.add(mem2.id)
                
                if len(group) > 1:
                    groups.append(group)
            
            # From each group, keep the most recent one
            to_forget = []
            for group in groups:
                group_memories = [m for m in memories if m.id in group]
                # Sort by creation time
                group_memories.sort(key=lambda m: m.created_at, reverse=True)
                # Mark all except the most recent for forgetting
                to_forget.extend([m.id for m in group_memories[1:]])
            
            if to_forget:
                self.logger.info(
                    f"Identified {len(to_forget)} similar memories for consolidation"
                )
            
            return to_forget
            
        except Exception as e:
            self.logger.error(f"Failed to consolidate similar memories: {e}", exc_info=True)
            return []

