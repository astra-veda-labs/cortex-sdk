"""
High-level API for memory operations.
Provides user-friendly interfaces for storing and retrieving memories.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from cortex.utils.schema import (
    Memory as MemorySchema,
    MemorySearchResult,
    MemoryType,
    MemoryPriority,
    FileMemory,
    MemorySummary,
    ForgetCriteria,
    MemoryStats
)
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class Memory:
    """
    High-level API for memory operations.
    Wraps the MemoryManager with a simpler interface.
    """
    
    def __init__(self, memory_manager):
        """
        Initialize Memory API.
        
        Args:
            memory_manager: Instance of MemoryManager
        """
        self.manager = memory_manager
        self.logger = get_logger(__name__)
    
    def store(
        self,
        content: str,
        memory_type: Union[str, MemoryType] = MemoryType.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: Union[str, MemoryPriority] = MemoryPriority.MEDIUM,
        ttl_days: Optional[int] = None
    ) -> str:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory (short_term, long_term, file)
            metadata: Additional metadata
            tags: Memory tags
            priority: Memory priority
            ttl_days: Time-to-live in days
            
        Returns:
            Memory ID
        """
        try:
            # Convert string enums if needed
            if isinstance(memory_type, str):
                memory_type = MemoryType(memory_type)
            if isinstance(priority, str):
                priority = MemoryPriority(priority)
            
            # Calculate expiration
            expires_at = None
            if ttl_days:
                expires_at = datetime.utcnow() + timedelta(days=ttl_days)
            
            memory_id = self.manager.remember(
                content=content,
                memory_type=memory_type,
                metadata=metadata or {},
                tags=tags or [],
                priority=priority,
                expires_at=expires_at
            )
            
            self.logger.info(f"Stored memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}", exc_info=True)
            raise
    
    def retrieve(
        self,
        query: str,
        memory_type: Optional[Union[str, MemoryType]] = None,
        limit: int = 10,
        min_similarity: float = 0.5,
        tags: Optional[List[str]] = None
    ) -> List[MemorySearchResult]:
        """
        Retrieve memories matching a query.
        
        Args:
            query: Search query
            memory_type: Filter by memory type
            limit: Maximum results
            min_similarity: Minimum similarity score
            tags: Filter by tags
            
        Returns:
            List of search results
        """
        try:
            if isinstance(memory_type, str):
                memory_type = MemoryType(memory_type)
            
            results = self.manager.recall(
                query=query,
                memory_type=memory_type,
                limit=limit,
                min_similarity=min_similarity,
                tags=tags
            )
            
            self.logger.info(f"Retrieved {len(results)} memories for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            raise
    
    def get_by_id(self, memory_id: str) -> Optional[MemorySchema]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object or None
        """
        try:
            memory = self.manager.get_memory(memory_id)
            if memory:
                self.logger.debug(f"Retrieved memory: {memory_id}")
            else:
                self.logger.warning(f"Memory not found: {memory_id}")
            return memory
            
        except Exception as e:
            self.logger.error(f"Failed to get memory: {e}", exc_info=True)
            raise
    
    def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[Union[str, MemoryPriority]] = None
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory identifier
            content: New content
            metadata: New metadata
            tags: New tags
            priority: New priority
            
        Returns:
            True if updated successfully
        """
        try:
            if isinstance(priority, str):
                priority = MemoryPriority(priority)
            
            success = self.manager.update_memory(
                memory_id=memory_id,
                content=content,
                metadata=metadata,
                tags=tags,
                priority=priority
            )
            
            if success:
                self.logger.info(f"Updated memory: {memory_id}")
            else:
                self.logger.warning(f"Failed to update memory: {memory_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update memory: {e}", exc_info=True)
            raise
    
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            success = self.manager.delete_memory(memory_id)
            
            if success:
                self.logger.info(f"Deleted memory: {memory_id}")
            else:
                self.logger.warning(f"Failed to delete memory: {memory_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete memory: {e}", exc_info=True)
            raise
    
    def summarize(
        self,
        topic: Optional[str] = None,
        memory_type: Optional[Union[str, MemoryType]] = None,
        tags: Optional[List[str]] = None,
        time_range: Optional[tuple] = None
    ) -> MemorySummary:
        """
        Get a summary of memories.
        
        Args:
            topic: Optional topic filter
            memory_type: Filter by memory type
            tags: Filter by tags
            time_range: Tuple of (start_date, end_date)
            
        Returns:
            Memory summary
        """
        try:
            if isinstance(memory_type, str):
                memory_type = MemoryType(memory_type)
            
            summary = self.manager.summarize(
                topic=topic,
                memory_type=memory_type,
                tags=tags,
                time_range=time_range
            )
            
            self.logger.info(f"Generated summary of {summary.num_memories} memories")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}", exc_info=True)
            raise
    
    def forget(
        self,
        older_than_days: Optional[int] = None,
        relevance_threshold: Optional[float] = None,
        memory_type: Optional[Union[str, MemoryType]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Forget (delete) memories based on criteria.
        
        Args:
            older_than_days: Delete memories older than N days
            relevance_threshold: Delete memories below relevance score
            memory_type: Filter by memory type
            tags: Filter by tags
            
        Returns:
            Number of memories deleted
        """
        try:
            if isinstance(memory_type, str):
                memory_type = MemoryType(memory_type)
            
            criteria = ForgetCriteria(
                older_than_days=older_than_days,
                relevance_threshold=relevance_threshold,
                memory_type=memory_type,
                tags=tags
            )
            
            count = self.manager.forget(criteria)
            self.logger.info(f"Forgot {count} memories")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to forget memories: {e}", exc_info=True)
            raise
    
    def get_stats(self) -> MemoryStats:
        """
        Get statistics about stored memories.
        
        Returns:
            Memory statistics
        """
        try:
            stats = self.manager.get_stats()
            self.logger.debug("Retrieved memory statistics")
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}", exc_info=True)
            raise


class MemorySearch:
    """Helper class for building complex memory searches."""
    
    def __init__(self, memory_api: Memory):
        """
        Initialize MemorySearch.
        
        Args:
            memory_api: Memory API instance
        """
        self.memory_api = memory_api
        self.query_text = ""
        self.filters = {}
        self.limit_val = 10
        self.min_sim = 0.5
    
    def query(self, text: str) -> "MemorySearch":
        """Set search query."""
        self.query_text = text
        return self
    
    def filter_type(self, memory_type: Union[str, MemoryType]) -> "MemorySearch":
        """Filter by memory type."""
        self.filters['memory_type'] = memory_type
        return self
    
    def filter_tags(self, tags: List[str]) -> "MemorySearch":
        """Filter by tags."""
        self.filters['tags'] = tags
        return self
    
    def limit(self, n: int) -> "MemorySearch":
        """Set result limit."""
        self.limit_val = n
        return self
    
    def min_similarity(self, score: float) -> "MemorySearch":
        """Set minimum similarity."""
        self.min_sim = score
        return self
    
    def execute(self) -> List[MemorySearchResult]:
        """Execute the search."""
        return self.memory_api.retrieve(
            query=self.query_text,
            memory_type=self.filters.get('memory_type'),
            limit=self.limit_val,
            min_similarity=self.min_sim,
            tags=self.filters.get('tags')
        )

