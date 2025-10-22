"""
Summarization engine for Cortex SDK.
Generates summaries of memory content using transformer models.
"""

from typing import List, Optional
from transformers import pipeline, AutoTokenizer
from cortex.utils.logger import get_logger
from cortex.utils.schema import Memory, MemorySummary
from datetime import datetime
import torch

logger = get_logger(__name__)


class Summarizer:
    """
    Handles text summarization for memory content.
    Uses transformer models for abstractive summarization.
    """
    
    def __init__(
        self,
        model_name: str = "facebook/bart-large-cnn",
        use_gpu: bool = False,
        max_length: int = 150,
        min_length: int = 50
    ):
        """
        Initialize summarizer.
        
        Args:
            model_name: Name of the summarization model
            use_gpu: Whether to use GPU acceleration
            max_length: Maximum summary length
            min_length: Minimum summary length
        """
        self.model_name = model_name
        self.max_length = max_length
        self.min_length = min_length
        self.logger = get_logger(__name__)
        
        # Determine device
        device = 0 if use_gpu and torch.cuda.is_available() else -1
        
        # Load summarization pipeline
        try:
            self.logger.info(f"Loading summarization model: {model_name}")
            self.summarizer = pipeline(
                "summarization",
                model=model_name,
                device=device
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.logger.info("Summarization model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load summarization model: {e}", exc_info=True)
            raise
    
    def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None
    ) -> str:
        """
        Summarize a single text.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length (uses default if None)
            min_length: Minimum summary length (uses default if None)
            
        Returns:
            Summary text
        """
        try:
            if not text or len(text.strip()) == 0:
                return ""
            
            max_len = max_length or self.max_length
            min_len = min_length or self.min_length
            
            # Truncate text if too long for model
            tokens = self.tokenizer.encode(text, truncation=True, max_length=1024)
            truncated_text = self.tokenizer.decode(tokens, skip_special_tokens=True)
            
            # Generate summary
            summary_output = self.summarizer(
                truncated_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            
            summary = summary_output[0]['summary_text']
            self.logger.debug(f"Generated summary of length {len(summary)}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to summarize text: {e}", exc_info=True)
            return text[:max_len] if len(text) > max_len else text
    
    def summarize_memories(
        self,
        memories: List[Memory],
        include_metadata: bool = True
    ) -> MemorySummary:
        """
        Summarize a collection of memories.
        
        Args:
            memories: List of memories to summarize
            include_metadata: Whether to include metadata in summary
            
        Returns:
            MemorySummary object
        """
        try:
            if not memories:
                return MemorySummary(
                    summary_text="No memories to summarize.",
                    num_memories=0,
                    topics=[],
                    time_range=None
                )
            
            # Combine memory contents
            combined_text = " ".join([m.content for m in memories])
            
            # Generate summary
            summary_text = self.summarize_text(combined_text)
            
            # Extract topics from tags
            all_tags = set()
            for memory in memories:
                all_tags.update(memory.tags)
            topics = list(all_tags)
            
            # Calculate time range
            time_range = None
            if memories:
                oldest = min(m.created_at for m in memories)
                newest = max(m.created_at for m in memories)
                time_range = {'start': oldest, 'end': newest}
            
            memory_summary = MemorySummary(
                summary_text=summary_text,
                num_memories=len(memories),
                topics=topics,
                time_range=time_range
            )
            
            self.logger.info(f"Summarized {len(memories)} memories")
            return memory_summary
            
        except Exception as e:
            self.logger.error(f"Failed to summarize memories: {e}", exc_info=True)
            # Return basic summary on error
            return MemorySummary(
                summary_text="Error generating summary.",
                num_memories=len(memories),
                topics=[],
                time_range=None
            )
    
    def extractive_summary(self, text: str, num_sentences: int = 3) -> str:
        """
        Create extractive summary by selecting key sentences.
        
        Args:
            text: Text to summarize
            num_sentences: Number of sentences to extract
            
        Returns:
            Extractive summary
        """
        try:
            # Simple sentence extraction based on position and length
            sentences = text.split('. ')
            
            if len(sentences) <= num_sentences:
                return text
            
            # Score sentences (simple heuristic: prefer longer, earlier sentences)
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = len(sentence) * (1 / (i + 1))  # Length * position weight
                scored_sentences.append((score, sentence))
            
            # Sort by score and select top sentences
            scored_sentences.sort(reverse=True, key=lambda x: x[0])
            top_sentences = [s[1] for s in scored_sentences[:num_sentences]]
            
            # Join sentences
            summary = '. '.join(top_sentences)
            if not summary.endswith('.'):
                summary += '.'
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to create extractive summary: {e}", exc_info=True)
            return text[:500]  # Return first 500 chars on error
    
    def summarize_by_topic(
        self,
        memories: List[Memory],
        topic: str
    ) -> str:
        """
        Summarize memories related to a specific topic.
        
        Args:
            memories: List of memories
            topic: Topic to focus on
            
        Returns:
            Topic-focused summary
        """
        try:
            # Filter memories related to topic
            topic_lower = topic.lower()
            relevant_memories = [
                m for m in memories
                if topic_lower in m.content.lower() or topic_lower in [t.lower() for t in m.tags]
            ]
            
            if not relevant_memories:
                return f"No memories found related to '{topic}'."
            
            # Combine and summarize
            combined_text = f"Regarding {topic}: " + " ".join([m.content for m in relevant_memories])
            summary = self.summarize_text(combined_text)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to summarize by topic: {e}", exc_info=True)
            return f"Error summarizing memories about '{topic}'."
    
    def batch_summarize(
        self,
        texts: List[str],
        max_length: Optional[int] = None,
        min_length: Optional[int] = None
    ) -> List[str]:
        """
        Summarize multiple texts in batch.
        
        Args:
            texts: List of texts to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            List of summaries
        """
        try:
            summaries = []
            
            for text in texts:
                summary = self.summarize_text(text, max_length, min_length)
                summaries.append(summary)
            
            self.logger.info(f"Batch summarized {len(texts)} texts")
            return summaries
            
        except Exception as e:
            self.logger.error(f"Failed to batch summarize: {e}", exc_info=True)
            return texts  # Return original texts on error
    
    def get_key_phrases(self, text: str, num_phrases: int = 5) -> List[str]:
        """
        Extract key phrases from text.
        
        Args:
            text: Text to analyze
            num_phrases: Number of key phrases to extract
            
        Returns:
            List of key phrases
        """
        try:
            # Simple word frequency-based extraction
            words = text.lower().split()
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had'}
            filtered_words = [w.strip('.,!?;:') for w in words if w not in stop_words]
            
            # Count frequencies
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Return top phrases
            key_phrases = [word for word, freq in sorted_words[:num_phrases]]
            
            return key_phrases
            
        except Exception as e:
            self.logger.error(f"Failed to extract key phrases: {e}", exc_info=True)
            return []

