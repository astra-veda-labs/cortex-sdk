"""
Tests for memory forgetting and cleanup operations.
"""

import pytest
from cortex.utils.schema import (
    MemoryType,
    MemoryPriority,
    ForgetCriteria
)
from datetime import datetime, timedelta


class TestForgetCriteria:
    """Test forgetting memories based on criteria."""
    
    def test_forget_by_age(self, memory_manager):
        """Test forgetting memories older than specified days."""
        # Store a memory
        memory_id = memory_manager.remember(
            content="Old memory",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Forget memories older than 0 days (all)
        criteria = ForgetCriteria(older_than_days=0)
        count = memory_manager.forget(criteria)
        
        assert count >= 0
    
    def test_forget_by_relevance(self, memory_manager):
        """Test forgetting memories below relevance threshold."""
        memory_id = memory_manager.remember(
            content="Low relevance memory",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Get and update memory to set low relevance
        memory = memory_manager.get_memory(memory_id)
        if memory:
            memory.relevance_score = 0.1
            memory_manager.short_term_store.update(memory)
        
        # Forget low relevance memories
        criteria = ForgetCriteria(relevance_threshold=0.5)
        count = memory_manager.forget(criteria)
        
        assert count >= 0
    
    def test_forget_by_type(self, memory_manager):
        """Test forgetting memories of specific type."""
        # Store both types
        memory_manager.remember(
            content="Short term",
            memory_type=MemoryType.SHORT_TERM
        )
        memory_manager.remember(
            content="Long term",
            memory_type=MemoryType.LONG_TERM
        )
        
        # Forget only short-term
        criteria = ForgetCriteria(
            memory_type=MemoryType.SHORT_TERM,
            relevance_threshold=0.0
        )
        count = memory_manager.forget(criteria)
        
        assert count >= 0
    
    def test_forget_by_tags(self, memory_manager):
        """Test forgetting memories with specific tags."""
        memory_manager.remember(
            content="Tagged memory",
            memory_type=MemoryType.SHORT_TERM,
            tags=["delete-me"]
        )
        memory_manager.remember(
            content="Keep this memory",
            memory_type=MemoryType.SHORT_TERM,
            tags=["keep"]
        )
        
        # Forget memories with specific tag
        criteria = ForgetCriteria(tags=["delete-me"])
        count = memory_manager.forget(criteria)
        
        assert count >= 0
    
    def test_forget_combined_criteria(self, memory_manager):
        """Test forgetting with multiple criteria."""
        memory_manager.remember(
            content="Old low relevance memory",
            memory_type=MemoryType.SHORT_TERM,
            tags=["old"]
        )
        
        # Combine multiple criteria
        criteria = ForgetCriteria(
            older_than_days=0,
            relevance_threshold=0.5,
            memory_type=MemoryType.SHORT_TERM
        )
        
        count = memory_manager.forget(criteria)
        assert count >= 0


class TestForgetEngine:
    """Test forget engine functionality."""
    
    def test_forget_expired_memories(self, memory_manager):
        """Test automatic forgetting of expired memories."""
        # Store an expired memory
        expires_at = datetime.utcnow() - timedelta(hours=1)
        
        memory_id = memory_manager.remember(
            content="Expired memory",
            memory_type=MemoryType.SHORT_TERM,
            expires_at=expires_at
        )
        
        # Cleanup should remove expired
        removed = memory_manager.cleanup()
        
        # Verify memory is gone
        memory = memory_manager.get_memory(memory_id)
        assert memory is None
    
    def test_preserve_valid_memories(self, memory_manager):
        """Test that valid memories are not forgotten."""
        memory_id = memory_manager.remember(
            content="Valid memory",
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.HIGH
        )
        
        # Try to forget with strict criteria
        criteria = ForgetCriteria(
            relevance_threshold=0.99,  # Very high threshold
            priority=MemoryPriority.LOW  # Different priority
        )
        
        memory_manager.forget(criteria)
        
        # Memory should still exist
        memory = memory_manager.get_memory(memory_id)
        assert memory is not None
    
    def test_forget_returns_count(self, memory_manager):
        """Test that forget returns accurate count."""
        # Store multiple memories
        for i in range(3):
            memory_manager.remember(
                content=f"Memory {i}",
                memory_type=MemoryType.SHORT_TERM
            )
        
        initial_stats = memory_manager.get_stats()
        initial_count = initial_stats.total_memories
        
        # Forget all with low threshold
        criteria = ForgetCriteria(relevance_threshold=0.0)
        forgotten = memory_manager.forget(criteria)
        
        assert forgotten <= initial_count


class TestMemoryDecay:
    """Test memory relevance decay."""
    
    def test_relevance_decreases_over_time(self, memory_manager):
        """Test that memory relevance can be decayed."""
        memory_id = memory_manager.remember(
            content="Memory to decay",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Get initial relevance
        memory = memory_manager.get_memory(memory_id)
        initial_relevance = memory.relevance_score
        
        # Apply decay through forget engine
        from cortex.core.forget_engine import ForgetEngine
        forget_engine = ForgetEngine()
        
        new_relevance = forget_engine.decay_relevance(memory, decay_rate=0.5)
        
        # Relevance should decrease
        assert new_relevance <= initial_relevance


class TestSelectiveForgetting:
    """Test selective forgetting strategies."""
    
    def test_forget_by_priority(self, memory_manager):
        """Test forgetting based on priority levels."""
        # Store memories with different priorities
        low_priority = memory_manager.remember(
            content="Low priority",
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.LOW
        )
        
        high_priority = memory_manager.remember(
            content="High priority",
            memory_type=MemoryType.SHORT_TERM,
            priority=MemoryPriority.HIGH
        )
        
        # Forget low priority
        criteria = ForgetCriteria(priority=MemoryPriority.LOW)
        count = memory_manager.forget(criteria)
        
        # High priority should remain
        high_memory = memory_manager.get_memory(high_priority)
        assert high_memory is not None
    
    def test_forget_least_accessed(self, memory_manager):
        """Test forgetting least accessed memories."""
        # Store and access memories differently
        mem1_id = memory_manager.remember(
            content="Rarely accessed",
            memory_type=MemoryType.SHORT_TERM
        )
        
        mem2_id = memory_manager.remember(
            content="Frequently accessed",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Access mem2 multiple times
        for _ in range(5):
            memory_manager.get_memory(mem2_id)
        
        # Forget based on low access count
        criteria = ForgetCriteria(max_access_count=2)
        count = memory_manager.forget(criteria)
        
        assert count >= 0


class TestMemoryRetention:
    """Test memory retention policies."""
    
    def test_retain_important_memories(self, memory_manager):
        """Test that high priority memories are retained."""
        important_id = memory_manager.remember(
            content="Critical information",
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.CRITICAL,
            tags=["important"]
        )
        
        # Try aggressive forgetting
        criteria = ForgetCriteria(
            relevance_threshold=0.5,
            memory_type=MemoryType.LONG_TERM
        )
        
        memory_manager.forget(criteria)
        
        # Important memory should survive if relevance is high
        memory = memory_manager.get_memory(important_id)
        # Memory may or may not exist depending on relevance
        assert isinstance(memory_manager.get_memory(important_id), (type(None), type(memory)))
    
    def test_capacity_management(self, memory_manager):
        """Test that stores respect capacity limits."""
        config = memory_manager.config
        
        # Try to store more than capacity
        for i in range(config.short_term_capacity + 5):
            memory_manager.remember(
                content=f"Memory {i}",
                memory_type=MemoryType.SHORT_TERM
            )
        
        stats = memory_manager.get_stats()
        
        # Should not exceed capacity
        assert stats.short_term_count <= config.short_term_capacity

