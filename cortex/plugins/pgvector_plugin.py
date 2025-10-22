"""
PostgreSQL pgvector plugin for Cortex SDK.
Provides persistent storage backend using PostgreSQL with pgvector extension.
"""

from typing import List, Optional
import json
from cortex.utils.schema import Memory
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class PGVectorPlugin:
    """
    PostgreSQL storage plugin with pgvector extension for vector similarity.
    Provides scalable persistent storage with native vector operations.
    """
    
    def __init__(self, connection_string: str, embedding_dim: int = 384):
        """
        Initialize pgvector plugin.
        
        Args:
            connection_string: PostgreSQL connection string
            embedding_dim: Dimension of embedding vectors
        """
        self.connection_string = connection_string
        self.embedding_dim = embedding_dim
        self.logger = get_logger(__name__)
        
        try:
            import psycopg2
            from psycopg2.extras import Json
            self.psycopg2 = psycopg2
            self.Json = Json
        except ImportError:
            self.logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        
        # Initialize database
        self._init_database()
        
        self.logger.info("Initialized PGVectorPlugin")
    
    def _init_database(self):
        """Initialize database tables and extensions."""
        try:
            conn = self.psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Enable pgvector extension
            cursor.execute('CREATE EXTENSION IF NOT EXISTS vector')
            
            # Create memories table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    embedding vector({self.embedding_dim}),
                    metadata JSONB,
                    priority TEXT,
                    relevance_score REAL,
                    access_count INTEGER,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    last_accessed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    tags TEXT[]
                )
            ''')
            
            # Create indexes
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)'
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_tags ON memories USING GIN(tags)'
            )
            
            # Create vector index for similarity search
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_embedding ON memories '
                'USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.debug("PostgreSQL database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    def _get_connection(self):
        """Get database connection."""
        return self.psycopg2.connect(self.connection_string)
    
    def store_memory(self, memory: Memory) -> bool:
        """
        Store a memory in database.
        
        Args:
            memory: Memory to store
            
        Returns:
            True if stored successfully
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO memories
                (id, content, memory_type, embedding, metadata, priority,
                 relevance_score, access_count, created_at, updated_at,
                 last_accessed_at, expires_at, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    memory_type = EXCLUDED.memory_type,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    priority = EXCLUDED.priority,
                    relevance_score = EXCLUDED.relevance_score,
                    access_count = EXCLUDED.access_count,
                    updated_at = EXCLUDED.updated_at,
                    last_accessed_at = EXCLUDED.last_accessed_at,
                    expires_at = EXCLUDED.expires_at,
                    tags = EXCLUDED.tags
            ''', (
                memory.id,
                memory.content,
                memory.memory_type,
                memory.embedding,
                self.Json(memory.metadata),
                memory.priority,
                memory.relevance_score,
                memory.access_count,
                memory.created_at,
                memory.updated_at,
                memory.last_accessed_at,
                memory.expires_at,
                memory.tags
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.debug(f"Stored memory in PostgreSQL: {memory.id}")
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
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM memories WHERE id = %s', (memory_id,))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if row:
                return self._row_to_memory(row)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get memory: {e}", exc_info=True)
            return None
    
    def _row_to_memory(self, row: tuple) -> Memory:
        """Convert database row to Memory object."""
        return Memory(
            id=row[0],
            content=row[1],
            memory_type=row[2],
            embedding=row[3],
            metadata=row[4] if row[4] else {},
            priority=row[5],
            relevance_score=row[6],
            access_count=row[7],
            created_at=row[8],
            updated_at=row[9],
            last_accessed_at=row[10],
            expires_at=row[11],
            tags=row[12] if row[12] else []
        )
    
    def update_memory(self, memory: Memory) -> bool:
        """
        Update a memory.
        
        Args:
            memory: Updated memory object
            
        Returns:
            True if updated successfully
        """
        return self.store_memory(memory)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM memories WHERE id = %s', (memory_id,))
            
            conn.commit()
            deleted = cursor.rowcount > 0
            
            cursor.close()
            conn.close()
            
            if deleted:
                self.logger.debug(f"Deleted memory from PostgreSQL: {memory_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete memory: {e}", exc_info=True)
            return False
    
    def search_memories(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Memory]:
        """
        Search memories by embedding similarity using pgvector.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of memories
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use pgvector's cosine similarity operator
            cursor.execute('''
                SELECT *, 1 - (embedding <=> %s::vector) AS similarity
                FROM memories
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            ''', (query_embedding, query_embedding, min_similarity, query_embedding, limit))
            
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert rows to memories (excluding similarity column)
            memories = [self._row_to_memory(row[:-1]) for row in rows]
            
            self.logger.debug(f"Found {len(memories)} memories in PostgreSQL search")
            return memories
            
        except Exception as e:
            self.logger.error(f"Failed to search memories: {e}", exc_info=True)
            return []
    
    def get_all_memories(self) -> List[Memory]:
        """
        Get all memories from database.
        
        Returns:
            List of all memories
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM memories')
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            memories = [self._row_to_memory(row) for row in rows]
            
            return memories
            
        except Exception as e:
            self.logger.error(f"Failed to get all memories: {e}", exc_info=True)
            return []
    
    def clear(self):
        """Clear all memories from database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM memories')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info("Cleared all memories from PostgreSQL")
            
        except Exception as e:
            self.logger.error(f"Failed to clear memories: {e}", exc_info=True)
    
    def get_count(self) -> int:
        """Get number of stored memories."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM memories')
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to get count: {e}", exc_info=True)
            return 0

