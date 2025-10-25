#!/usr/bin/env python3
"""
AIMap Chat Bot Startup Script
This script starts the chat bot application
"""

import os
import sys
import subprocess

def main():
    print("🤖 Starting AI Assistant...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app/simple_app.py'):
        print("❌ Error: Please run this script from the Chat_bot directory")
        print("Expected structure: Chat_bot/start_chatbot.py")
        sys.exit(1)
    
    # Check if model file exists
    model_path = 'rag_model/foundation_model/llama-2-7b-chat-hf-q2_k.gguf'
    if not os.path.exists(model_path):
        print(f"❌ Error: Model file not found at {model_path}")
        print("Please ensure the Llama model file is in the correct location")
        sys.exit(1)
    
    print("✅ Model file found")
    print("✅ Starting Flask application...")
    print("\n🚀 AI Assistant will be available at: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Change to app directory and run the Flask app
    os.chdir('app')
    try:
        subprocess.run([sys.executable, 'simple_app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 AI Assistant stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting AI Assistant: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
