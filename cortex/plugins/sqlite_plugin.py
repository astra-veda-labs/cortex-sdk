"""
SQLite plugin for Cortex SDK.
Provides persistent storage backend using SQLite with vector support.
"""

import sqlite3
import json
from typing import List, Optional
from pathlib import Path
from cortex.utils.schema import Memory
from cortex.utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)


class SQLitePlugin:
    """
    SQLite storage plugin with vector similarity support.
    Provides persistent storage for memories.
    """
    
    def __init__(self, db_path: str = "./cortex_memory.db", embedding_dim: int = 384):
        """
        Initialize SQLite plugin.
        
        Args:
            db_path: Path to SQLite database file
            embedding_dim: Dimension of embedding vectors
        """
        self.db_path = Path(db_path)
        self.embedding_dim = embedding_dim
        self.logger = get_logger(__name__)
        
        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        self.logger.info(f"Initialized SQLitePlugin at {db_path}")
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create memories table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        embedding BLOB,
                        metadata TEXT,
                        priority TEXT,
                        relevance_score REAL,
                        access_count INTEGER,
                        created_at TEXT,
                        updated_at TEXT,
                        last_accessed_at TEXT,
                        expires_at TEXT,
                        tags TEXT
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
                    'CREATE INDEX IF NOT EXISTS idx_relevance ON memories(relevance_score)'
                )
                
                conn.commit()
                self.logger.debug("Database tables initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    def _memory_to_row(self, memory: Memory) -> tuple:
        """Convert Memory object to database row."""
        embedding_blob = None
        if memory.embedding:
            embedding_array = np.array(memory.embedding, dtype=np.float32)
            embedding_blob = embedding_array.tobytes()
        
        return (
            memory.id,
            memory.content,
            memory.memory_type,
            embedding_blob,
            json.dumps(memory.metadata),
            memory.priority,
            memory.relevance_score,
            memory.access_count,
            memory.created_at.isoformat(),
            memory.updated_at.isoformat(),
            memory.last_accessed_at.isoformat() if memory.last_accessed_at else None,
            memory.expires_at.isoformat() if memory.expires_at else None,
            json.dumps(memory.tags)
        )
    
    def _row_to_memory(self, row: tuple) -> Memory:
        """Convert database row to Memory object."""
        from datetime import datetime
        
        embedding = None
        if row[3]:
            embedding = np.frombuffer(row[3], dtype=np.float32).tolist()
        
        return Memory(
            id=row[0],
            content=row[1],
            memory_type=row[2],
            embedding=embedding,
            metadata=json.loads(row[4]) if row[4] else {},
            priority=row[5],
            relevance_score=row[6],
            access_count=row[7],
            created_at=datetime.fromisoformat(row[8]),
            updated_at=datetime.fromisoformat(row[9]),
            last_accessed_at=datetime.fromisoformat(row[10]) if row[10] else None,
            expires_at=datetime.fromisoformat(row[11]) if row[11] else None,
            tags=json.loads(row[12]) if row[12] else []
        )
    
    def store_memory(self, memory: Memory) -> bool:
        """
        Store a memory in database.
        
        Args:
            memory: Memory to store
            
        Returns:
            True if stored successfully
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                row = self._memory_to_row(memory)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO memories
                    (id, content, memory_type, embedding, metadata, priority,
                     relevance_score, access_count, created_at, updated_at,
                     last_accessed_at, expires_at, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                
                conn.commit()
                self.logger.debug(f"Stored memory in SQLite: {memory.id}")
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT * FROM memories WHERE id = ?',
                    (memory_id,)
                )
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_memory(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get memory: {e}", exc_info=True)
            return None
    
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                
                conn.commit()
                self.logger.debug(f"Deleted memory from SQLite: {memory_id}")
                return cursor.rowcount > 0
                
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
        Search memories by embedding similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of memories
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all memories (will compute similarity in Python)
                cursor.execute('SELECT * FROM memories WHERE embedding IS NOT NULL')
                
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # Convert to memories and compute similarities
                memories_with_sim = []
                query_emb = np.array(query_embedding, dtype=np.float32)
                
                for row in rows:
                    memory = self._row_to_memory(row)
                    if memory.embedding:
                        mem_emb = np.array(memory.embedding, dtype=np.float32)
                        
                        # Compute cosine similarity
                        similarity = np.dot(query_emb, mem_emb) / (
                            np.linalg.norm(query_emb) * np.linalg.norm(mem_emb)
                        )
                        
                        if similarity >= min_similarity:
                            memories_with_sim.append((memory, similarity))
                
                # Sort by similarity
                memories_with_sim.sort(key=lambda x: x[1], reverse=True)
                
                # Return top results
                results = [m for m, s in memories_with_sim[:limit]]
                
                self.logger.debug(f"Found {len(results)} memories in SQLite search")
                return results
                
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM memories')
                rows = cursor.fetchall()
                
                memories = [self._row_to_memory(row) for row in rows]
                
                return memories
                
        except Exception as e:
            self.logger.error(f"Failed to get all memories: {e}", exc_info=True)
            return []
    
    def clear(self):
        """Clear all memories from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM memories')
                conn.commit()
                self.logger.info("Cleared all memories from SQLite")
                
        except Exception as e:
            self.logger.error(f"Failed to clear memories: {e}", exc_info=True)
    
    def get_count(self) -> int:
        """Get number of stored memories."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM memories')
                count = cursor.fetchone()[0]
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to get count: {e}", exc_info=True)
            return 0

