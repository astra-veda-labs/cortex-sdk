#!/usr/bin/env python3
"""
Interactive Chat Bot using Llama-2-7B
A working chat bot for semiconductor manufacturing discussions
"""

import os
import sys
from llama_cpp import Llama

class AIMapChatBot:
    def __init__(self):
        self.llm = None
        self.load_model()
    
    def load_model(self):
        """Load the Llama model"""
        project_root = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(project_root, "../foundation_model/llama-2-7b-chat-hf-q2_k.gguf")
        
        print(f"🔍 Loading model from: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        print("🔄 Loading Llama-2-7B model... (this may take a moment)")
        
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,        # Context window
                n_threads=4,       # Number of CPU threads
                n_gpu_layers=0,    # Set to 0 for CPU-only
                verbose=False      # Reduce output verbosity
            )
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
            sys.exit(1)
    
    def generate_response(self, user_input):
        """Generate response using the loaded model"""
        try:
            # Create a conversational prompt
            prompt = f"Human: {user_input}\nAssistant:"
            
            response = self.llm(
                prompt,
                max_tokens=300,     # Increased token limit for better responses
                temperature=0.7,    # Creativity level
                top_p=0.9,         # Nucleus sampling
                stop=["Human:", "\n\nHuman:", "Human"],  # Stop tokens
                echo=False         # Don't echo the prompt
            )
            
            return response["choices"][0]["text"].strip()
        
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def start_chat(self):
        """Start the interactive chat session"""
        print("\n" + "="*60)
        print("🤖 AIMap Chat Bot - Powered by Llama-2-7B")
        print("="*60)
        print("💡 Specialized in semiconductor manufacturing and etching")
        print("💡 Type 'quit', 'exit', or 'bye' to end the conversation")
        print("💡 Type 'help' for usage tips")
        print("="*60)
        
        conversation_count = 0
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n👤 You: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("\n👋 Goodbye! Thanks for chatting with AIMap!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if not user_input:
                    print("Please enter a question or message.")
                    continue
                
                # Generate and display response
                print("\n🤖 AIMap Bot: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(response)
                
                conversation_count += 1
                
                # Show conversation count every 5 exchanges
                if conversation_count % 5 == 0:
                    print(f"\n💬 Conversation exchanges: {conversation_count}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Chat ended. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print("Please try again or type 'quit' to exit.")
    
    def show_help(self):
        """Show help information"""
        print("\n" + "="*50)
        print("📚 AIMap Chat Bot Help")
        print("="*50)
        print("🎯 This bot specializes in:")
        print("   • Semiconductor manufacturing")
        print("   • Etching processes and techniques")
        print("   • Photolithography")
        print("   • Material science")
        print("   • General technical questions")
        print("\n💡 Example questions you can ask:")
        print("   • 'What is plasma etching?'")
        print("   • 'Explain the difference between wet and dry etching'")
        print("   • 'How does photolithography work?'")
        print("   • 'What are the advantages of ICP etching?'")
        print("\n🔧 Commands:")
        print("   • 'help' - Show this help message")
        print("   • 'quit', 'exit', 'bye' - End the conversation")
        print("="*50)

def main():
    """Main function"""
    try:
        # Create and start the chat bot
        bot = AIMapChatBot()
        bot.start_chat()
    except Exception as e:
        print(f"❌ Failed to start chat bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
