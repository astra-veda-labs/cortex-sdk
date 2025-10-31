"""
Cortex-powered AI Chatbot
Integrates Llama model with Cortex SDK memory management.
Uses Cortex SDK as external dependency for conversation memory.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Import Cortex SDK (as external package)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

try:
    from cortex.core.memory_manager import MemoryManager
    from cortex.api.config import MemoryConfig
    from cortex.utils.schema import MemoryType, MemoryPriority
    CORTEX_AVAILABLE = True
except ImportError as e:
    CORTEX_AVAILABLE = False
    # Create dummy classes for when Cortex is not available
    MemoryManager = None
    MemoryConfig = None
    MemoryType = None
    MemoryPriority = None
    print(f"Warning: Cortex SDK not available ({e}). Install with: pip install -e ../../../")

from llama_cpp import Llama

# Import summarization libraries
try:
    from transformers import pipeline
    SUMMARIZATION_AVAILABLE = True
except ImportError:
    SUMMARIZATION_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_SIMILARITY_AVAILABLE = True
except ImportError:
    SEMANTIC_SIMILARITY_AVAILABLE = False

# Configure logger to show INFO level messages
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class CortexChatBot:
    """
    AI Chatbot powered by Llama with Cortex memory management.
    Uses Cortex for intelligent conversation history and context retrieval.
    """
    
    def __init__(
        self,
        model_path: str,
        memory_config: Optional['MemoryConfig'] = None,
        max_context_messages: int = 10,
        use_cortex: bool = True,
        enable_summarization: bool = True,
        topic_relevance_threshold: float = 0.3  # Semantic similarity threshold for topic relevance
    ):
        """
        Initialize Cortex-powered chatbot.
        
        Args:
            model_path: Path to the Llama model file
            memory_config: Cortex memory configuration (optional)
            max_context_messages: Maximum messages to include in context
            use_cortex: Whether to use Cortex SDK for memory management
            enable_summarization: Whether to summarize old context
            topic_relevance_threshold: Minimum semantic similarity for topic relevance
        """
        self.model_path = model_path
        self.model = None
        self.max_context_messages = max_context_messages
        self.use_cortex = use_cortex and CORTEX_AVAILABLE
        self.enable_summarization = enable_summarization
        self.topic_relevance_threshold = topic_relevance_threshold
        
        # Initialize summarizer if available
        self.summarizer = None
        if enable_summarization and SUMMARIZATION_AVAILABLE:
            try:
                # Use a lightweight summarization model
                logger.info("Initializing summarization model...")
                self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)
                logger.info("Summarization model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load summarization model: {e}. Continuing without summarization.")
                self.summarizer = None
        
        # Initialize semantic similarity model for topic relevance
        self.semantic_model = None
        if SEMANTIC_SIMILARITY_AVAILABLE:
            try:
                logger.info("Loading semantic similarity model for topic filtering...")
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic similarity model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load semantic similarity model: {e}")
                self.semantic_model = None
        
        # Initialize Cortex Memory Manager if available
        if self.use_cortex:
            if memory_config is None:
                memory_config = MemoryConfig.lightweight()
                memory_config.backend = "local"  # Use in-memory storage
                memory_config.short_term_capacity = 1000  # Store up to 1000 messages
                memory_config.short_term_ttl_days = 1  # Messages expire after 1 day
            
            self.memory = MemoryManager(config=memory_config)
            logger.info("Initialized CortexChatBot with Cortex SDK memory management")
        else:
            self.memory = None
            logger.warning("Cortex SDK not available, using basic memory")
        
        # Session storage for quick access
        self.sessions: Dict[str, List[str]] = {}  # session_id -> [memory_ids]
        
        # Topic tracking per session - track current topic to maintain context chains
        self.session_topics: Dict[str, str] = {}  # session_id -> current_topic
        self.topic_contexts: Dict[str, Dict[str, List[str]]] = {}  # session_id -> {topic: [memory_ids]}
    
    def load_model(self):
        """Load the Llama model."""
        if self.model is None:
            logger.info(f"Loading Llama model from {self.model_path}")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                n_threads=4,
                n_gpu_layers=0,
                verbose=False
            )
            logger.info("Llama model loaded successfully")
    
    def _store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        priority=None
    ) -> str:
        """
        Store a message in Cortex memory or fallback storage.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            priority: Memory priority (if Cortex is available)
            
        Returns:
            Memory ID
        """
        try:
            if not self.use_cortex or self.memory is None:
                # Fallback: simple list storage
                if session_id not in self.sessions:
                    self.sessions[session_id] = []
                msg_dict = {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.sessions[session_id].append(msg_dict)
                logger.debug(f"Stored message in fallback storage")
                return str(len(self.sessions[session_id]) - 1)
            
            # Create metadata for the message
            metadata = {
                "session_id": session_id,
                "role": role,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in Cortex memory (short-term for chat messages)
            if priority is None:
                priority = MemoryPriority.MEDIUM
                
            memory_id = self.memory.remember(
                content=content,
                memory_type=MemoryType.SHORT_TERM,
                metadata=metadata,
                tags=[f"session:{session_id}", f"role:{role}", "chat"],
                priority=priority
            )
            
            # Track in session
            if session_id not in self.sessions:
                self.sessions[session_id] = []
            self.sessions[session_id].append(memory_id)
            
            logger.debug(f"Stored message in Cortex memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store message in memory: {e}", exc_info=True)
            return ""
    
    def _check_answer_cache(
        self,
        user_message: str,
        session_id: str,
        similarity_threshold: float = 0.90  # Lowered from 0.95 to 0.90 for more aggressive caching
    ) -> Optional[Dict]:
        """
        Check if we have a cached answer for a similar question.
        Uses AGGRESSIVE similarity threshold (0.90 = 90%) for faster responses.
        
        Args:
            user_message: Current user question
            session_id: Session identifier
            similarity_threshold: Minimum similarity to use cached answer (default: 0.90)
            
        Returns:
            Cached response dict if found, None otherwise
        """
        try:
            if not self.use_cortex or self.memory is None:
                return None
            
            # Search for similar user questions in recent history
            results = self.memory.recall(
                query=user_message,
                memory_type=MemoryType.SHORT_TERM,
                limit=10,  # Check last 10 messages
                min_similarity=similarity_threshold,  # 90% similar = aggressive caching
                tags=[f"session:{session_id}", "role:user", "chat"]
            )
            
            # If we found a nearly identical question
            for result in results:
                if result.similarity >= similarity_threshold:
                    # Get the answer that followed this question
                    cached_question_id = result.memory.id
                    
                    # Find the assistant response that came after this question
                    all_session_memories = self.sessions.get(session_id, [])
                    
                    try:
                        question_index = all_session_memories.index(cached_question_id)
                        # Check if there's an answer after this question
                        if question_index + 1 < len(all_session_memories):
                            answer_id = all_session_memories[question_index + 1]
                            answer_memory = self.memory.get_memory(answer_id)
                            
                            if answer_memory and answer_memory.metadata.get("role") == "assistant":
                                logger.info(f"Found cached answer (similarity: {result.similarity:.2%})")
                                
                                # Return cached response
                                return {
                                    "response": answer_memory.content,
                                    "context_used": 1,
                                    "context_messages": [{
                                        "role": "user",
                                        "content": result.memory.content
                                    }],
                                    "source": "cached_answer",
                                    "cached": True,
                                    "cache_similarity": result.similarity
                                }
                    except (ValueError, IndexError):
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking answer cache: {e}", exc_info=True)
            return None
    
    def _detect_topic(self, text: str) -> str:
        """
        Detect the topic of a conversation using semantic embeddings.
        
        Args:
            text: Text to analyze
            
        Returns:
            Topic identifier (simplified)
        """
        try:
            if self.semantic_model:
                # Use semantic clustering to detect topic
                # For simplicity, we'll use keyword-based detection with semantic enhancement
                text_lower = text.lower()
                
                # Define topic keywords
                topic_keywords = {
                    'cars': ['car', 'cars', 'vehicle', 'vehicles', 'automobile', 'buying car', 'car price', 'honda', 'toyota', 'bmw', 'mercedes'],
                    'food': ['food', 'cooking', 'recipe', 'ingredient', 'dish', 'meal', 'pickle', 'tomato', 'curry', 'rice', 'chicken', 'beef'],
                    'coding': ['code', 'programming', 'python', 'function', 'algorithm', 'palindrome', 'software', 'developer', 'debug'],
                    'general': []  # Default
                }
                
                # Find best matching topic
                best_match = 'general'
                best_score = 0
                
                for topic, keywords in topic_keywords.items():
                    if topic == 'general':
                        continue
                    matches = sum(1 for keyword in keywords if keyword in text_lower)
                    score = matches / len(keywords) if keywords else 0
                    if score > best_score:
                        best_score = score
                        best_match = topic
                
                # If semantic model available, use it for better detection
                if best_score < 0.3:  # Low confidence
                    # Use semantic similarity to check against known topics
                    topic_descriptions = {
                        'cars': 'automobiles vehicles cars buying selling',
                        'food': 'cooking recipes food ingredients meals',
                        'coding': 'programming code algorithms software development'
                    }
                    
                    best_semantic_match = 'general'
                    best_semantic_score = 0
                    for topic, desc in topic_descriptions.items():
                        query_emb = self.semantic_model.encode(text, convert_to_tensor=False)
                        desc_emb = self.semantic_model.encode(desc, convert_to_tensor=False)
                        import numpy as np
                        similarity = np.dot(query_emb, desc_emb) / (
                            np.linalg.norm(query_emb) * np.linalg.norm(desc_emb)
                        )
                        if similarity > best_semantic_score:
                            best_semantic_score = similarity
                            best_semantic_match = topic
                    
                    if best_semantic_score > 0.4:  # Reasonable threshold
                        best_match = best_semantic_match
                
                return best_match
            else:
                # Fallback to simple keyword matching
                text_lower = text.lower()
                if any(word in text_lower for word in ['car', 'vehicle', 'automobile', 'buy', 'price']):
                    return 'cars'
                elif any(word in text_lower for word in ['food', 'cook', 'recipe', 'ingredient', 'pickle']):
                    return 'food'
                elif any(word in text_lower for word in ['code', 'program', 'algorithm', 'palindrome']):
                    return 'coding'
                return 'general'
        except Exception as e:
            logger.warning(f"Error detecting topic: {e}")
            return 'general'
    
    def _is_topic_relevant(self, query: str, memory_content: str) -> bool:
        """
        Check if memory content is topically relevant to the query using semantic similarity.
        Prevents cross-topic contamination (e.g., pickle vs palindrome code).
        
        Args:
            query: Current user query
            memory_content: Content from memory to check
            
        Returns:
            True if topically relevant, False otherwise
        """
        try:
            # Use semantic similarity if available (much better than keyword matching)
            if self.semantic_model:
                try:
                    # Get embeddings for query and memory content
                    query_embedding = self.semantic_model.encode(query, convert_to_tensor=False)
                    memory_embedding = self.semantic_model.encode(memory_content, convert_to_tensor=False)
                    
                    # Calculate cosine similarity
                    import numpy as np
                    similarity = np.dot(query_embedding, memory_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(memory_embedding)
                    )
                    
                    is_relevant = similarity >= self.topic_relevance_threshold
                    logger.debug(f"Topic relevance: {similarity:.3f} (threshold: {self.topic_relevance_threshold}) - {'RELEVANT' if is_relevant else 'IRRELEVANT'}")
                    return is_relevant
                except Exception as e:
                    logger.warning(f"Error in semantic similarity check: {e}, falling back to keyword matching")
            
            # Fallback to keyword-based matching (simpler but less accurate)
            query_lower = query.lower()
            memory_lower = memory_content.lower()
            
            # Extract key terms from query (2+ character words)
            query_terms = set(word for word in query_lower.split() if len(word) >= 3)
            memory_terms = set(word for word in memory_lower.split() if len(word) >= 3)
            
            # Calculate overlap
            common_terms = query_terms & memory_terms
            if len(query_terms) == 0:
                return True  # Empty query, allow all
            
            overlap_ratio = len(common_terms) / len(query_terms)
            is_relevant = overlap_ratio >= 0.2  # At least 20% term overlap
            
            logger.debug(f"Keyword overlap: {overlap_ratio:.3f} - {'RELEVANT' if is_relevant else 'IRRELEVANT'}")
            return is_relevant
            
        except Exception as e:
            logger.error(f"Error in topic relevance check: {e}", exc_info=True)
            return True  # Default to allowing if check fails
    
    def _recall_conversation_context(
        self,
        session_id: str,
        query: Optional[str] = None,
        limit: int = None,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Recall conversation context from Cortex memory with smart filtering.
        Uses HYBRID approach: semantic search + recency filtering
        
        Args:
            session_id: Session identifier
            query: Optional query for semantic search
            limit: Maximum messages to retrieve
            
        Returns:
            List of message dictionaries with role and content
        """
        try:
            if limit is None:
                limit = self.max_context_messages
            
            if not self.use_cortex or self.memory is None:
                # Fallback: return from simple storage
                messages = self.sessions.get(session_id, [])
                # Filter by topic if specified
                if topic_filter:
                    # Simple keyword filtering for fallback
                    messages = [msg for msg in messages if isinstance(msg, dict) and 
                               self._detect_topic(msg.get('content', '')) == topic_filter]
                return messages[-limit:]
            
            # Get topic-specific memory IDs if topic filtering is enabled
            topic_memory_ids = None
            if topic_filter and session_id in self.topic_contexts:
                topic_memory_ids = self.topic_contexts[session_id].get(topic_filter, [])
                if topic_memory_ids:
                    logger.info(f"📚 Using {len(topic_memory_ids)} memories from topic '{topic_filter}'")
            
            # HYBRID APPROACH: Combine semantic search + recency (within topic)
            if query:
                # Step 1: Get recent messages - ALWAYS include last N messages from session for continuity
                # This ensures conversation flow even when topic changes
                all_session_memory_ids = self.sessions.get(session_id, [])
                recent_count = min(limit, 10)  # Get last 10 messages as baseline
                recent_memories = []
                
                # First, get recent messages from current topic if available
                if topic_memory_ids and len(topic_memory_ids) > 0:
                    # Get last messages from current topic (up to recent_count)
                    topic_recent = topic_memory_ids[-min(recent_count, len(topic_memory_ids)):]
                    for mem_id in topic_recent:
                        mem = self.memory.get_memory(mem_id)
                        if mem and not mem.is_expired():
                            recent_memories.append(mem)
                            logger.debug(f"Added recent message from topic '{topic_filter}': {mem.content[:50]}...")
                
                # Also include very recent messages from session (last 3) for continuity
                # This ensures smooth conversation flow even during topic transitions
                if all_session_memory_ids:
                    very_recent_count = min(3, len(all_session_memory_ids))
                    very_recent_ids = all_session_memory_ids[-very_recent_count:]
                    for mem_id in very_recent_ids:
                        if mem_id not in [m.id for m in recent_memories]:
                            mem = self.memory.get_memory(mem_id)
                            if mem and not mem.is_expired():
                                # Only add if it's the same topic or very recent (within last 3)
                                mem_topic = self._detect_topic(mem.content)
                                if not topic_filter or mem_topic == topic_filter or len(all_session_memory_ids) - all_session_memory_ids.index(mem_id) <= 2:
                                    recent_memories.append(mem)
                                    logger.debug(f"Added very recent message for continuity: {mem.content[:50]}...")
                
                # Step 2: Semantic search for highly relevant older context (within topic)
                # Search within topic-specific memories if available
                search_tags = [f"session:{session_id}", "chat"]
                if topic_memory_ids:
                    # Restrict search to topic-specific memories by including their IDs
                    # We'll filter results to only include topic memories
                    semantic_results = self.memory.recall(
                        query=query,
                        memory_type=MemoryType.SHORT_TERM,
                        limit=limit * 3,  # Search wider since we'll filter by topic
                        min_similarity=0.7,  # Moderate threshold
                        tags=search_tags
                    )
                    # Filter to only include results from current topic
                    semantic_results = [
                        r for r in semantic_results 
                        if r.memory.id in topic_memory_ids
                    ]
                else:
                    semantic_results = self.memory.recall(
                        query=query,
                        memory_type=MemoryType.SHORT_TERM,
                        limit=limit * 2,
                        min_similarity=0.75,
                        tags=search_tags
                    )
                
                # Step 3: Combine and deduplicate
                all_memories = {}
                
                # ALWAYS add recent messages (no filtering) - ensures conversation continuity
                for mem in recent_memories:
                    all_memories[mem.id] = mem
                    logger.debug(f"Included recent message: {mem.content[:50]}...")
                
                # Add semantic matches - filter for topic relevance on older messages
                for result in semantic_results:
                    mem = result.memory
                    if mem.id not in all_memories:
                        # For semantic matches, check topic relevance and similarity
                        is_relevant = True
                        if topic_filter:
                            # Check if memory is from the current topic
                            mem_topic = self._detect_topic(mem.content)
                            is_relevant = mem_topic == topic_filter
                        
                        if is_relevant:
                            # Additional semantic similarity check
                            if result.similarity >= 0.7:  # Moderate threshold
                                all_memories[mem.id] = mem
                                logger.debug(f"Added semantically relevant context: {mem.content[:50]}... (similarity: {result.similarity:.3f})")
                            else:
                                logger.debug(f"Filtered out: similarity too low ({result.similarity:.3f})")
                        else:
                            logger.debug(f"Filtered out: different topic ({mem.content[:50]}...)")
                
                memories = list(all_memories.values())
                
                # Sort by timestamp to maintain chronological order
                try:
                    memories.sort(key=lambda m: m.created_at if hasattr(m, 'created_at') else m.metadata.get('timestamp', ''))
                except:
                    pass
                
            else:
                # No query: just get recent messages - prioritize current topic but include recent for continuity
                all_session_memory_ids = self.sessions.get(session_id, [])
                memories = []
                
                # First, get messages from current topic
                if topic_memory_ids and len(topic_memory_ids) > 0:
                    for mem_id in topic_memory_ids[-limit:]:
                        mem = self.memory.get_memory(mem_id)
                        if mem and not mem.is_expired():
                            memories.append(mem)
                
                # Also include very recent messages (last 3) from session for continuity
                if len(memories) < limit and all_session_memory_ids:
                    very_recent_count = min(3, len(all_session_memory_ids))
                    very_recent_ids = all_session_memory_ids[-very_recent_count:]
                    for mem_id in very_recent_ids:
                        if mem_id not in [m.id for m in memories]:
                            mem = self.memory.get_memory(mem_id)
                            if mem and not mem.is_expired():
                                memories.append(mem)
                
                # If still not enough, get more from session
                if len(memories) < limit and all_session_memory_ids:
                    for mem_id in all_session_memory_ids[-limit*2:]:
                        if len(memories) >= limit:
                            break
                        if mem_id not in [m.id for m in memories]:
                            mem = self.memory.get_memory(mem_id)
                            if mem and not mem.is_expired():
                                if topic_filter:
                                    mem_topic = self._detect_topic(mem.content)
                                    if mem_topic == topic_filter:
                                        memories.append(mem)
                                else:
                                    memories.append(mem)
            
            # Convert memories to message format
            messages = []
            for mem in memories:
                messages.append({
                    "role": mem.metadata.get("role", "user"),
                    "content": mem.content,
                    "timestamp": mem.metadata.get("timestamp"),
                    "memory_id": mem.id
                })
            
            # Sort by timestamp (chronological order)
            messages.sort(key=lambda x: x.get("timestamp", ""))
            
            # ALWAYS summarize old conversations - keep only last 2 messages in full detail
            # This ensures the LLM gets key facts summarized instead of full conversation history
            if len(messages) > 2:
                try:
                    # Split into recent (keep full) and old (summarize)
                    # Always keep only last 2 messages in full, summarize everything before
                    recent_count = min(2, len(messages) - 1)  # Keep last 2 messages full
                    old_messages = messages[:-recent_count] if recent_count > 0 else messages[:-1]
                    recent_messages = messages[-recent_count:] if recent_count > 0 else [messages[-1]]
                    
                    if len(old_messages) > 0:
                        # Create a conversation summary from old messages
                        conversation_text = "\n".join([
                            f"{msg['role'].capitalize()}: {msg['content']}" 
                            for msg in old_messages
                        ])
                        
                        # Extract key facts from old messages - intelligent summarization
                        logger.info(f"📝 Summarizing {len(old_messages)} old messages into concise summary")
                        
                        # Use model summarization if available, otherwise use extractive summarization
                        summary_text = None
                        if self.enable_summarization and self.summarizer:
                            try:
                                summary = self.summarizer(
                                    conversation_text,
                                    max_length=200,  # Longer summary to capture key facts
                                    min_length=30,   # Shorter minimum
                                    do_sample=False
                                )[0]['summary_text']
                                summary_text = summary
                                logger.info(f"✅ Model summarization: '{summary[:100]}...'")
                            except Exception as e:
                                logger.warning(f"Model summarization failed: {e}, using extractive summary")
                        
                        # Fallback to intelligent extractive summarization
                        if not summary_text:
                            key_facts = []
                            # Extract important information from old messages
                            for msg in old_messages:
                                content = msg['content']
                                content_lower = content.lower()
                                
                                # Extract names
                                if 'name is' in content_lower or 'my name' in content_lower or 'i am' in content_lower:
                                    key_facts.append(content)
                                # Extract preferences, important statements
                                elif msg['role'] == 'user' and (len(content) < 150 or any(word in content_lower for word in ['like', 'prefer', 'want', 'need', 'important', 'favorite'])):
                                    key_facts.append(content)
                                # Extract assistant responses that contain important information
                                elif msg['role'] == 'assistant' and len(content) < 100:
                                    # Short assistant responses might be key facts
                                    key_facts.append(content)
                            
                            # If we found key facts, join them
                            if key_facts:
                                summary_text = ". ".join(key_facts[:5])  # Max 5 key facts
                                logger.info(f"✅ Extractive summary: '{summary_text[:100]}...'")
                            else:
                                # Create a general summary
                                user_msgs = [m['content'] for m in old_messages if m['role'] == 'user']
                                assistant_msgs = [m['content'] for m in old_messages if m['role'] == 'assistant']
                                summary_parts = []
                                if user_msgs:
                                    summary_parts.append(f"User discussed: {user_msgs[0][:80]}{'...' if len(user_msgs[0]) > 80 else ''}")
                                if assistant_msgs:
                                    summary_parts.append(f"Assistant responded about: {assistant_msgs[0][:80]}{'...' if len(assistant_msgs[0]) > 80 else ''}")
                                summary_text = ". ".join(summary_parts) if summary_parts else "Previous conversation occurred"
                                logger.info(f"✅ General summary: '{summary_text[:100]}...'")
                        
                        # Add summary as a single message with key facts
                        if summary_text:
                            summary_message = {
                                "role": "system",
                                "content": f"Key facts from previous conversation: {summary_text}",
                                "timestamp": old_messages[-1].get("timestamp", "") if old_messages else "",
                                "memory_id": "summary",
                                "is_summary": True
                            }
                            messages = [summary_message] + recent_messages
                            logger.info(f"✅ Summarized {len(old_messages)} messages, kept {len(recent_messages)} recent messages")
                        else:
                            messages = recent_messages
                    else:
                        messages = recent_messages if recent_messages else messages[-limit:]
                except Exception as e:
                    logger.warning(f"Failed to summarize context: {e}. Using full context.")
                    messages = messages[-limit:]
            elif len(messages) > limit:
                # If summarization not available, just limit
                messages = messages[-limit:]
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to recall conversation context: {e}", exc_info=True)
            return []
    
    def generate_response(
        self,
        user_message: str,
        session_id: str = "default",
        use_semantic_context: bool = True,
        use_answer_cache: bool = True,
        use_fresh_llm: bool = True
    ) -> Dict[str, any]:
        """
        Generate a response using Llama with Cortex memory context.
        Includes SMART CACHING: Returns cached answer for highly similar questions.
        
        Args:
            user_message: User's input message
            session_id: Session identifier for conversation tracking
            use_semantic_context: Whether to use semantic search for context
            
        Returns:
            Dictionary with:
                - response: Bot's response text
                - context_used: Number of messages from memory
                - context_messages: List of context messages used
                - source: "cortex_memory", "cached_answer", or "no_context"
                - cached: True if answer was from cache
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()
            
            # SMART CACHING: Check if we have a VERY similar recent question (if enabled)
            # PRIORITY: Cache takes precedence over LLM when both are enabled
            if use_answer_cache and self.use_cortex and self.memory:
                cached_result = self._check_answer_cache(user_message, session_id)
                if cached_result:
                    logger.info("=" * 80)
                    logger.info(f"💾 USING CACHED RESPONSE - Session: {session_id}")
                    logger.info(f"📝 User Message: {user_message}")
                    logger.info(f"🎯 Cache Similarity: {cached_result.get('cache_similarity', 0):.2%}")
                    logger.info(f"📥 Cached Response: {cached_result.get('response', '')[:200]}{'...' if len(cached_result.get('response', '')) > 200 else ''}")
                    logger.info("=" * 80)
                    # Add prompt info to cached result (None since no LLM call was made)
                    cached_result['prompt_sent_to_llm'] = None
                    cached_result['user_message'] = user_message
                    return cached_result
            
            # Detect topic for current message
            current_topic = self._detect_topic(user_message)
            previous_topic = self.session_topics.get(session_id, None)
            
            # If topic is generic and we have a previous topic, check if it's a continuation
            if current_topic == 'general' and previous_topic and previous_topic != 'general':
                # Check if message seems like a continuation (questions like "can you make a plan", "how about", etc.)
                continuation_phrases = ['can you', 'how about', 'what about', 'tell me', 'give me', 'make', 'suggest', 'which', 'what']
                if any(phrase in user_message.lower() for phrase in continuation_phrases):
                    # Likely a continuation of previous topic
                    current_topic = previous_topic
                    logger.info(f"📎 Detected continuation of '{previous_topic}' topic: {user_message[:50]}...")
                else:
                    # Might be a new topic, use semantic similarity to check
                    if self.semantic_model and len(self.sessions.get(session_id, [])) > 0:
                        # Get last message to check similarity
                        last_mem_id = self.sessions[session_id][-1]
                        last_mem = self.memory.get_memory(last_mem_id) if self.memory else None
                        if last_mem:
                            import numpy as np
                            query_emb = self.semantic_model.encode(user_message, convert_to_tensor=False)
                            last_emb = self.semantic_model.encode(last_mem.content, convert_to_tensor=False)
                            similarity = np.dot(query_emb, last_emb) / (
                                np.linalg.norm(query_emb) * np.linalg.norm(last_emb)
                            )
                            if similarity > 0.5:  # Moderate similarity threshold
                                current_topic = previous_topic
                                logger.info(f"📎 Semantic similarity ({similarity:.3f}) suggests continuation of '{previous_topic}' topic")
            
            # Track topic change
            topic_changed = previous_topic is not None and previous_topic != current_topic and previous_topic != 'general'
            if topic_changed:
                logger.info(f"🔄 Topic changed: '{previous_topic}' -> '{current_topic}' (session: {session_id})")
            elif previous_topic is None:
                logger.info(f"📌 New topic detected: '{current_topic}' (session: {session_id})")
            elif current_topic == previous_topic:
                logger.debug(f"📌 Continuing topic: '{current_topic}' (session: {session_id})")
            
            # Update session topic
            self.session_topics[session_id] = current_topic
            
            # Initialize topic context tracking if needed
            if session_id not in self.topic_contexts:
                self.topic_contexts[session_id] = {}
            if current_topic not in self.topic_contexts[session_id]:
                self.topic_contexts[session_id][current_topic] = []
            
            # Store user message in memory
            memory_id = self._store_message(
                session_id=session_id,
                role="user",
                content=user_message,
                priority=MemoryPriority.MEDIUM
            )
            
            # Track this message in topic context
            if memory_id:
                self.topic_contexts[session_id][current_topic].append(memory_id)
            
            # Recall conversation context (if enabled)
            # Focus on current topic but include relevant context from current topic history
            if use_semantic_context:
                # Get context from current topic
                context_messages = self._recall_conversation_context(
                    session_id=session_id,
                    query=user_message,
                    limit=self.max_context_messages,
                    topic_filter=current_topic  # Only get context from current topic
                )
            else:
                # Get recent messages from current topic only
                context_messages = self._recall_conversation_context(
                    session_id=session_id,
                    limit=self.max_context_messages,
                    topic_filter=current_topic  # Only get context from current topic
                )
            
            # Build prompt with context
            prompt = self._build_prompt(context_messages, user_message)
            
            # Log what we're sending to the LLM
            logger.info("=" * 80)
            logger.info(f"🤖 LLM REQUEST - Session: {session_id}")
            logger.info(f"📝 User Message: {user_message}")
            logger.info(f"🏷️  Current Topic: {current_topic}")
            if topic_changed:
                logger.info(f"🔄 Topic Changed: {previous_topic} -> {current_topic}")
            logger.info(f"📚 Context Messages Used: {len(context_messages)}")
            if context_messages:
                logger.info("📋 Context History (showing ALL):")
                for i, msg in enumerate(context_messages, 1):
                    msg_role = msg.get('role', 'unknown')
                    msg_content = msg.get('content', '')
                    msg_topic = self._detect_topic(msg_content) if msg_content else 'unknown'
                    logger.info(f"   {i}. [{msg_role}] ({msg_topic}): {msg_content[:80]}{'...' if len(msg_content) > 80 else ''}")
            else:
                logger.warning("⚠️  No context messages found!")
            logger.info("-" * 80)
            logger.info("📤 FULL PROMPT SENT TO LLM:")
            logger.info(prompt)
            logger.info("=" * 80)
            
            # Generate response (if fresh_llm is enabled)
            if use_fresh_llm:
                logger.info(f"🔄 Generating response for session {session_id}")
                response = self.model(
                    prompt,
                    max_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    stop=["User:", "\n\n"],
                    echo=False
                )
                bot_response = response['choices'][0]['text'].strip()
                logger.info("✅ LLM RESPONSE RECEIVED:")
                logger.info(f"📥 Response: {bot_response[:200]}{'...' if len(bot_response) > 200 else ''}")
            else:
                # Return a simple response when LLM is disabled
                bot_response = "I'm currently in a limited mode. Please enable the LLM to get a full response."
            
            # Store bot response in memory
            response_memory_id = self._store_message(
                session_id=session_id,
                role="assistant",
                content=bot_response,
                priority=MemoryPriority.MEDIUM
            )
            
            # Track response in topic context
            if response_memory_id and session_id in self.topic_contexts:
                current_topic = self.session_topics.get(session_id, 'general')
                if current_topic not in self.topic_contexts[session_id]:
                    self.topic_contexts[session_id][current_topic] = []
                self.topic_contexts[session_id][current_topic].append(response_memory_id)
            
            logger.info(f"Response generated successfully for session {session_id}")
            
            # Return detailed response with context information
            return {
                "response": bot_response,
                "context_used": len(context_messages),
                "context_messages": context_messages,
                "source": "cortex_memory" if self.use_cortex and context_messages else "no_context",
                "prompt_sent_to_llm": prompt if use_fresh_llm else None,
                "user_message": user_message,
                "topic": current_topic,
                "topic_changed": topic_changed
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "context_used": 0,
                "context_messages": [],
                "source": "error"
            }
    
    def _build_prompt(
        self,
        context_messages: List[Dict[str, str]],
        current_message: str
    ) -> str:
        """
        Build a prompt with conversation context.
        Summaries are included as system messages with key facts.
        
        Args:
            context_messages: Previous conversation messages (may include summaries)
            current_message: Current user message
            
        Returns:
            Formatted prompt
        """
        # System prompt
        prompt = """You are a helpful AI assistant. You provide clear, accurate, and friendly responses.

