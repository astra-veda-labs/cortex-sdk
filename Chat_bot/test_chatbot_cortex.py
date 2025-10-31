#!/usr/bin/env python3
"""
Test Suite for Chat_bot with Cortex SDK Integration
Tests memory management, context recall, and conversation flow
"""

import sys
import os
import time
import requests
import json
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:5001"
TEST_SESSION_ID = "test_session_cortex_001"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")


def print_test(test_name: str):
    """Print test name"""
    print(f"{Colors.BOLD}{Colors.BLUE}[TEST]{Colors.END} {test_name}")


def print_pass(message: str):
    """Print pass message"""
    print(f"  {Colors.GREEN}✓ PASS:{Colors.END} {message}")


def print_fail(message: str):
    """Print fail message"""
    print(f"  {Colors.RED}✗ FAIL:{Colors.END} {message}")


def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.YELLOW}ℹ INFO:{Colors.END} {message}")


class ChatBotTester:
    """Test suite for Chat_bot with Cortex integration"""
    
    def __init__(self, base_url: str = BASE_URL):
        """Initialize tester"""
        self.base_url = base_url
        self.session_id = TEST_SESSION_ID
        self.tests_passed = 0
        self.tests_failed = 0
    
    def check_server(self) -> bool:
        """Check if server is running"""
        print_test("Server Health Check")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                print_pass(f"Server is running")
                print_info(f"Chat bot available: {data.get('chat_bot_available')}")
                print_info(f"Cortex available: {data.get('cortex_available')}")
                return True
            else:
                print_fail(f"Server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print_fail("Cannot connect to server. Is it running?")
            print_info(f"Start server: cd Chat_bot && python start_chatbot.py")
            return False
        except Exception as e:
            print_fail(f"Error: {e}")
            return False
    
    def send_message(self, message: str, session_id: str = None) -> Dict:
        """Send a message to the chatbot"""
        if session_id is None:
            session_id = self.session_id
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"message": message, "session_id": session_id},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def test_basic_conversation(self):
        """Test 1: Basic conversation"""
        print_test("Basic Conversation")
        
        message = "Hello! My name is Alice."
        response = self.send_message(message)
        
        if response.get("status") == "success" and response.get("response"):
            print_pass(f"Bot responded to greeting")
            print_info(f"User: {message}")
            print_info(f"Bot: {response.get('response')[:100]}...")
            self.tests_passed += 1
        else:
            print_fail(f"No valid response: {response.get('error', 'Unknown error')}")
            self.tests_failed += 1
        
        time.sleep(2)
    
    def test_context_recall(self):
        """Test 2: Context recall - Bot should remember previous conversation"""
        print_test("Context Recall (Memory)")
        
        # First, tell the bot something
        message1 = "My favorite color is blue and I love programming in Python."
        response1 = self.send_message(message1)
        print_info(f"User: {message1}")
        time.sleep(2)
        
        # Ask about it later
        message2 = "What is my favorite color?"
        response2 = self.send_message(message2)
        
        if response2.get("status") == "success":
            bot_response = response2.get("response", "").lower()
            print_info(f"User: {message2}")
            print_info(f"Bot: {response2.get('response')}")
            
            # Check if bot recalls the color
            if "blue" in bot_response:
                print_pass("Bot correctly recalled the favorite color from memory!")
                self.tests_passed += 1
            else:
                print_fail("Bot did not recall the favorite color")
                print_info("This may indicate Cortex memory is not working")
                self.tests_failed += 1
        else:
            print_fail(f"Request failed: {response2.get('error')}")
            self.tests_failed += 1
        
        time.sleep(2)
    
    def test_repeated_questions(self):
        """Test 3: Repeated questions - Test semantic search"""
        print_test("Repeated Questions (Semantic Search)")
        
        # Ask similar questions
        questions = [
            "What programming language did I mention?",
            "Which coding language do I prefer?",
            "What language did I say I love?"
        ]
        
        responses_with_python = 0
        
        for i, question in enumerate(questions, 1):
            response = self.send_message(question)
            if response.get("status") == "success":
                bot_response = response.get("response", "").lower()
                print_info(f"Q{i}: {question}")
                print_info(f"A{i}: {response.get('response')[:80]}...")
                
                if "python" in bot_response:
                    responses_with_python += 1
            
            time.sleep(1)
        
        if responses_with_python >= 2:
            print_pass(f"Bot recalled 'Python' in {responses_with_python}/3 similar questions")
            print_info("Semantic search is working!")
            self.tests_passed += 1
        else:
            print_fail(f"Bot only recalled 'Python' in {responses_with_python}/3 questions")
            self.tests_failed += 1
    
    def test_conversation_history(self):
        """Test 4: Get conversation history via API"""
        print_test("Conversation History API")
        
        try:
            response = requests.get(
                f"{self.base_url}/chat/history/{self.session_id}",
                timeout=10
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("status") == "success":
                history = data.get("history", [])
                print_pass(f"Retrieved conversation history")
                print_info(f"History contains {len(history)} messages")
                
                if len(history) > 0:
                    print_info(f"Sample: {history[0]}")
                    self.tests_passed += 1
                else:
                    print_fail("History is empty")
                    self.tests_failed += 1
            else:
                print_fail(f"Failed to get history: {data.get('error')}")
                self.tests_failed += 1
        except Exception as e:
            print_fail(f"Error: {e}")
            self.tests_failed += 1
    
    def test_memory_stats(self):
        """Test 5: Memory statistics"""
        print_test("Memory Statistics")
        
        try:
            response = requests.get(
                f"{self.base_url}/memory/stats",
                timeout=10
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("status") == "success":
                stats = data.get("stats", {})
                print_pass("Retrieved memory statistics")
                print_info(f"Total memories: {stats.get('total_memories', 0)}")
                print_info(f"Short-term count: {stats.get('short_term_count', 0)}")
                print_info(f"Total sessions: {stats.get('total_sessions', 0)}")
                print_info(f"Cortex enabled: {stats.get('cortex_enabled', False)}")
                
                if stats.get('total_memories', 0) > 0:
                    print_pass("Memory is being stored successfully!")
                    self.tests_passed += 1
                else:
                    print_fail("No memories stored yet")
                    self.tests_failed += 1
            else:
                print_fail(f"Failed to get stats: {data.get('error')}")
                self.tests_failed += 1
        except Exception as e:
            print_fail(f"Error: {e}")
            self.tests_failed += 1
    
    def test_multi_turn_conversation(self):
        """Test 6: Multi-turn conversation with context"""
        print_test("Multi-turn Conversation Flow")
        
        conversation = [
            ("I work as a software engineer at Google.", None),
            ("I have been there for 3 years.", None),
            ("Where do I work?", "google"),
            ("How long have I worked there?", "3"),
        ]
        
        passed = True
        for i, (message, expected_keyword) in enumerate(conversation, 1):
            response = self.send_message(message)
            
            if response.get("status") == "success":
                bot_response = response.get("response", "").lower()
                print_info(f"Turn {i}: {message}")
                
                if expected_keyword:
                    if expected_keyword in bot_response:
                        print_info(f"✓ Bot correctly recalled: '{expected_keyword}'")
                    else:
                        print_info(f"✗ Bot did not recall: '{expected_keyword}'")
                        print_info(f"Response: {response.get('response')[:100]}")
                        passed = False
            else:
                print_fail(f"Turn {i} failed")
                passed = False
            
            time.sleep(1.5)
        
        if passed:
            print_pass("Multi-turn conversation with context successful!")
            self.tests_passed += 1
        else:
            print_fail("Context not fully maintained across turns")
            self.tests_failed += 1
    
    def test_new_session(self):
        """Test 7: New session isolation"""
        print_test("Session Isolation")
        
        new_session = "test_session_isolated_002"
        
        # Ask about previous session's info in new session
        message = "What is my name?"
        response = self.send_message(message, session_id=new_session)
        
        if response.get("status") == "success":
            bot_response = response.get("response", "").lower()
            print_info(f"New session query: {message}")
            print_info(f"Bot response: {response.get('response')[:100]}")
            
            # Should NOT know "Alice" from previous session
            if "alice" not in bot_response:
                print_pass("Sessions are properly isolated!")
                print_info("Bot correctly doesn't know name from other session")
                self.tests_passed += 1
            else:
                print_fail("Session isolation may be broken")
                print_info("Bot recalled info from different session")
                self.tests_failed += 1
        else:
            print_fail(f"Request failed: {response.get('error')}")
            self.tests_failed += 1
    
    def test_cortex_features(self):
        """Test 8: Cortex-specific features"""
        print_test("Cortex SDK Features")
        
        # Test summarization endpoint
        try:
            response = requests.get(
                f"{self.base_url}/chat/summarize/{self.session_id}",
                timeout=15
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("status") == "success":
                summary = data.get("summary", "")
                print_pass("Conversation summarization works!")
                print_info(f"Summary: {summary[:150]}...")
                self.tests_passed += 1
            else:
                print_info("Summarization not available (may require Cortex)")
                print_info(f"Response: {data.get('error') or data.get('summary')}")
                self.tests_failed += 1
        except Exception as e:
            print_fail(f"Error: {e}")
            self.tests_failed += 1
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("CORTEX SDK + CHAT BOT INTEGRATION TESTS")
        
        # Check server first
        if not self.check_server():
            print(f"\n{Colors.RED}Cannot proceed without running server!{Colors.END}\n")
            return False
        
        print(f"\n{Colors.BOLD}Starting test suite with session: {self.session_id}{Colors.END}\n")
        time.sleep(1)
        
        # Run all tests
        self.test_basic_conversation()
        self.test_context_recall()
        self.test_repeated_questions()
        self.test_conversation_history()
        self.test_memory_stats()
        self.test_multi_turn_conversation()
        self.test_new_session()
        self.test_cortex_features()
        
        # Print results
        print_header("TEST RESULTS")
        
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"{Colors.BOLD}Total Tests:{Colors.END} {total_tests}")
        print(f"{Colors.GREEN}Passed:{Colors.END} {self.tests_passed}")
        print(f"{Colors.RED}Failed:{Colors.END} {self.tests_failed}")
        print(f"{Colors.CYAN}Pass Rate:{Colors.END} {pass_rate:.1f}%\n")
        
        if pass_rate >= 75:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ INTEGRATION SUCCESSFUL!{Colors.END}")
            print(f"{Colors.GREEN}Cortex SDK is working with the Chat_bot!{Colors.END}\n")
        elif pass_rate >= 50:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ PARTIAL SUCCESS{Colors.END}")
            print(f"{Colors.YELLOW}Some features working, check failures above.{Colors.END}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ INTEGRATION ISSUES{Colors.END}")
            print(f"{Colors.RED}Multiple test failures. Check Cortex SDK installation.{Colors.END}\n")
        
        return pass_rate >= 75


def main():
    """Main test runner"""
    tester = ChatBotTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


