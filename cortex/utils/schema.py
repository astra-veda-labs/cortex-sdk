"""
Schema definitions for Cortex SDK data structures.
Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MemoryType(str, Enum):
    """Types of memory storage."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    FILE = "file"


class MemoryPriority(str, Enum):
    """Priority levels for memories."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Memory(BaseModel):
    """Core memory data structure."""
    
    id: str = Field(..., description="Unique memory identifier")
    content: str = Field(..., description="Memory content/text")
    memory_type: MemoryType = Field(default=MemoryType.SHORT_TERM, description="Type of memory")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    priority: MemoryPriority = Field(default=MemoryPriority.MEDIUM, description="Memory priority")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score")
    access_count: int = Field(default=0, ge=0, description="Number of times accessed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last access timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_access(self):
        """Update access timestamp and count."""
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if memory has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class MemorySearchResult(BaseModel):
    """Search result containing memory and similarity score."""
    
    memory: Memory
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    rank: int = Field(..., ge=1, description="Result rank")
    
    class Config:
        use_enum_values = True


class FileMemory(BaseModel):
    """File-based memory with metadata."""
    
    id: str = Field(..., description="Unique file identifier")
    file_path: str = Field(..., description="Path to the file")
    file_name: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    content_summary: Optional[str] = Field(default=None, description="Summary of file content")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: List[str] = Field(default_factory=list, description="File tags")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemorySummary(BaseModel):
    """Summary of a collection of memories."""
    
    summary_text: str = Field(..., description="Summarized content")
    num_memories: int = Field(..., ge=0, description="Number of memories summarized")
    time_range: Optional[Dict[str, datetime]] = Field(default=None, description="Time range of memories")
    topics: List[str] = Field(default_factory=list, description="Extracted topics")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Summary creation time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ForgetCriteria(BaseModel):
    """Criteria for forgetting/removing memories."""
    
    older_than_days: Optional[int] = Field(default=None, ge=0, description="Days threshold")
    relevance_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Min relevance")
    max_access_count: Optional[int] = Field(default=None, ge=0, description="Max access count")
    memory_type: Optional[MemoryType] = Field(default=None, description="Specific memory type")
    tags: Optional[List[str]] = Field(default=None, description="Memory tags to target")
    priority: Optional[MemoryPriority] = Field(default=None, description="Priority level")
    
    class Config:
        use_enum_values = True


class MemoryStats(BaseModel):
    """Statistics about memory storage."""
    
    total_memories: int = Field(default=0, ge=0)
    short_term_count: int = Field(default=0, ge=0)
    long_term_count: int = Field(default=0, ge=0)
    file_count: int = Field(default=0, ge=0)
    total_size_bytes: int = Field(default=0, ge=0)
    oldest_memory: Optional[datetime] = None
    newest_memory: Optional[datetime] = None
    avg_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

