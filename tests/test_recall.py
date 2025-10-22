"""
Tests for memory recall and search operations.
"""

import pytest
from cortex.utils.schema import MemoryType, MemoryPriority


class TestMemoryRecall:
    """Test memory recall/search operations."""
    
    def test_recall_simple_query(self, memory_manager):
        """Test basic recall with a simple query."""
        # Store some memories
        memory_manager.remember(
            content="Python is a programming language",
            memory_type=MemoryType.SHORT_TERM,
            tags=["python", "programming"]
        )
        memory_manager.remember(
            content="Machine learning uses algorithms",
            memory_type=MemoryType.SHORT_TERM,
            tags=["ml", "ai"]
        )
        
        # Recall memories
        results = memory_manager.recall(
            query="programming language",
            limit=5
        )
        
        assert len(results) > 0
        assert results[0].similarity > 0
    
    def test_recall_with_limit(self, memory_manager):
        """Test recall with result limit."""
        # Store multiple memories
        for i in range(5):
            memory_manager.remember(
                content=f"Memory number {i} about testing",
                memory_type=MemoryType.SHORT_TERM
            )
        
        # Recall with limit
        results = memory_manager.recall(
            query="testing",
            limit=3
        )
        
        assert len(results) <= 3
    
    def test_recall_with_similarity_threshold(self, memory_manager):
        """Test recall with minimum similarity threshold."""
        memory_manager.remember(
            content="Deep learning neural networks",
            memory_type=MemoryType.SHORT_TERM
        )
        memory_manager.remember(
            content="Cooking pasta recipes",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Query about neural networks
        results = memory_manager.recall(
            query="artificial intelligence and neural networks",
            min_similarity=0.3
        )
        
        # All results should meet threshold
        for result in results:
            assert result.similarity >= 0.3
    
    def test_recall_by_memory_type(self, memory_manager):
        """Test recall filtered by memory type."""
        # Store in different types
        memory_manager.remember(
            content="Short term information",
            memory_type=MemoryType.SHORT_TERM,
            tags=["short"]
        )
        memory_manager.remember(
            content="Long term knowledge",
            memory_type=MemoryType.LONG_TERM,
            tags=["long"]
        )
        
        # Recall only long-term
        results = memory_manager.recall(
            query="information knowledge",
            memory_type=MemoryType.LONG_TERM
        )
        
        for result in results:
            assert result.memory.memory_type == MemoryType.LONG_TERM
    
    def test_recall_with_tags(self, memory_manager):
        """Test recall filtered by tags."""
        memory_manager.remember(
            content="Python programming tutorial",
            memory_type=MemoryType.SHORT_TERM,
            tags=["python", "tutorial"]
        )
        memory_manager.remember(
            content="JavaScript web development",
            memory_type=MemoryType.SHORT_TERM,
            tags=["javascript", "web"]
        )
        
        # Recall with tag filter
        results = memory_manager.recall(
            query="programming",
            tags=["python"]
        )
        
        # Should only return memories with python tag
        for result in results:
            assert "python" in result.memory.tags
    
    def test_recall_ranking(self, memory_manager):
        """Test that recall results are properly ranked."""
        memory_manager.remember(
            content="Python is great for machine learning",
            memory_type=MemoryType.SHORT_TERM
        )
        memory_manager.remember(
            content="Machine learning requires data",
            memory_type=MemoryType.SHORT_TERM
        )
        
        results = memory_manager.recall(
            query="machine learning",
            limit=5
        )
        
        # Check ranking order
        for i in range(len(results) - 1):
            assert results[i].similarity >= results[i + 1].similarity
            assert results[i].rank == i + 1
    
    def test_recall_empty_query(self, memory_manager):
        """Test recall with empty query."""
        memory_manager.remember(
            content="Some content",
            memory_type=MemoryType.SHORT_TERM
        )
        
        results = memory_manager.recall(query="")
        
        # Should handle gracefully
        assert isinstance(results, list)
    
    def test_recall_no_matches(self, memory_manager):
        """Test recall when no memories match."""
        memory_manager.remember(
            content="Python programming",
            memory_type=MemoryType.SHORT_TERM
        )
        
        results = memory_manager.recall(
            query="completely unrelated topic xyz123",
            min_similarity=0.9  # Very high threshold
        )
        
        # May return empty list or low similarity results
        assert isinstance(results, list)


class TestSemanticSearch:
    """Test semantic search capabilities."""
    
    def test_semantic_similarity(self, memory_manager):
        """Test that semantically similar queries return related memories."""
        memory_manager.remember(
            content="Dogs are loyal pets that love to play fetch",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Query with similar meaning but different words
        results = memory_manager.recall(
            query="canines are faithful companions",
            limit=1
        )
        
        assert len(results) > 0
        # Should find the dog-related memory
        assert "dog" in results[0].memory.content.lower() or "pet" in results[0].memory.content.lower()
    
    def test_context_understanding(self, memory_manager):
        """Test understanding of context in queries."""
        memory_manager.remember(
            content="The capital of France is Paris",
            memory_type=MemoryType.LONG_TERM,
            tags=["geography", "france"]
        )
        memory_manager.remember(
            content="Python list comprehensions are powerful",
            memory_type=MemoryType.LONG_TERM,
            tags=["programming", "python"]
        )
        
        # Query about geography
        results = memory_manager.recall(
            query="What is the capital city of France?",
            limit=1
        )
        
        assert len(results) > 0
        assert "Paris" in results[0].memory.content or "France" in results[0].memory.content


class TestRecallPerformance:
    """Test recall performance characteristics."""
    
    def test_recall_with_many_memories(self, memory_manager):
        """Test recall performance with many stored memories."""
        # Store many memories
        for i in range(20):
            memory_manager.remember(
                content=f"Document number {i} about various topics",
                memory_type=MemoryType.SHORT_TERM,
                tags=[f"tag{i}"]
            )
        
        # Recall should still work efficiently
        results = memory_manager.recall(
            query="document topics",
            limit=10
        )
        
        assert len(results) <= 10
        assert len(results) > 0
    
    def test_recall_consistency(self, memory_manager):
        """Test that recall returns consistent results."""
        memory_id = memory_manager.remember(
            content="Consistent memory content",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # Query multiple times
        results1 = memory_manager.recall(query="consistent memory", limit=1)
        results2 = memory_manager.recall(query="consistent memory", limit=1)
        
        # Should return same memory
        if len(results1) > 0 and len(results2) > 0:
            assert results1[0].memory.id == results2[0].memory.id

