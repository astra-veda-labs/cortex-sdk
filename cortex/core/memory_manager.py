"""
Memory Manager - Main orchestrator for Cortex SDK.
Coordinates all memory operations across stores and engines.
"""

import uuid
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from cortex.core.short_term_store import ShortTermStore
from cortex.core.long_term_store import LongTermStore
from cortex.core.file_store import FileStore
from cortex.core.embedding_engine import EmbeddingEngine, CachedEmbeddingEngine
from cortex.core.summarizer import Summarizer
from cortex.core.forget_engine import ForgetEngine
from cortex.api.config import MemoryConfig
from cortex.utils.schema import (
    Memory,
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


class MemoryManager:
    """
    Main memory management system that coordinates all operations.
    Provides high-level interface for memory operations.
    """
    
    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        backend: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Memory Manager.
        
        Args:
            config: Memory configuration
            backend: Backend type (overrides config)
            **kwargs: Additional backend-specific parameters
        """
        # Setup configuration
        self.config = config or MemoryConfig()
        if backend:
            self.config.backend = backend
        
        # Update config with kwargs
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.logger = get_logger(__name__)
        self.logger.info(f"Initializing MemoryManager with backend: {self.config.backend}")
        
        # Initialize storage systems
        self.short_term_store = ShortTermStore(capacity=self.config.short_term_capacity)
        self.long_term_store = LongTermStore(capacity=self.config.long_term_capacity)
        self.file_store = FileStore(capacity=self.config.file_storage_capacity)
        
        # Initialize engines
        if self.config.enable_caching:
            self.embedding_engine = CachedEmbeddingEngine(
                model_name=self.config.embedding_model,
                use_gpu=self.config.use_gpu,
                batch_size=self.config.batch_size
            )
        else:
            self.embedding_engine = EmbeddingEngine(
                model_name=self.config.embedding_model,
                use_gpu=self.config.use_gpu,
                batch_size=self.config.batch_size
            )
        
        self.summarizer = Summarizer(
            model_name=self.config.summarization_model,
            use_gpu=self.config.use_gpu
        )
        
        self.forget_engine = ForgetEngine()
        
        # Initialize backend plugin if not local
        self.backend_plugin = None
        if self.config.backend != "local":
            self._init_backend_plugin()
        
        self.logger.info("MemoryManager initialized successfully")
    
    def _init_backend_plugin(self):
        """Initialize backend plugin based on configuration."""
        try:
            if self.config.backend == "sqlite":
                from cortex.plugins.sqlite_plugin import SQLitePlugin
                self.backend_plugin = SQLitePlugin(
                    db_path=self.config.db_path,
                    embedding_dim=self.config.embedding_dimension
                )
            elif self.config.backend == "pgvector":
                from cortex.plugins.pgvector_plugin import PGVectorPlugin
                self.backend_plugin = PGVectorPlugin(
                    connection_string=self.config.connection_string,
                    embedding_dim=self.config.embedding_dimension
                )
            else:
                self.logger.warning(f"Unknown backend: {self.config.backend}, using local")
        except ImportError as e:
            self.logger.error(f"Failed to load backend plugin: {e}")
            self.logger.warning("Falling back to local backend")
    
    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory storage
            metadata: Additional metadata
            tags: Memory tags
            priority: Memory priority
            expires_at: Expiration timestamp
            
        Returns:
            Memory ID
        """
        try:
            # Generate memory ID
            memory_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self.embedding_engine.encode(content)
            
            # Set expiration if not provided
            if expires_at is None and memory_type == MemoryType.SHORT_TERM:
                if self.config.short_term_ttl_days:
                    expires_at = datetime.utcnow() + timedelta(
                        days=self.config.short_term_ttl_days
                    )
            
            # Create memory object
            memory = Memory(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                embedding=embedding.tolist(),
                metadata=metadata or {},
                tags=tags or [],
                priority=priority,
                expires_at=expires_at
            )
            
            # Store in appropriate store
            if memory_type == MemoryType.SHORT_TERM:
                success = self.short_term_store.add(memory)
            elif memory_type == MemoryType.LONG_TERM:
                success = self.long_term_store.add(memory)
            else:
                success = False
            
            # Also store in backend plugin if available
            if self.backend_plugin:
                self.backend_plugin.store_memory(memory)
            
            if success:
                self.logger.info(f"Stored memory {memory_id} in {memory_type}")
                return memory_id
            else:
                raise Exception("Failed to store memory in store")
            
        except Exception as e:
            self.logger.error(f"Failed to remember: {e}", exc_info=True)
            raise
    
    def recall(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_similarity: float = 0.5,
        tags: Optional[List[str]] = None
    ) -> List[MemorySearchResult]:
        """
        Recall memories matching a query.
        
        Args:
            query: Search query
            memory_type: Filter by memory type
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            tags: Filter by tags
            
        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_engine.encode(query)
            
            # Get candidates from stores
            candidates = []
            
            if memory_type is None or memory_type == MemoryType.SHORT_TERM:
                candidates.extend(self.short_term_store.search(tags=tags))
            
            if memory_type is None or memory_type == MemoryType.LONG_TERM:
                candidates.extend(self.long_term_store.search(tags=tags))
            
            # Check backend plugin
            if self.backend_plugin:
                plugin_results = self.backend_plugin.search_memories(
                    query_embedding=query_embedding.tolist(),
                    limit=limit,
                    min_similarity=min_similarity
                )
                candidates.extend(plugin_results)
            
            # Filter candidates with embeddings
            candidates_with_emb = [c for c in candidates if c.embedding is not None]
            
            if not candidates_with_emb:
                return []
            
            # Compute similarities
            embeddings = [c.embedding for c in candidates_with_emb]
            similarities = self.embedding_engine.compute_similarities(
                query_embedding, embeddings
            )
            
            # Create results
            results = []
            for i, (candidate, similarity) in enumerate(zip(candidates_with_emb, similarities)):
                if similarity >= min_similarity:
                    result = MemorySearchResult(
                        memory=candidate,
                        similarity=similarity,
                        rank=0  # Will be set after sorting
                    )
                    results.append(result)
            
            # Sort by similarity
            results.sort(key=lambda x: x.similarity, reverse=True)
            
            # Set ranks
            for rank, result in enumerate(results, 1):
                result.rank = rank
            
            # Limit results
            results = results[:limit]
            
            self.logger.info(f"Recalled {len(results)} memories for query: '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to recall: {e}", exc_info=True)
            return []
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory object or None
        """
        try:
            # Try short-term store
            memory = self.short_term_store.get(memory_id)
            if memory:
                return memory
            
            # Try long-term store
            memory = self.long_term_store.get(memory_id)
            if memory:
                return memory
            
            # Try backend plugin
            if self.backend_plugin:
                memory = self.backend_plugin.get_memory(memory_id)
                if memory:
                    return memory
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get memory: {e}", exc_info=True)
            return None
    
    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[MemoryPriority] = None
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
            # Get existing memory
            memory = self.get_memory(memory_id)
            if not memory:
                return False
            
            # Update fields
            if content is not None:
                memory.content = content
                # Regenerate embedding
                memory.embedding = self.embedding_engine.encode(content).tolist()
            
            if metadata is not None:
                memory.metadata.update(metadata)
            
            if tags is not None:
                memory.tags = tags
            
            if priority is not None:
                memory.priority = priority
            
            memory.updated_at = datetime.utcnow()
            
            # Update in appropriate store
            if memory.memory_type == MemoryType.SHORT_TERM:
                success = self.short_term_store.update(memory)
            elif memory.memory_type == MemoryType.LONG_TERM:
                success = self.long_term_store.update(memory)
            else:
                success = False
            
            # Update in backend plugin
            if self.backend_plugin:
                self.backend_plugin.update_memory(memory)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update memory: {e}", exc_info=True)
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            # Try removing from all stores
            success = False
            
            if self.short_term_store.remove(memory_id):
                success = True
            
            if self.long_term_store.remove(memory_id):
                success = True
            
            # Remove from backend plugin
            if self.backend_plugin:
                self.backend_plugin.delete_memory(memory_id)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete memory: {e}", exc_info=True)
            return False
    
    def summarize(
        self,
        topic: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        time_range: Optional[tuple] = None
    ) -> MemorySummary:
        """
        Generate a summary of memories.
        
        Args:
            topic: Optional topic filter
            memory_type: Filter by memory type
            tags: Filter by tags
            time_range: Tuple of (start_date, end_date)
            
        Returns:
            Memory summary
        """
        try:
            # Get candidate memories
            candidates = []
            
            if memory_type is None or memory_type == MemoryType.SHORT_TERM:
                candidates.extend(self.short_term_store.search(tags=tags))
            
            if memory_type is None or memory_type == MemoryType.LONG_TERM:
                candidates.extend(self.long_term_store.search(tags=tags))
            
            # Filter by time range
            if time_range:
                start_date, end_date = time_range
                candidates = [
                    m for m in candidates
                    if start_date <= m.created_at <= end_date
                ]
            
            # Generate summary
            if topic:
                summary = self.summarizer.summarize_by_topic(candidates, topic)
                return MemorySummary(
                    summary_text=summary,
                    num_memories=len(candidates),
                    topics=[topic],
                    time_range={'start': time_range[0], 'end': time_range[1]} if time_range else None
                )
            else:
                return self.summarizer.summarize_memories(candidates)
            
        except Exception as e:
            self.logger.error(f"Failed to summarize: {e}", exc_info=True)
            return MemorySummary(
                summary_text="Error generating summary",
                num_memories=0,
                topics=[],
                time_range=None
            )
    
    def forget(self, criteria: ForgetCriteria) -> int:
        """
        Forget memories based on criteria.
        
        Args:
            criteria: Forgetting criteria
            
        Returns:
            Number of memories forgotten
        """
        try:
            # Get all memories
            all_memories = []
            all_memories.extend(self.short_term_store.get_all())
            all_memories.extend(self.long_term_store.get_all())
            
            # Filter memories to forget
            to_forget = self.forget_engine.filter_memories(all_memories, criteria)
            
            # Delete memories
            count = 0
            for memory in to_forget:
                if self.delete_memory(memory.id):
                    count += 1
            
            self.logger.info(f"Forgot {count} memories")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to forget: {e}", exc_info=True)
            return 0
    
    def store_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        generate_summary: bool = True
    ) -> Optional[str]:
        """
        Store a file with metadata.
        
        Args:
            file_path: Path to the file
            metadata: Additional metadata
            tags: File tags
            generate_summary: Whether to generate content summary
            
        Returns:
            File ID or None
        """
        try:
            # TODO: Extract text content from file for summary
            content_summary = None
            if generate_summary:
                # Placeholder for file content extraction
                content_summary = f"File: {file_path}"
            
            file_id = self.file_store.add(
                file_path=file_path,
                metadata=metadata,
                tags=tags,
                content_summary=content_summary
            )
            
            return file_id
            
        except Exception as e:
            self.logger.error(f"Failed to store file: {e}", exc_info=True)
            return None
    
    def recall_files(
        self,
        query: Optional[str] = None,
        file_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[FileMemory]:
        """
        Retrieve files matching criteria.
        
        Args:
            query: Optional search query
            file_type: Filter by file type
            tags: Filter by tags
            
        Returns:
            List of file memories
        """
        try:
            results = self.file_store.search(
                file_type=file_type,
                tags=tags
            )
            
            # TODO: Add semantic search support for files
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to recall files: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> MemoryStats:
        """
        Get statistics about memory storage.
        
        Returns:
            Memory statistics
        """
        try:
            st_stats = self.short_term_store.get_stats()
            lt_stats = self.long_term_store.get_stats()
            f_stats = self.file_store.get_stats()
            
            stats = MemoryStats(
                total_memories=st_stats['total_memories'] + lt_stats['total_memories'],
                short_term_count=st_stats['total_memories'],
                long_term_count=lt_stats['total_memories'],
                file_count=f_stats['total_files'],
                total_size_bytes=f_stats.get('total_size_bytes', 0),
                oldest_memory=min(
                    [st_stats.get('oldest_memory'), lt_stats.get('oldest_memory')],
                    default=None,
                    key=lambda x: x if x else datetime.max
                ) if st_stats.get('oldest_memory') or lt_stats.get('oldest_memory') else None,
                newest_memory=max(
                    [st_stats.get('newest_memory'), lt_stats.get('newest_memory')],
                    default=None,
                    key=lambda x: x if x else datetime.min
                ) if st_stats.get('newest_memory') or lt_stats.get('newest_memory') else None,
                avg_relevance=(
                    st_stats.get('avg_relevance', 0) * st_stats['total_memories'] +
                    lt_stats.get('avg_relevance', 0) * lt_stats['total_memories']
                ) / (st_stats['total_memories'] + lt_stats['total_memories'])
                if (st_stats['total_memories'] + lt_stats['total_memories']) > 0 else 0.0
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}", exc_info=True)
            return MemoryStats()
    
    def cleanup(self):
        """Perform cleanup operations (remove expired memories, etc.)"""
        try:
            # Remove expired memories
            st_removed = self.short_term_store.remove_expired()
            lt_removed = self.long_term_store.remove_expired()
            
            total_removed = st_removed + lt_removed
            
            if total_removed > 0:
                self.logger.info(f"Cleanup removed {total_removed} expired memories")
            
            return total_removed
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}", exc_info=True)
            return 0

