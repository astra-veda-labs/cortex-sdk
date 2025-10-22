"""
Pytest configuration and fixtures for Cortex SDK tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from cortex import MemoryManager, MemoryConfig
from cortex.utils.schema import Memory, MemoryType, MemoryPriority
from datetime import datetime
import uuid


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config():
    """Create a test configuration."""
    config = MemoryConfig(
        short_term_capacity=10,
        long_term_capacity=100,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimension=384,
        batch_size=4,
        use_gpu=False,
        enable_caching=False,
        backend="local"
    )
    return config


@pytest.fixture
def memory_manager(test_config):
    """Create a memory manager instance for testing."""
    return MemoryManager(config=test_config)


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    return Memory(
        id=str(uuid.uuid4()),
        content="This is a test memory about machine learning",
        memory_type=MemoryType.SHORT_TERM,
        embedding=[0.1] * 384,
        metadata={"source": "test"},
        tags=["test", "ml"],
        priority=MemoryPriority.MEDIUM,
        relevance_score=0.8,
        access_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_memories():
    """Create multiple sample memories for testing."""
    memories = []
    
    topics = [
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language for data science",
        "Neural networks are inspired by biological neurons",
        "Deep learning uses multiple layers of neural networks",
        "Natural language processing deals with text data"
    ]
    
    for i, topic in enumerate(topics):
        memory = Memory(
            id=str(uuid.uuid4()),
            content=topic,
            memory_type=MemoryType.LONG_TERM if i % 2 == 0 else MemoryType.SHORT_TERM,
            embedding=[0.1 * (i + 1)] * 384,
            metadata={"index": i},
            tags=["ai", "tech"],
            priority=MemoryPriority.MEDIUM,
            relevance_score=0.7 + (i * 0.05),
            access_count=i,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        memories.append(memory)
    
    return memories


@pytest.fixture
def sample_content():
    """Sample text content for testing."""
    return {
        "short": "Python is great for AI",
        "medium": "Machine learning algorithms can learn patterns from data without explicit programming.",
        "long": """
        Artificial intelligence and machine learning have revolutionized how we process
        and analyze data. From natural language processing to computer vision, these
        technologies are transforming industries. Deep learning, a subset of machine
        learning, uses neural networks with multiple layers to achieve state-of-the-art
        results in various tasks. Python has emerged as the dominant programming language
        in this field, with libraries like TensorFlow, PyTorch, and scikit-learn providing
        powerful tools for researchers and practitioners.
        """
    }


@pytest.fixture(autouse=True)
def reset_test_environment():
    """Reset test environment before each test."""
    # This runs before each test
    yield
    # Cleanup after test if needed
    pass


@pytest.fixture
def mock_embedding():
    """Create a mock embedding vector."""
    return [0.5] * 384


@pytest.fixture
def sqlite_db_path(temp_dir):
    """Create a path for SQLite database in temp directory."""
    return str(temp_dir / "test_cortex.db")


@pytest.fixture
def memory_manager_sqlite(test_config, sqlite_db_path):
    """Create a memory manager with SQLite backend."""
    test_config.backend = "sqlite"
    test_config.db_path = sqlite_db_path
    return MemoryManager(config=test_config)

