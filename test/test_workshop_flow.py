import unittest
from unittest.mock import patch, MagicMock
from app.agent.vehicle_agent import run_vehicle_agent

class TestWorkshopTrigger(unittest.TestCase):

    @patch('app.agent.vehicle_agent.load_short_term_memory')
    @patch('app.agent.vehicle_agent.load_short_term_memory_structured')
    @patch('app.agent.vehicle_agent.load_chat_summary')
    @patch('app.agent.vehicle_agent.load_chat_issue_summary')
    @patch('app.agent.vehicle_agent.load_open_issues')
    @patch('app.agent.vehicle_agent.save_chat_turn')
    def test_workshop_trigger_on_yes(self, mock_save, mock_issues, mock_issue_sum, mock_sum, mock_memory_struct, mock_memory_text):
        # Setup: History ends with CONFIRM_WORKSHOP
        mock_memory_struct.return_value = [
            {"user": "My brakes are squealing", "agent": {"action": "CONFIRM_WORKSHOP", "explanation": "Would you like workshop details?"}}
        ]
        mock_memory_text.return_value = "User: My brakes are squealing\nAgent: Would you like workshop details?"
        mock_sum.return_value = None
        mock_issue_sum.return_return = None
        mock_issues.return_value = []
        
        # Action: User says "yes"
        response = run_vehicle_agent(
            user_input="yes",
            chat_id="test-chat",
            user_id="test-user"
        )
        
        # Assert: Action should be WORKSHOP_RESULTS
        self.assertEqual(response['action'], "WORKSHOP_RESULTS")
        self.assertTrue("workshops" in response['explanation'].lower())
        mock_save.assert_called()

    @patch('app.agent.vehicle_agent.load_short_term_memory')
    @patch('app.agent.vehicle_agent.load_short_term_memory_structured')
    @patch('app.agent.vehicle_agent.load_chat_summary')
    @patch('app.agent.vehicle_agent.load_chat_issue_summary')
    @patch('app.agent.vehicle_agent.load_open_issues')
    @patch('app.agent.vehicle_agent.save_chat_turn')
    def test_no_trigger_on_normal_yes(self, mock_save, mock_issues, mock_issue_sum, mock_sum, mock_memory_struct, mock_memory_text):
        # Setup: History ends with ASK (not workshop related)
        mock_memory_struct.return_value = [
            {"user": "My car won't start", "agent": {"action": "ASK", "explanation": "Does it click?"}}
        ]
        mock_memory_text.return_value = "User: My car won't start\nAgent: Does it click?"
        mock_sum.return_value = None
        mock_issue_sum.return_return = None
        mock_issues.return_value = []
        
        # Action: User says "yes" (answering the "does it click" question)
        # Note: In this case, it should NOT trigger build_workshop_response
        # It should proceed to call the LLM
        with patch('app.agent.vehicle_agent.llm') as mock_llm:
            mock_llm.invoke.return_value.content = '{"action": "ASK", "diagnosis": "Battery", "explanation": "Likely battery."}'
            response = run_vehicle_agent(
                user_input="yes",
                chat_id="test-chat",
                user_id="test-user"
            )
            self.assertEqual(response['action'], "ASK")

if __name__ == '__main__':
    unittest.main()
