#!/usr/bin/env python3
"""
Flask App with Cortex-Powered Chat Bot
Integrates Llama chatbot with Cortex SDK for intelligent memory management
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
import logging as log

# Configure logging
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the rag_model path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Cortex-powered chat bot
try:
    from rag_model.src_gpt.cortex_chat import CortexChatBot, CORTEX_AVAILABLE
    CHAT_BOT_AVAILABLE = True
    log.info("Cortex chat bot module imported successfully")
    log.info(f"Cortex SDK available: {CORTEX_AVAILABLE}")
except Exception as e:
    log.error(f"Failed to import chat bot: {str(e)}")
    CHAT_BOT_AVAILABLE = False
    CORTEX_AVAILABLE = False

app = Flask(__name__)

# Initialize chat bot (lazy loading)
chat_bot = None

def get_chat_bot():
    """Lazy initialization of the chat bot."""
    global chat_bot
    if chat_bot is None and CHAT_BOT_AVAILABLE:
        try:
            # Path to the Llama model
            model_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'rag_model',
                'foundation_model',
                'llama-2-7b-chat-hf-q2_k.gguf'
            )
            
            chat_bot = CortexChatBot(
                model_path=model_path,
                max_context_messages=10,
                use_cortex=True  # Enable Cortex SDK integration
            )
            chat_bot.load_model()
            log.info("Cortex-powered chat bot initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize chat bot: {str(e)}", exc_info=True)
            return None
    return chat_bot

@app.route('/')
def index():
    """Render the chat interface."""
    return render_template('index.html', title="AI Assistant")

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for the AI assistant with Cortex memory."""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'status': 'error', 'error': 'No message provided'})
        
        # Get the chat bot
        bot = get_chat_bot()
        if bot is None:
            return jsonify({
                'status': 'error', 
                'error': 'Chat bot not available. Please check server logs.'
            })
        
        # Generate response with Cortex memory context
        result = bot.generate_response(
            user_message=user_message,
            session_id=session_id,
            use_semantic_context=True  # Use semantic search for relevant context
        )
        
        log.info(f"Chat response generated for session {session_id}")
        
        return jsonify({
            'status': 'success',
            'response': result['response'],
            'session_id': session_id,
            'cortex_enabled': bot.use_cortex,
            'context_used': result.get('context_used', 0),
            'memory_source': result.get('source', 'unknown'),
            'context_messages': [
                {'role': msg['role'], 'content': msg['content'][:100] + '...' if len(msg['content']) > 100 else msg['content']}
                for msg in result.get('context_messages', [])
            ]
        })
        
    except Exception as e:
        log.error(f"Error in chat: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session from Cortex memory."""
    try:
        bot = get_chat_bot()
        if bot is None:
            return jsonify({'status': 'error', 'error': 'Chat bot not available'})
        
        # Get history from Cortex memory
        history = bot.get_conversation_history(session_id, limit=50)
        
        return jsonify({
            'status': 'success',
            'history': history,
            'cortex_enabled': bot.use_cortex
        })
    except Exception as e:
        log.error(f"Error getting chat history: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/chat/summarize/<session_id>', methods=['GET'])
def summarize_conversation(session_id):
    """Generate a summary of the conversation using Cortex."""
    try:
        bot = get_chat_bot()
        if bot is None or not bot.use_cortex:
            return jsonify({'status': 'error', 'error': 'Cortex not available'})
        
        summary = bot.summarize_conversation(session_id)
        
        return jsonify({
            'status': 'success',
            'summary': summary,
            'session_id': session_id
        })
    except Exception as e:
        log.error(f"Error summarizing conversation: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/chat/clear/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Clear chat history for a session."""
    try:
        bot = get_chat_bot()
        if bot is None:
            return jsonify({'status': 'error', 'error': 'Chat bot not available'})
        
        count = bot.clear_session(session_id)
        
        return jsonify({
            'status': 'success',
            'messages_cleared': count,
            'session_id': session_id
        })
    except Exception as e:
        log.error(f"Error clearing session: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/memory/stats', methods=['GET'])
def memory_stats():
    """Get Cortex memory statistics."""
    try:
        bot = get_chat_bot()
        if bot is None or not bot.use_cortex:
            return jsonify({'status': 'error', 'error': 'Cortex not available'})
        
        stats = bot.get_memory_stats()
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        log.error(f"Error getting memory stats: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'success',
        'chat_bot_available': CHAT_BOT_AVAILABLE,
        'cortex_available': CORTEX_AVAILABLE,
        'message': 'AI Assistant server is running with Cortex SDK'
    })

if __name__ == '__main__':
    try:
        log.info("Starting AI Assistant with Cortex SDK integration...")
        log.info(f"Chat bot available: {CHAT_BOT_AVAILABLE}")
        log.info(f"Cortex SDK available: {CORTEX_AVAILABLE}")
        app.run(host="0.0.0.0", debug=True, port=5001, use_reloader=False)
    except Exception as e:
        log.error(f"Error starting Flask app: {str(e)}")
    finally:
        log.info("Application has shut down.")
