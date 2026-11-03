import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app, GLOBAL_REGISTERED_BOOKINGS

class TestVendorBookingVisibility(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        GLOBAL_REGISTERED_BOOKINGS.clear()

    def test_customer_booking_appears_on_vendor_dashboard(self):
        # 1. Customer fills booking info and completes payment
        with self.app.session_transaction() as cust_sess:
            cust_sess['user'] = 'customer_test@example.com'
            cust_sess['user_name'] = 'Vikram Sharma'
            cust_sess['booking_info'] = {
                'name': 'Vikram Sharma',
                'email': 'customer_test@example.com',
                'phone': '9876543210',
                'venue': 'Royal Milan Garden',
                'catering': 'Shahi Royal Caterers',
                'event_date': '2026-11-25',
                'amount': 150000.0,
                'terms_accepted': True
            }

        booking_res = self.app.post('/process-payment', data={
            'payment_method': 'UPI / QR Code',
            'transaction_id': 'TXN99887766'
        }, follow_redirects=True)
        self.assertEqual(booking_res.status_code, 200)

        # 2. Vendor logs in on a SEPARATE session/client
        vendor_client = app.test_client()
        with vendor_client.session_transaction() as v_sess:
            v_sess['vendor'] = 'royal_milan@shubhlo.com'
            v_sess['vendor_name'] = 'Royal Milan Garden'
            v_sess['vendor_service'] = 'venue'
            v_sess['mock_vendors'] = [
                {
                    'id': 999,
                    'name': 'Royal Milan Garden',
                    'email': 'royal_milan@shubhlo.com',
                    'phone': '9876543210',
                    'service': 'venue',
                    'description': 'Luxury venue',
                    'price': 150000.0,
                    'photo': None,
                    'approval_status': 'Approved'
                }
            ]

        v_res = vendor_client.get('/vendor_dashboard')
        self.assertEqual(v_res.status_code, 200)
        html = v_res.get_data(as_text=True)

        # Verify that customer booking appears on Vendor Dashboard (pending owner contact approval state)
        self.assertIn('Masked by Owner', html)
        self.assertIn('2026-11-25', html)

        # 3. Simulate Owner approving the booking
        for b in GLOBAL_REGISTERED_BOOKINGS:
            b['status'] = 'Confirmed'
            b['booking_status'] = 'Confirmed'

        v_res_approved = vendor_client.get('/vendor_dashboard')
        html_approved = v_res_approved.get_data(as_text=True)

        # Verify unlocked state shows Customer Name & Contact info
        self.assertIn('Vikram Sharma', html_approved)
        self.assertIn('Booking Approved by Owner', html_approved)

if __name__ == '__main__':
    unittest.main()
