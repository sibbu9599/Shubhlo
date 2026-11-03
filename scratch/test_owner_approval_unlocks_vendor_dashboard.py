import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app, GLOBAL_REGISTERED_BOOKINGS

class TestOwnerApprovalUnlocksVendorDashboard(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        GLOBAL_REGISTERED_BOOKINGS.clear()

    def test_owner_approval_reflects_unlocked_on_vendor_dashboard(self):
        # 1. Customer creates booking
        cust_client = app.test_client()
        with cust_client.session_transaction() as cust_sess:
            cust_sess['user'] = 'customer_rahul@example.com'
            cust_sess['booking_info'] = {
                'name': 'Rahul Verma',
                'email': 'customer_rahul@example.com',
                'phone': '9876543210',
                'venue': 'Royal Milan Garden',
                'event_date': '2026-12-20',
                'amount': 120000.0,
                'terms_accepted': True
            }

        pay_res = cust_client.post('/process-payment', data={
            'payment_method': 'UPI / QR Code',
            'transaction_id': 'TXN112233'
        }, follow_redirects=True)
        self.assertEqual(pay_res.status_code, 200)

        # Get generated booking ID
        self.assertTrue(len(GLOBAL_REGISTERED_BOOKINGS) > 0)
        b_id = GLOBAL_REGISTERED_BOOKINGS[0]['id']

        # 2. Owner logs in and approves booking
        owner_client = app.test_client()
        with owner_client.session_transaction() as o_sess:
            o_sess['admin'] = 'owner@shubhlo.com'
            o_sess['is_owner'] = True

        approve_res = owner_client.post(f'/owner/approve_and_unlock/{b_id}', follow_redirects=True)
        self.assertEqual(approve_res.status_code, 200)

        # Verify global booking status is Confirmed
        self.assertEqual(GLOBAL_REGISTERED_BOOKINGS[0]['status'], 'Confirmed')

        # 3. Vendor logs in on a FRESH client
        vendor_client = app.test_client()
        with vendor_client.session_transaction() as v_sess:
            v_sess['vendor'] = 'royal_milan@shubhlo.com'
            v_sess['vendor_name'] = 'Royal Milan Garden'
            v_sess['vendor_service'] = 'venue'
            v_sess['mock_vendors'] = [
                {
                    'id': 888,
                    'name': 'Royal Milan Garden',
                    'email': 'royal_milan@shubhlo.com',
                    'phone': '9876543210',
                    'service': 'venue',
                    'price': 120000.0,
                    'approval_status': 'Approved'
                }
            ]

        v_dash_res = vendor_client.get('/vendor_dashboard')
        self.assertEqual(v_dash_res.status_code, 200)
        html = v_dash_res.get_data(as_text=True)

        # Verify that Vendor Dashboard displays UNLOCKED customer info & Booking Approved status
        self.assertIn('Booking Approved by Owner', html)
        self.assertIn('Rahul Verma', html)
        self.assertIn('9876543210', html)

if __name__ == '__main__':
    unittest.main()
