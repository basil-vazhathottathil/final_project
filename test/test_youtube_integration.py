import os
import unittest
import re
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

load_dotenv()

from app.agent.tools.youtube_search import search_youtube_videos, normalize_youtube_url
from app.agent.vehicle_agent import run_vehicle_agent

class TestYouTubeIntegration(unittest.TestCase):
    
    def test_normalize_url(self):
        urls = {
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }
        for input_url, expected in urls.items():
            normalized = normalize_youtube_url(input_url)
            self.assertEqual(normalized, expected, f"Failed for {input_url}: expected {expected}, got {normalized}")

    @patch('app.agent.tools.youtube_search.get_web_search_tool')
    def test_search_videos(self, mock_tool):
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = [
            {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            {"url": "https://example.com/not-youtube"},
            {"url": "https://youtu.be/12345678901"},
        ]
        mock_tool.return_value = mock_instance
        
        results = search_youtube_videos("oil change")
        print(f"Direct Search Results: {results}")
        self.assertEqual(len(results), 2, f"Expected 2 results, got {len(results)}")
        self.assertIn("https://www.youtube.com/watch?v=dQw4w9WgXcQ", results)
        self.assertIn("https://www.youtube.com/watch?v=12345678901", results)

    @patch('app.agent.vehicle_agent.load_short_term_memory')
    @patch('app.agent.vehicle_agent.load_short_term_memory_structured')
    @patch('app.agent.vehicle_agent.load_chat_summary')
    @patch('app.agent.vehicle_agent.load_chat_issue_summary')
    @patch('app.agent.vehicle_agent.load_open_issues')
    @patch('app.agent.vehicle_agent.save_chat_turn')
    @patch('app.agent.vehicle_agent.upsert_chat_summary')
    @patch('app.agent.vehicle_agent.llm')
    @patch('app.agent.vehicle_agent.search_youtube_videos')
    def test_agent_integration(self, mock_search, mock_llm, mock_upsert_summary, mock_save, mock_open_issues, mock_chat_issue_summary, mock_chat_summary, mock_memory_struct, mock_memory_text):
        # Setup mocks
        mock_search.return_value = ["https://www.youtube.com/watch?v=testvideoid"]
        
        mock_ai_response = MagicMock()
        mock_ai_response.content = '{ "diagnosis": "Low oil", "action": "DIY", "confidence": 0.9, "explanation": "You should add oil." }'
        mock_llm.invoke.return_value = mock_ai_response
        
        # Run agent
        response = run_vehicle_agent(
            user_input="How do I add oil?",
            chat_id="test-chat",
            user_id="test-user"
        )
        
        # Verify search was called
        mock_search.assert_called_once_with("Low oil")
        self.assertIn("https://www.youtube.com/watch?v=testvideoid", response.get("youtube_urls", []))
        print("\n✅ Agent integration test passed: YouTube URLs populated in response.")

if __name__ == "__main__":
    unittest.main()
