"""
Chroma Backend for Cortex SDK

This module implements the Chroma vector database backend for semantic search.
"""

from typing import List, Dict, Any, Optional
from .base_backend import BaseBackend, Memory, MemoryType, MemoryPriority, MemorySearchResult
import uuid
import time

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class ChromaBackend(BaseBackend):
    """Chroma vector database backend implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Chroma backend
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.client = None
        self.collection = None
        self.persistent = config.get("persistent", False)
        self.collection_name = config.get("collection_name", "cortex_memories")
        self.similarity_threshold = config.get("similarity_threshold", 0.5)
        self.embedding_model = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    
    def initialize(self) -> bool:
        """Initialize the Chroma backend"""
        if not CHROMA_AVAILABLE:
            print("Chroma not available. Install with: pip install chromadb")
            return False
        
        try:
            # Initialize Chroma client
            if self.persistent:
                self.client = chromadb.PersistentClient(path="./chroma_db")
            else:
                self.client = chromadb.Client(Settings(anonymized_telemetry=False))
            
            # Create or get collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Cortex SDK memories"}
                )
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Chroma backend: {e}")
            return False
    
    def store_memory(self, memory: Memory) -> bool:
        """Store a memory in Chroma"""
        if not self.initialized or not self.collection:
            return False
        
        try:
            # Generate ID if not provided
            if not memory.id:
                memory.id = str(uuid.uuid4())
            
            # Add timestamp
            memory.metadata["timestamp"] = time.time()
            
            # Prepare metadata for Chroma
            chroma_metadata = {
                "memory_type": str(memory.memory_type),
                "priority": str(memory.priority),
                "timestamp": memory.metadata["timestamp"]
            }
            
            # Add custom metadata
            for key, value in memory.metadata.items():
                if key != "timestamp":  # Already added
                    chroma_metadata[key] = str(value)  # Chroma requires string values
            
            # Store in Chroma
            self.collection.add(
                documents=[memory.content],
                metadatas=[chroma_metadata],
                ids=[memory.id]
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing memory in Chroma: {e}")
            return False
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID"""
        if not self.initialized or not self.collection:
            return None
        
        try:
            result = self.collection.get(ids=[memory_id])
            
            if result["ids"]:
                # Reconstruct Memory object
                content = result["documents"][0]
                metadata = result["metadatas"][0]
                
                # Convert metadata back to original types
                memory_metadata = {}
                for key, value in metadata.items():
                    if key in ["memory_type", "priority"]:
                        continue  # Skip Chroma-specific fields
                    memory_metadata[key] = value
                
                memory = Memory(
                    id=memory_id,
                    content=content,
                    memory_type=MemoryType(metadata["memory_type"]),
                    priority=MemoryPriority(metadata["priority"]),
                    metadata=memory_metadata
                )
                
                return memory
            
            return None
            
        except Exception as e:
            print(f"Error retrieving memory from Chroma: {e}")
            return None
    
    def search_memories(
        self, 
        query: str, 
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        min_similarity: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """Search for memories using Chroma's semantic search"""
        if not self.initialized or not self.collection:
            return []
        
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if memory_type:
                where_clause["memory_type"] = memory_type.value
            
            # Add custom filters
            if filters:
                for key, value in filters.items():
                    where_clause[key] = str(value)  # Chroma requires string values
            
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Convert to MemorySearchResult objects
            search_results = []
            
            if results["ids"] and results["ids"][0]:
                for i, (memory_id, content, metadata, distance) in enumerate(
                    zip(
                        results["ids"][0],
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0]
                    )
                ):
                    # Convert distance to similarity (Chroma uses distance, we want similarity)
                    similarity = 1.0 - distance
                    
                    if similarity >= min_similarity:
                        # Reconstruct Memory object
                        memory_metadata = {}
                        for key, value in metadata.items():
                            if key in ["memory_type", "priority"]:
                                continue
                            memory_metadata[key] = value
                        
                        memory = Memory(
                            id=memory_id,
                            content=content,
                            memory_type=MemoryType(metadata["memory_type"]),
                            priority=MemoryPriority(metadata["priority"]),
                            metadata=memory_metadata
                        )
                        
                        result = MemorySearchResult(
                            memory=memory,
                            similarity=similarity,
                            rank=i + 1
                        )
                        search_results.append(result)
            
            return search_results
            
        except Exception as e:
            print(f"Error searching memories in Chroma: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID"""
        if not self.initialized or not self.collection:
            return False
        
        try:
            self.collection.delete(ids=[memory_id])
            return True
            
        except Exception as e:
            print(f"Error deleting memory from Chroma: {e}")
            return False
    
    def clear_memories(self, memory_type: Optional[MemoryType] = None) -> bool:
        """Clear all memories or memories of a specific type"""
        if not self.initialized or not self.collection:
            return False
        
        try:
            if memory_type:
                # Delete specific type
                self.collection.delete(
                    where={"memory_type": memory_type.value}
                )
            else:
                # Delete all
                self.collection.delete()
            
            return True
            
        except Exception as e:
            print(f"Error clearing memories in Chroma: {e}")
            return False
    
    def get_memory_count(self, memory_type: Optional[MemoryType] = None) -> int:
        """Get the count of memories"""
        if not self.initialized or not self.collection:
            return 0
        
        try:
            if memory_type:
                result = self.collection.get(
                    where={"memory_type": memory_type.value}
                )
                return len(result["ids"])
            else:
                result = self.collection.get()
                return len(result["ids"])
                
        except Exception as e:
            print(f"Error getting memory count from Chroma: {e}")
            return 0
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend information"""
        info = {
            "type": "chroma",
            "initialized": self.initialized,
            "persistent": self.persistent,
            "collection_name": self.collection_name,
            "similarity_threshold": self.similarity_threshold,
            "embedding_model": self.embedding_model
        }
        
        if self.initialized and self.collection:
            try:
                result = self.collection.get()
                info["total_memories"] = len(result["ids"])
                
                # Count by memory type
                memory_types = {}
                for metadata in result["metadatas"]:
                    memory_type = metadata.get("memory_type", "unknown")
                    memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
                
                info["memories_by_type"] = memory_types
                
            except Exception as e:
                info["error"] = str(e)
        
        return info
