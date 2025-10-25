#!/usr/bin/env python3
"""
Model Download Script
Downloads the Llama-2-7B model if not present
"""

import os
import sys
from huggingface_hub import hf_hub_download

def download_model():
    """Download the Llama-2-7B model"""
    model_dir = "rag_model/foundation_model"
    model_file = "llama-2-7b-chat-hf-q2_k.gguf"
    model_path = os.path.join(model_dir, model_file)
    
    # Create directory if it doesn't exist
    os.makedirs(model_dir, exist_ok=True)
    
    # Check if model already exists
    if os.path.exists(model_path):
        print(f"✅ Model already exists at: {model_path}")
        return model_path
    
    print("🔄 Downloading Llama-2-7B model...")
    print("This may take several minutes depending on your internet connection...")
    
    try:
        # Download from Hugging Face
        downloaded_path = hf_hub_download(
            repo_id="TheBloke/Llama-2-7B-Chat-GGUF",
            filename=model_file,
            cache_dir=model_dir
        )
        
        print(f"✅ Model downloaded successfully to: {downloaded_path}")
        return downloaded_path
        
    except Exception as e:
        print(f"❌ Error downloading model: {str(e)}")
        print("\nAlternative: You can manually download the model from:")
        print("https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF")
        print(f"And place it at: {model_path}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()