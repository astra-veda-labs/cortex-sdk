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

logger = logging.getLogger(__name__)


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
        use_cortex: bool = True
    ):
        """
        Initialize Cortex-powered chatbot.
        
        Args:
            model_path: Path to the Llama model file
            memory_config: Cortex memory configuration (optional)
            max_context_messages: Maximum messages to include in context
            use_cortex: Whether to use Cortex SDK for memory management
        """
        self.model_path = model_path
        self.model = None
        self.max_context_messages = max_context_messages
        self.use_cortex = use_cortex and CORTEX_AVAILABLE
        
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
    
    def _recall_conversation_context(
        self,
        session_id: str,
        query: Optional[str] = None,
        limit: int = None
    ) -> List[Dict[str, str]]:
        """
        Recall conversation context from Cortex memory or fallback storage.
        
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
                return messages[-limit:]
            
            # Get session-specific memories from Cortex
            if query:
                # Semantic search for relevant context
                results = self.memory.recall(
                    query=query,
                    memory_type=MemoryType.SHORT_TERM,
                    limit=limit,
                    min_similarity=0.3,
                    tags=[f"session:{session_id}", "chat"]
                )
                memories = [r.memory for r in results]
            else:
                # Get recent messages from session
                memory_ids = self.sessions.get(session_id, [])
                memories = []
                for mem_id in memory_ids[-limit:]:  # Get most recent
                    mem = self.memory.get_memory(mem_id)
                    if mem and not mem.is_expired():
                        memories.append(mem)
            
            # Convert memories to message format
            messages = []
            for mem in memories:
                messages.append({
                    "role": mem.metadata.get("role", "user"),
                    "content": mem.content,
                    "timestamp": mem.metadata.get("timestamp")
                })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x.get("timestamp", ""))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to recall conversation context: {e}", exc_info=True)
            return []
    
    def generate_response(
        self,
        user_message: str,
        session_id: str = "default",
        use_semantic_context: bool = True
    ) -> Dict[str, any]:
        """
        Generate a response using Llama with Cortex memory context.
        
        Args:
            user_message: User's input message
            session_id: Session identifier for conversation tracking
            use_semantic_context: Whether to use semantic search for context
            
        Returns:
            Dictionary with:
                - response: Bot's response text
                - context_used: Number of messages from memory
                - context_messages: List of context messages used
                - source: "cortex_memory" or "no_context"
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                self.load_model()
            
            # Store user message in memory
            self._store_message(
                session_id=session_id,
                role="user",
                content=user_message,
                priority=MemoryPriority.MEDIUM
            )
            
            # Recall conversation context
            if use_semantic_context:
                # Use semantic search to find relevant context
                context_messages = self._recall_conversation_context(
                    session_id=session_id,
                    query=user_message,
                    limit=self.max_context_messages
                )
            else:
                # Get recent messages
                context_messages = self._recall_conversation_context(
                    session_id=session_id,
                    limit=self.max_context_messages
                )
            
            # Build prompt with context
            prompt = self._build_prompt(context_messages, user_message)
            
            # Generate response
            logger.info(f"Generating response for session {session_id}")
            response = self.model(
                prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9,
                stop=["User:", "\n\n"],
                echo=False
            )
            
            bot_response = response['choices'][0]['text'].strip()
            
            # Store bot response in memory
            self._store_message(
                session_id=session_id,
                role="assistant",
                content=bot_response,
                priority=MemoryPriority.MEDIUM
            )
            
            logger.info(f"Response generated successfully for session {session_id}")
            
            # Return detailed response with context information
            return {
                "response": bot_response,
                "context_used": len(context_messages),
                "context_messages": context_messages,
                "source": "cortex_memory" if self.use_cortex and context_messages else "no_context"
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
        
        Args:
            context_messages: Previous conversation messages
            current_message: Current user message
            
        Returns:
            Formatted prompt
        """
        # System prompt
        prompt = """You are a helpful AI assistant. You provide clear, accurate, and friendly responses.

"""
        
        # Add conversation context
        if context_messages:
            prompt += "Previous conversation:\n"
            for msg in context_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
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

