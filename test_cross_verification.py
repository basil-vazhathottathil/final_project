import unittest
from unittest.mock import patch, MagicMock
from app.agent.vehicle_agent import run_vehicle_agent

class TestCrossVerification(unittest.TestCase):

    @patch('app.agent.vehicle_agent.load_short_term_memory')
    @patch('app.agent.vehicle_agent.load_short_term_memory_structured')
    @patch('app.agent.vehicle_agent.load_chat_summary')
    @patch('app.agent.vehicle_agent.load_chat_issue_summary')
    @patch('app.agent.vehicle_agent.load_open_issues')
    @patch('app.agent.vehicle_agent.save_chat_turn')
    @patch('app.agent.vehicle_agent.upsert_chat_summary')
    @patch('app.agent.vehicle_agent.upsert_issue_from_summary')
    @patch('app.agent.vehicle_agent.get_web_search_tool')
    @patch('app.agent.vehicle_agent.llm')
    def test_cross_verification_flow(self, mock_llm, mock_search_tool, mock_upsert_issue, *mocks):
        # 1. Setup Mock for first LLM pass (Low Confidence)
        mock_resp_1 = MagicMock()
        mock_resp_1.content = '{"diagnosis": "Strange clicking sound", "action": "ASK", "confidence": 0.4, "explanation": "I need more info."}'
        
        # 2. Setup Mock for second LLM pass (After search)
        mock_resp_2 = MagicMock()
        mock_resp_2.content = '{"diagnosis": "Worn CV joint", "action": "CONFIRM_WORKSHOP", "confidence": 0.8, "explanation": "Based on search results, clicking while turning usually means a worn CV joint."}'
        
        # 3. Setup Mock for summary and issue extraction
        mock_resp_summary = MagicMock()
        mock_resp_summary.content = "Summary: User reports clicking sound, agent verified CV joint issue."
        
        mock_resp_issue = MagicMock()
        mock_resp_issue.content = '{"title": "Worn CV Joint", "summary": "Clicking sound while turning.", "severity": 0.8}'
        
        mock_llm.invoke.side_effect = [mock_resp_1, mock_resp_2, mock_resp_summary, mock_resp_issue]
        
        # 4. Setup Mock for Search Tool
        mock_search_instance = MagicMock()
        mock_search_instance.invoke.return_value = [
            {"content": "Clicking sound while turning often indicates a failing CV joint."},
            {"url": "https://example.com/cv-joint-guide"}
        ]
        mock_search_tool.return_value = mock_search_instance
        
        # 4. Run Agent
        response = run_vehicle_agent(
            user_input="There is a clicking sound when I turn the steering wheel.",
            chat_id="test-verify-chat",
            user_id="test-user"
        )
        
        # 5. Assertions
        print(f"Final Response Diagnosis: {response.get('diagnosis')}")
        print(f"Final Response Confidence: {response.get('confidence')}")
        
        self.assertEqual(mock_llm.invoke.call_count, 4)
        mock_search_instance.invoke.assert_called_once()
        self.assertEqual(response["diagnosis"], "Worn CV joint")
        self.assertEqual(response["confidence"], 0.8)
        print("\n✅ Cross-Verification test passed: Web search triggered and diagnosis updated.")

if __name__ == "__main__":
    unittest.main()