"""
        
        # Add conversation context
        if context_messages:
            # Check if there's a summary
            has_summary = any(msg.get('is_summary', False) for msg in context_messages)
            
            if has_summary:
                # Include summary as key facts
                for msg in context_messages:
                    if msg.get('is_summary', False):
                        prompt += f"{msg['content']}\n\n"
                        break
                
                # Add recent conversation
                recent_messages = [msg for msg in context_messages if not msg.get('is_summary', False)]
                if recent_messages:
                    prompt += "Recent conversation:\n"
                    for msg in recent_messages:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        prompt += f"{role}: {msg['content']}\n"
                    prompt += "\n"
            else:
                # No summary, show all context as conversation
                prompt += "Previous conversation:\n"
                for msg in context_messages:
                    role = "User" if msg["role"] == "user" else ("Assistant" if msg["role"] == "assistant" else "System")
                    prompt += f"{role}: {msg['content']}\n"
                prompt += "\n"
        
        # Add current message
        prompt += f"User: {current_message}\nAssistant:"
        
        return prompt
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """
        Get full conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        return self._recall_conversation_context(session_id, limit=limit)
    
    def summarize_conversation(self, session_id: str) -> str:
        """
        Generate a summary of the conversation using Cortex summarization.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation summary
        """
        try:
            if not self.use_cortex or self.memory is None:
                return "Summary feature requires Cortex SDK"
            
            summary = self.memory.summarize(
                tags=[f"session:{session_id}", "chat"]
            )
            return summary.summary_text
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}", exc_info=True)
            return "Unable to generate summary."
    
    def clear_session(self, session_id: str) -> int:
        """
        Clear all messages for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of messages cleared
        """
        try:
            if not self.use_cortex or self.memory is None:
                # Fallback: clear from simple storage
                count = len(self.sessions.get(session_id, []))
                if session_id in self.sessions:
                    del self.sessions[session_id]
                return count
            
            memory_ids = self.sessions.get(session_id, [])
            count = 0
            for mem_id in memory_ids:
                if self.memory.delete_memory(mem_id):
                    count += 1
            
            # Clear session tracking
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            logger.info(f"Cleared {count} messages from session {session_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}", exc_info=True)
            return 0
    
    def get_memory_stats(self) -> Dict:
        """
        Get statistics about memory usage.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self.use_cortex or self.memory is None:
            # Fallback stats
            total_messages = sum(len(msgs) for msgs in self.sessions.values())
            return {
                "total_memories": total_messages,
                "short_term_count": total_messages,
                "total_sessions": len(self.sessions),
                "cortex_enabled": False
            }
        
        stats = self.memory.get_stats()
        return {
            "total_memories": stats.total_memories,
            "short_term_count": stats.short_term_count,
            "total_sessions": len(self.sessions),
            "oldest_memory": stats.oldest_memory.isoformat() if stats.oldest_memory else None,
            "newest_memory": stats.newest_memory.isoformat() if stats.newest_memory else None,
            "cortex_enabled": True
        }

