#!/usr/bin/env python3
"""
Simplified Flask App with Chat Bot Integration
This version avoids dependency conflicts and focuses on the chat functionality
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
import logging as log
import uuid
from collections import defaultdict

# Configure logging
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the rag_model path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the chat bot
try:
    from rag_model.src_gpt.interactive_chat import AIMapChatBot
    CHAT_BOT_AVAILABLE = True
    log.info("Chat bot module imported successfully")
except Exception as e:
    log.error(f"Failed to import chat bot: {str(e)}")
    CHAT_BOT_AVAILABLE = False

app = Flask(__name__)

# Chat history management
chat_histories = defaultdict(list)

def get_history(session_id):
    return chat_histories.get(session_id, [])

def append_history(session_id, speaker, message):
    chat_histories[session_id].append((speaker, message))
    if len(chat_histories[session_id]) > 20:
        chat_histories[session_id] = chat_histories[session_id][-20:]

# Initialize chat bot
chat_bot = None

def get_chat_bot():
    global chat_bot
    if chat_bot is None and CHAT_BOT_AVAILABLE:
        try:
            chat_bot = AIMapChatBot()
            log.info("Chat bot initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize chat bot: {str(e)}")
            return None
    return chat_bot

@app.route('/')
def index():
    return render_template('index.html', title="AI Assistant")

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for the AI assistant"""
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
        
        # Generate response
        response = bot.generate_response(user_message)
        
        # Store in chat history
        append_history(session_id, "user", user_message)
        append_history(session_id, "assistant", response)
        
        log.info(f"Chat response generated for session {session_id}")
        
        return jsonify({
            'status': 'success',
            'response': response,
            'session_id': session_id
        })
        
    except Exception as e:
        log.error(f"Error in chat: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        history = get_history(session_id)
        return jsonify({
            'status': 'success',
            'history': history
        })
    except Exception as e:
        log.error(f"Error getting chat history: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'chat_bot_available': CHAT_BOT_AVAILABLE,
        'message': 'AI Assistant server is running'
    })

if __name__ == '__main__':
    try:
        log.info("Starting AI Assistant Flask app...")
        log.info(f"Chat bot available: {CHAT_BOT_AVAILABLE}")
        app.run(host="0.0.0.0", debug=True, port=5001, use_reloader=False)
    except Exception as e:
        log.error(f"Error starting Flask app: {str(e)}")
    finally:
        log.info("Application has shut down.")
