"""
Tests for core memory operations.
"""

import pytest
from cortex.utils.schema import MemoryType, MemoryPriority, ForgetCriteria
from datetime import datetime, timedelta


class TestMemoryStorage:
    """Test memory storage operations."""
    
    def test_remember_short_term(self, memory_manager, sample_content):
        """Test storing a short-term memory."""
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            tags=["test"],
            priority=MemoryPriority.MEDIUM
        )
        
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0
    
    def test_remember_long_term(self, memory_manager, sample_content):
        """Test storing a long-term memory."""
        memory_id = memory_manager.remember(
            content=sample_content["medium"],
            memory_type=MemoryType.LONG_TERM,
            tags=["test", "important"],
            priority=MemoryPriority.HIGH
        )
        
        assert memory_id is not None
        memory = memory_manager.get_memory(memory_id)
        assert memory is not None
        assert memory.content == sample_content["medium"]
        assert memory.memory_type == MemoryType.LONG_TERM
    
    def test_remember_with_metadata(self, memory_manager, sample_content):
        """Test storing memory with metadata."""
        metadata = {"source": "test", "user": "tester"}
        
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            metadata=metadata,
            tags=["meta"]
        )
        
        memory = memory_manager.get_memory(memory_id)
        assert memory.metadata == metadata
    
    def test_get_memory(self, memory_manager, sample_content):
        """Test retrieving a memory by ID."""
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM
        )
        
        memory = memory_manager.get_memory(memory_id)
        assert memory is not None
        assert memory.id == memory_id
        assert memory.content == sample_content["short"]
    
    def test_get_nonexistent_memory(self, memory_manager):
        """Test retrieving a non-existent memory."""
        memory = memory_manager.get_memory("nonexistent-id")
        assert memory is None
    
    def test_update_memory(self, memory_manager, sample_content):
        """Test updating an existing memory."""
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            tags=["original"]
        )
        
        # Update the memory
        success = memory_manager.update_memory(
            memory_id=memory_id,
            content=sample_content["medium"],
            tags=["updated"]
        )
        
        assert success is True
        
        # Verify update
        memory = memory_manager.get_memory(memory_id)
        assert memory.content == sample_content["medium"]
        assert "updated" in memory.tags
    
    def test_delete_memory(self, memory_manager, sample_content):
        """Test deleting a memory."""
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Delete the memory
        success = memory_manager.delete_memory(memory_id)
        assert success is True
        
        # Verify deletion
        memory = memory_manager.get_memory(memory_id)
        assert memory is None
    
    def test_memory_with_expiration(self, memory_manager, sample_content):
        """Test memory with expiration time."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            expires_at=expires_at
        )
        
        memory = memory_manager.get_memory(memory_id)
        assert memory.expires_at is not None
        assert memory.expires_at == expires_at
        assert not memory.is_expired()


class TestMemoryStats:
    """Test memory statistics."""
    
    def test_get_stats(self, memory_manager):
        """Test getting memory statistics."""
        stats = memory_manager.get_stats()
        
        assert stats is not None
        assert stats.total_memories == 0
        assert stats.short_term_count == 0
        assert stats.long_term_count == 0
    
    def test_stats_after_storing(self, memory_manager, sample_content):
        """Test statistics after storing memories."""
        # Store some memories
        memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM
        )
        memory_manager.remember(
            content=sample_content["medium"],
            memory_type=MemoryType.LONG_TERM
        )
        
        stats = memory_manager.get_stats()
        assert stats.total_memories == 2
        assert stats.short_term_count == 1
        assert stats.long_term_count == 1


class TestMemoryCleanup:
    """Test memory cleanup operations."""
    
    def test_cleanup_no_expired(self, memory_manager, sample_content):
        """Test cleanup with no expired memories."""
        memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM
        )
        
        removed = memory_manager.cleanup()
        assert removed == 0
    
    def test_cleanup_expired_memories(self, memory_manager, sample_content):
        """Test cleanup of expired memories."""
        # Store a memory that's already expired
        expires_at = datetime.utcnow() - timedelta(hours=1)
        
        memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            expires_at=expires_at
        )
        
        removed = memory_manager.cleanup()
        assert removed == 1


class TestMemoryPriority:
    """Test memory priority handling."""
    
    def test_store_different_priorities(self, memory_manager, sample_content):
        """Test storing memories with different priorities."""
        priorities = [
            MemoryPriority.LOW,
            MemoryPriority.MEDIUM,
            MemoryPriority.HIGH,
            MemoryPriority.CRITICAL
        ]
        
        for priority in priorities:
            memory_id = memory_manager.remember(
                content=sample_content["short"],
                memory_type=MemoryType.SHORT_TERM,
                priority=priority
            )
            
            memory = memory_manager.get_memory(memory_id)
            assert memory.priority == priority


class TestMemoryTags:
    """Test memory tagging."""
    
    def test_store_with_tags(self, memory_manager, sample_content):
        """Test storing memory with tags."""
        tags = ["important", "work", "project-a"]
        
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            tags=tags
        )
        
        memory = memory_manager.get_memory(memory_id)
        assert set(memory.tags) == set(tags)
    
    def test_update_tags(self, memory_manager, sample_content):
        """Test updating memory tags."""
        memory_id = memory_manager.remember(
            content=sample_content["short"],
            memory_type=MemoryType.SHORT_TERM,
            tags=["old-tag"]
        )
        
        new_tags = ["new-tag", "updated"]
        memory_manager.update_memory(
            memory_id=memory_id,
            tags=new_tags
        )
        
        memory = memory_manager.get_memory(memory_id)
        assert set(memory.tags) == set(new_tags)

