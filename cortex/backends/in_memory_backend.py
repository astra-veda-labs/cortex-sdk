"""
In-Memory Backend for Cortex SDK

This module implements the in-memory storage backend using Python data structures.
"""

from typing import List, Dict, Any, Optional
from .base_backend import BaseBackend, Memory, MemoryType, MemoryPriority, MemorySearchResult
import uuid
import time
from collections import defaultdict


class InMemoryBackend(BaseBackend):
    """In-memory storage backend implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize in-memory backend
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.memories: Dict[str, Memory] = {}
        self.memories_by_type: Dict[MemoryType, List[str]] = defaultdict(list)
        self.memories_by_session: Dict[str, List[str]] = defaultdict(list)
        self.capacity = config.get("capacity", 1000)
        self.persistent = config.get("persistent", False)
    
    def initialize(self) -> bool:
        """Initialize the in-memory backend"""
        try:
            self.memories.clear()
            self.memories_by_type.clear()
            self.memories_by_session.clear()
            self.initialized = True
            return True
        except Exception as e:
            print(f"Error initializing in-memory backend: {e}")
            return False
    
    def store_memory(self, memory: Memory) -> bool:
        """Store a memory in the in-memory backend"""
        try:
            # Generate ID if not provided
            if not memory.id:
                memory.id = str(uuid.uuid4())
            
            # Add timestamp
            memory.metadata["timestamp"] = time.time()
            
            # Store memory
            self.memories[memory.id] = memory
            
            # Index by type
            self.memories_by_type[memory.memory_type].append(memory.id)
            
            # Index by session
            session_id = memory.metadata.get("session_id")
            if session_id:
                self.memories_by_session[session_id].append(memory.id)
            
            # Check capacity and remove oldest if needed
            if len(self.memories) > self.capacity:
                self._remove_oldest_memory()
            
            return True
            
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID"""
        return self.memories.get(memory_id)
    
    def search_memories(
        self, 
        query: str, 
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_similarity: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Search for memories using simple text matching"""
        results = []
        
        # Get memories to search
        memories_to_search = []
        if memory_type:
            memory_ids = self.memories_by_type.get(memory_type, [])
            memories_to_search = [self.memories[mid] for mid in memory_ids if mid in self.memories]
        else:
            memories_to_search = list(self.memories.values())
        
        # Apply filters
        if filters:
            memories_to_search = self._apply_filters(memories_to_search, filters)
        
        # Simple text-based similarity (for demo purposes)
        query_lower = query.lower()
        for memory in memories_to_search:
            content_lower = memory.content.lower()
            
            # Simple similarity calculation
            similarity = self._calculate_similarity(query_lower, content_lower)
            
            if similarity >= min_similarity:
                result = MemorySearchResult(
                    memory=memory,
                    similarity=similarity,
                    rank=len(results) + 1
                )
                results.append(result)
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        try:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                
                # Remove from type index
                if memory_id in self.memories_by_type[memory.memory_type]:
                    self.memories_by_type[memory.memory_type].remove(memory_id)
                
                # Remove from session index
                session_id = memory.metadata.get("session_id")
                if session_id and memory_id in self.memories_by_session[session_id]:
                    self.memories_by_session[session_id].remove(memory_id)
                
                # Remove from main storage
                del self.memories[memory_id]
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False
    
    def clear_memories(self, memory_type: Optional[MemoryType] = None) -> bool:
        """Clear all memories or memories of a specific type"""
        try:
            if memory_type:
                # Clear specific type
                memory_ids = self.memories_by_type.get(memory_type, [])
                for memory_id in memory_ids:
                    if memory_id in self.memories:
                        del self.memories[memory_id]
                self.memories_by_type[memory_type] = []
            else:
                # Clear all
                self.memories.clear()
                self.memories_by_type.clear()
                self.memories_by_session.clear()
            
            return True
            
        except Exception as e:
            print(f"Error clearing memories: {e}")
            return False
    
    def get_memory_count(self, memory_type: Optional[MemoryType] = None) -> int:
        """Get the count of memories"""
        if memory_type:
            return len(self.memories_by_type.get(memory_type, []))
        return len(self.memories)
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend information"""
        return {
            "type": "in_memory",
            "initialized": self.initialized,
            "total_memories": len(self.memories),
            "memories_by_type": {
                memory_type.value: len(memory_ids) 
                for memory_type, memory_ids in self.memories_by_type.items()
            },
            "sessions": len(self.memories_by_session),
            "capacity": self.capacity,
            "persistent": self.persistent
        }
    
    def _calculate_similarity(self, query: str, content: str) -> float:
        """Calculate simple text similarity"""
        if not query or not content:
            return 0.0
        
        # Simple word overlap similarity
        query_words = set(query.split())
        content_words = set(content.split())
        
        if not query_words or not content_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _apply_filters(self, memories: List[Memory], filters: Dict[str, Any]) -> List[Memory]:
        """Apply filters to memories"""
        filtered = []
        
        for memory in memories:
            match = True
            
            for key, value in filters.items():
                if key in memory.metadata:
                    if memory.metadata[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                filtered.append(memory)
        
        return filtered
    
    def _remove_oldest_memory(self):
        """Remove the oldest memory to maintain capacity"""
        if not self.memories:
            return
        
        # Find oldest memory by timestamp
        oldest_id = min(
            self.memories.keys(),
            key=lambda x: self.memories[x].metadata.get("timestamp", 0)
        )
        
        # Remove oldest memory
        self.delete_memory(oldest_id)

