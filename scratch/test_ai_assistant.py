import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app

class TestAIAssistantEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_api_assistant_greetings(self):
        res = self.app.post('/api/assistant', json={'query': 'hi'})
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('reply', json_data)
        self.assertIn('Namaste & Welcome to Shubhlo AI Assistant', json_data['reply'])

    def test_api_assistant_venue_search(self):
        res = self.app.post('/api/assistant', json={'query': 'marriage garden venue prices'})
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('VENUE', json_data['reply'])

    def test_api_assistant_booking_help(self):
        res = self.app.post('/api/assistant', json={'query': 'how to book'})
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('Simple 3-Step Booking Process', json_data['reply'])

if __name__ == '__main__':
    unittest.main()
