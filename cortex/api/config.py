"""
Configuration management for Cortex SDK.
Handles all configuration options for memory management system.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class MemoryConfig(BaseModel):
    """Configuration for Cortex memory management."""
    
    # Storage capacities
    short_term_capacity: int = Field(default=1000, ge=1, description="Max short-term memories")
    long_term_capacity: int = Field(default=10000, ge=1, description="Max long-term memories")
    file_storage_capacity: int = Field(default=1000, ge=1, description="Max file memories")
    
    # Model configurations
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Model for embeddings"
    )
    summarization_model: str = Field(
        default="facebook/bart-large-cnn",
        description="Model for summarization"
    )
    
    # Embedding settings
    embedding_dimension: int = Field(default=384, ge=1, description="Embedding vector dimension")
    batch_size: int = Field(default=32, ge=1, description="Batch size for processing")
    
    # Memory management
    auto_summarize: bool = Field(default=True, description="Auto-summarize old memories")
    auto_forget: bool = Field(default=False, description="Auto-forget low relevance memories")
    forget_threshold: float = Field(default=0.2, ge=0.0, le=1.0, description="Relevance threshold")
    short_term_ttl_days: Optional[int] = Field(default=7, ge=1, description="Short-term TTL in days")
    long_term_ttl_days: Optional[int] = Field(default=None, description="Long-term TTL in days")
    
    # Search settings
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Min similarity")
    max_search_results: int = Field(default=10, ge=1, description="Max search results")
    
    # Backend settings
    backend: str = Field(default="local", description="Storage backend type")
    connection_string: Optional[str] = Field(default=None, description="DB connection string")
    db_path: Optional[str] = Field(default="./cortex_memory.db", description="Database path")
    
    # Advanced options
    enable_caching: bool = Field(default=True, description="Enable result caching")
    cache_ttl_seconds: int = Field(default=300, ge=1, description="Cache TTL in seconds")
    use_gpu: bool = Field(default=False, description="Use GPU for models")
    num_threads: int = Field(default=4, ge=1, description="Number of threads")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    verbose: bool = Field(default=False, description="Verbose output")
    
    class Config:
        validate_assignment = True
    
    @validator('backend')
    def validate_backend(cls, v):
        """Validate backend type."""
        valid_backends = ['local', 'sqlite', 'pgvector']
        if v not in valid_backends:
            raise ValueError(f"Backend must be one of {valid_backends}")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "MemoryConfig":
        """Create config from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def default(cls) -> "MemoryConfig":
        """Get default configuration."""
        return cls()
    
    @classmethod
    def lightweight(cls) -> "MemoryConfig":
        """Get lightweight configuration for limited resources."""
        return cls(
            short_term_capacity=100,
            long_term_capacity=1000,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimension=384,
            batch_size=16,
            use_gpu=False,
            enable_caching=False
        )
    
    @classmethod
    def performance(cls) -> "MemoryConfig":
        """Get high-performance configuration."""
        return cls(
            short_term_capacity=5000,
            long_term_capacity=50000,
            embedding_model="sentence-transformers/all-mpnet-base-v2",
            embedding_dimension=768,
            batch_size=64,
            use_gpu=True,
            enable_caching=True,
            num_threads=8
        )


class BackendConfig(BaseModel):
    """Backend-specific configuration."""
    
    backend_type: str = Field(..., description="Type of backend")
    connection_params: Dict[str, Any] = Field(default_factory=dict, description="Connection params")
    pool_size: int = Field(default=5, ge=1, description="Connection pool size")
    timeout: int = Field(default=30, ge=1, description="Connection timeout in seconds")
    
    class Config:
        validate_assignment = True

