#!/usr/bin/env python3
"""
Chat Bot Setup Script
Downloads required model and installs dependencies
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def download_model():
    """Download the Llama model"""
    print("🤖 Downloading Llama-2-7B model...")
    try:
        subprocess.run([sys.executable, "download_model.py"], check=True)
        print("✅ Model setup complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading model: {e}")
        print("Please run 'python download_model.py' manually")
        sys.exit(1)

def main():
    print("🚀 Setting up AI Chat Bot...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/simple_app.py"):
        print("❌ Error: Please run this script from the Chat_bot directory")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Download model
    download_model()
    
    print("\n🎉 Setup complete!")
    print("Run 'python start_chatbot.py' to start the chat bot")
    print("=" * 50)

if __name__ == "__main__":
    main()
