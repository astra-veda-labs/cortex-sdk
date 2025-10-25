#!/usr/bin/env python3
"""
AI Chat Bot Setup Script
Complete setup including dependencies and model download
"""

import os
import sys
import subprocess
import shutil

def install_dependencies():
    """Install required Python packages and Cortex SDK"""
    print("📦 Installing dependencies...")
    try:
        # Install regular dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        
        # Install Cortex SDK in development mode
        cortex_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if os.path.exists(os.path.join(cortex_path, "setup.py")):
            print("📦 Installing Cortex SDK (local development mode)...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", cortex_path], check=True)
            print("✅ Cortex SDK installed successfully")
        else:
            print("⚠️  Cortex SDK not found locally, skipping...")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def check_model_exists():
    """Check if model file already exists"""
    model_path = "rag_model/foundation_model/llama-2-7b-chat-hf-q2_k.gguf"
    if os.path.exists(model_path):
        print(f"✅ Model already exists at: {model_path}")
        return True
    return False

def copy_from_aimap():
    """Copy model from existing AIMap installation"""
    source_path = "/Users/manishb/Desktop/Coding/AIMap-release_one-dev/src/rag_model/foundation_model/llama-2-7b-chat-hf-q2_k.gguf"
    dest_dir = "rag_model/foundation_model"
    dest_path = os.path.join(dest_dir, "llama-2-7b-chat-hf-q2_k.gguf")
    
    print("🔍 Looking for existing model in AIMap...")
    
    if not os.path.exists(source_path):
        print("❌ AIMap model not found")
        return False
    
    os.makedirs(dest_dir, exist_ok=True)
    
    if os.path.exists(dest_path):
        print("✅ Model already exists at destination")
        return True
    
    try:
        print("🔄 Copying model (2.5GB) - this may take a moment...")
        shutil.copy2(source_path, dest_path)
        
        if os.path.exists(dest_path):
            source_size = os.path.getsize(source_path)
            dest_size = os.path.getsize(dest_path)
            
            if source_size == dest_size:
                print(f"✅ Model copied successfully! ({dest_size / (1024**3):.2f} GB)")
                return True
            else:
                print("❌ Copy verification failed")
                return False
        else:
            print("❌ Copy failed")
            return False
            
    except Exception as e:
        print(f"❌ Error copying model: {str(e)}")
        return False

def download_from_huggingface():
    """Download model using huggingface_hub"""
    print("🔄 Downloading from Hugging Face...")
    try:
        from huggingface_hub import hf_hub_download
        
        os.makedirs("rag_model/foundation_model", exist_ok=True)
        
        downloaded_path = hf_hub_download(
            repo_id="TheBloke/Llama-2-7B-Chat-GGUF",
            filename="llama-2-7b-chat-hf-q2_k.gguf",
            cache_dir="rag_model/foundation_model"
        )
        
        print(f"✅ Model downloaded successfully to: {downloaded_path}")
        return True
        
    except ImportError:
        print("❌ huggingface_hub not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
            return download_from_huggingface()  # Retry after installation
        except:
            print("❌ Failed to install huggingface_hub")
            return False
    except Exception as e:
        print(f"❌ Error downloading model: {str(e)}")
        return False

def download_with_curl():
    """Download model using curl"""
    print("🔄 Downloading using curl...")
    
    url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat-hf-q2_k.gguf"
    output_path = "rag_model/foundation_model/llama-2-7b-chat-hf-q2_k.gguf"
    
    os.makedirs("rag_model/foundation_model", exist_ok=True)
    
    try:
        print("📥 Downloading model (2.5GB) - this may take several minutes...")
        subprocess.run([
            "curl", "-L", "-o", output_path, url
        ], check=True)
        
        print(f"✅ Model downloaded successfully to: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading with curl: {str(e)}")
        return False
    except FileNotFoundError:
        print("❌ curl not found")
        return False

def setup_model():
    """Setup the model file using the best available method"""
    if check_model_exists():
        return True
    
    print("\n📋 Model file required (2.5GB). Trying different methods:\n")
    
    # Try copying from AIMap first (fastest)
    if copy_from_aimap():
        return True
    
    # Try downloading from Hugging Face
    if download_from_huggingface():
        return True
    
    # Try curl as fallback
    if download_with_curl():
        return True
    
    # Manual instructions
    print("\n❌ All automatic methods failed.")
    print("📋 Manual setup required:")
    print("1. Visit: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF")
    print("2. Download: llama-2-7b-chat-hf-q2_k.gguf (2.5GB)")
    print("3. Place it in: Chat_bot/rag_model/foundation_model/")
    print("4. Run: python start_chatbot.py")
    return False

def main():
    print("🤖 AI Chat Bot - Complete Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/simple_app.py"):
        print("❌ Error: Please run this script from the Chat_bot directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Setup model
    if not setup_model():
        print("❌ Setup failed at model setup")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("Run 'python start_chatbot.py' to start the chat bot")
    print("=" * 50)

if __name__ == "__main__":
    main()
