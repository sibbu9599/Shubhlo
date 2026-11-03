import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app

class TestWhatsAppOwnerCommunication(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_customer_dashboard_whatsapp_link(self):
        with self.app.session_transaction() as sess:
            sess['user'] = 'testuser@shubhlo.com'
            sess['user_name'] = 'Rahul Sharma'
            sess['mock_bookings'] = [
                {
                    'id': 101,
                    'booking_id': 101,
                    'event_name': 'Wedding',
                    'event_date': '2026-10-15',
                    'tehsil': 'Itarsi',
                    'total_price': 150000.0,
                    'amount': 150000.0,
                    'payment_status': 'Paid',
                    'advance_paid': 5118.0,
                    'status': 'Confirmed',
                    'selected_vendors': [{'category_title': 'Venue', 'name': 'Milan Garden'}]
                }
            ]
        
        res = self.app.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        # Check WhatsApp owner link presence
        self.assertIn('wa.me/917067883131', html)
        self.assertIn('Chat with Owner on WhatsApp', html)

    def test_confirm_booking_whatsapp_link(self):
        with self.app.session_transaction() as sess:
            sess['user'] = 'rohan@example.com'
            sess['user_name'] = 'Rohan Verma'

        self.app.post('/booking1', data={
            'name': 'Rohan Verma',
            'email': 'rohan@example.com',
            'phone': '9876543210',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'event_date': '2026-11-20',
            'address': 'House 45, Station Road'
        }, follow_redirects=True)

        res = self.app.post('/confirm_booking', data={
            'venue': 'Royal Palace Garden',
            'catering': 'Shahi Royal Caterers'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('wa.me/917067883131', html)
        self.assertIn('Connect with Owner on WhatsApp', html)

    def test_contact_page_whatsapp_card(self):
        res = self.app.get('/contact')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('wa.me/917067883131', html)
        self.assertIn('Chat with Owner on WhatsApp', html)

    def test_api_assistant_whatsapp_query(self):
        res = self.app.post('/api/assistant', json={'query': 'owner whatsapp pe baat karni hai'})
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('wa.me/917067883131', json_data['reply'])
        self.assertIn('Open WhatsApp Chat', json_data['reply'])

if __name__ == '__main__':
    unittest.main()
