import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app

class TestOwnerWhatsAppSMSFeature(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_owner_dashboard_whatsapp_and_sms_links_for_bookings(self):
        with self.app.session_transaction() as sess:
            sess['admin'] = 'owner@shubhlo.com'
            sess['is_owner'] = True
            sess['mock_bookings'] = [
                {
                    'id': 701,
                    'name': 'Aarav Patel',
                    'phone': '9876543210',
                    'email': 'aarav@example.com',
                    'event_name': 'Wedding / शादी',
                    'event_date': '2026-12-15',
                    'tehsil': 'Indore',
                    'district': 'Indore',
                    'amount': 95000.0,
                    'otp': '884920',
                    'status': 'Pending Owner Approval'
                }
            ]

        res = self.app.get('/owner/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Verify WhatsApp link for booking customer
        self.assertIn('https://wa.me/919876543210', html)
        self.assertIn('Aarav%20Patel', html)
        self.assertIn('booking%20%23701', html)

        # Verify SMS link for booking customer
        self.assertIn('sms:9876543210', html)

    def test_owner_dashboard_whatsapp_and_sms_links_for_registered_customers(self):
        with self.app.session_transaction() as sess:
            sess['admin'] = 'owner@shubhlo.com'
            sess['is_owner'] = True
            sess['customers'] = [
                {
                    'id': 301,
                    'name': 'Meera Singh',
                    'phone': '9123456789',
                    'email': 'meera@example.com'
                }
            ]

        res = self.app.get('/owner/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Verify WhatsApp link for registered customer
        self.assertIn('https://wa.me/919123456789', html)
        self.assertIn('Meera%20Singh', html)

        # Verify SMS link for registered customer
        self.assertIn('sms:9123456789', html)

if __name__ == '__main__':
    unittest.main()
