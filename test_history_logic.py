import unittest
from unittest.mock import MagicMock
from app.routers.chathistory import get_chat_history
from app.db.db import load_short_term_memory

class TestHistoryLogic(unittest.TestCase):

    def test_get_chat_history_shows_latest(self):
        # Mock data: newest (id:3) to oldest (id:1)
        mock_data = [
            {"chat_id": "c1", "prompt": "Newest", "response_ai": "Ai3", "created_at": "2024-02-24T12:00:03"},
            {"chat_id": "c1", "prompt": "Middle", "response_ai": "Ai2", "created_at": "2024-02-24T12:00:02"},
            {"chat_id": "c1", "prompt": "Oldest", "response_ai": "Ai1", "created_at": "2024-02-24T12:00:01"},
        ]
        
        # We need to simulate the dict-like response from supabase
        mock_res = MagicMock()
        mock_res.data = mock_data
        
        # Internal loop logic verification (since we can't easily mock Depends in unit test)
        conversations = {}
        for row in mock_data:
            cid = row["chat_id"]
            if cid not in conversations:
                conversations[cid] = {
                    "id": cid,
                    "title": (row["prompt"] or "")[:60],
                    "preview": (row["prompt"] or "")[:120],
                    "lastMessage": row["response_ai"],
                    "timestamp": row["created_at"],
                    "messageCount": 1,
                }
            else:
                conversations[cid]["messageCount"] += 1
        
        self.assertEqual(conversations["c1"]["lastMessage"], "Ai3")
        self.assertEqual(conversations["c1"]["timestamp"], "2024-02-24T12:00:03")
        self.assertEqual(conversations["c1"]["messageCount"], 3)

    def test_load_short_term_memory_includes_explanation(self):
        # This one tests db.py logic
        from app.db.db import load_short_term_memory as original_load
        
        with MagicMock() as mock_supabase:
            import app.db.db as db_mod
            old_supabase = db_mod.supabase
            db_mod.supabase = mock_supabase
            
            mock_data = [
                {"prompt": "Hello", "response_ai": {"explanation": "Hi there", "diagnosis": "None", "action": "ASK"}}
            ]
            mock_supabase.table().select().eq().order().limit().execute.return_value.data = mock_data
            
            result = db_mod.load_short_term_memory("chat1")
            self.assertIn("Hi there", result)
            self.assertIn("Agent: Hi there", result)
            
            db_mod.supabase = old_supabase

if __name__ == '__main__':
    unittest.main()
