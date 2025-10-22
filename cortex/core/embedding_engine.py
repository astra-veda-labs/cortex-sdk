"""
Embedding engine for Cortex SDK.
Generates vector embeddings for semantic search and similarity.
"""

import numpy as np
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
import torch
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingEngine:
    """
    Handles text embedding generation using transformer models.
    Provides semantic vector representations for memory content.
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        use_gpu: bool = False,
        batch_size: int = 32
    ):
        """
        Initialize embedding engine.
        
        Args:
            model_name: Name of the sentence transformer model
            use_gpu: Whether to use GPU acceleration
            batch_size: Batch size for encoding
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.logger = get_logger(__name__)
        
        # Determine device
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        
        # Load model
        try:
            self.logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name, device=self.device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.logger.info(f"Loaded model with embedding dimension: {self.embedding_dim}")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            raise
    
    def encode(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode text into embeddings.
        
        Args:
            text: Single text or list of texts
            normalize: Whether to normalize embeddings
            
        Returns:
            Numpy array of embeddings
        """
        try:
            # Convert single string to list
            is_single = isinstance(text, str)
            if is_single:
                text = [text]
            
            # Generate embeddings
            embeddings = self.model.encode(
                text,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=normalize,
                convert_to_numpy=True
            )
            
            # Return single embedding if input was single string
            if is_single:
                return embeddings[0]
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to encode text: {e}", exc_info=True)
            raise
    
    def compute_similarity(
        self,
        embedding1: Union[np.ndarray, List[float]],
        embedding2: Union[np.ndarray, List[float]]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0 to 1)
        """
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            # Clip to [0, 1] range
            similarity = np.clip(similarity, 0, 1)
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Failed to compute similarity: {e}", exc_info=True)
            return 0.0
    
    def compute_similarities(
        self,
        query_embedding: Union[np.ndarray, List[float]],
        embeddings: List[Union[np.ndarray, List[float]]]
    ) -> List[float]:
        """
        Compute similarities between query and multiple embeddings.
        
        Args:
            query_embedding: Query embedding
            embeddings: List of embeddings to compare
            
        Returns:
            List of similarity scores
        """
        try:
            query_emb = np.array(query_embedding)
            embeddings_array = np.array(embeddings)
            
            # Compute dot products
            similarities = np.dot(embeddings_array, query_emb)
            
            # Normalize
            query_norm = np.linalg.norm(query_emb)
            embeddings_norms = np.linalg.norm(embeddings_array, axis=1)
            similarities = similarities / (embeddings_norms * query_norm)
            
            # Clip to [0, 1] range
            similarities = np.clip(similarities, 0, 1)
            
            return similarities.tolist()
            
        except Exception as e:
            self.logger.error(f"Failed to compute similarities: {e}", exc_info=True)
            return [0.0] * len(embeddings)
    
    def find_most_similar(
        self,
        query_embedding: Union[np.ndarray, List[float]],
        embeddings: List[Union[np.ndarray, List[float]]],
        top_k: int = 10,
        min_similarity: float = 0.0
    ) -> List[tuple]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            embeddings: List of embeddings to search
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (index, similarity) tuples
        """
        try:
            # Compute all similarities
            similarities = self.compute_similarities(query_embedding, embeddings)
            
            # Create (index, similarity) pairs
            results = [(i, sim) for i, sim in enumerate(similarities) if sim >= min_similarity]
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Failed to find similar embeddings: {e}", exc_info=True)
            return []
    
    def batch_encode(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Encode texts in batches for efficiency.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size (uses default if None)
            show_progress: Whether to show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        try:
            batch_size = batch_size or self.batch_size
            
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            
            self.logger.debug(f"Encoded {len(texts)} texts in batches")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to batch encode: {e}", exc_info=True)
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.embedding_dim
    
    def clear_cache(self):
        """Clear model cache if using GPU."""
        if self.device == "cuda":
            torch.cuda.empty_cache()
            self.logger.debug("Cleared CUDA cache")


class CachedEmbeddingEngine(EmbeddingEngine):
    """
    Embedding engine with caching for frequently accessed embeddings.
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        use_gpu: bool = False,
        batch_size: int = 32,
        cache_size: int = 1000
    ):
        """
        Initialize cached embedding engine.
        
        Args:
            model_name: Name of the sentence transformer model
            use_gpu: Whether to use GPU acceleration
            batch_size: Batch size for encoding
            cache_size: Maximum number of cached embeddings
        """
        super().__init__(model_name, use_gpu, batch_size)
        
        self.cache_size = cache_size
        self.cache = {}  # text -> embedding
        self.cache_hits = 0
        self.cache_misses = 0
    
    def encode(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode text with caching support.
        
        Args:
            text: Single text or list of texts
            normalize: Whether to normalize embeddings
            
        Returns:
            Numpy array of embeddings
        """
        # Handle list of texts
        if isinstance(text, list):
            return super().encode(text, normalize)
        
        # Check cache for single text
        if text in self.cache:
            self.cache_hits += 1
            self.logger.debug(f"Cache hit for text (total hits: {self.cache_hits})")
            return self.cache[text]
        
        # Compute embedding
        self.cache_misses += 1
        embedding = super().encode(text, normalize)
        
        # Add to cache
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[text] = embedding
        
        return embedding
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            'cache_size': len(self.cache),
            'max_cache_size': self.cache_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0.0,
        }
    
    def clear_cache(self):
        """Clear embedding cache."""
        super().clear_cache()
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger.info("Cleared embedding cache")

