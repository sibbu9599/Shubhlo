import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_BOOKINGS

class TestVendorCrossServiceVisibility(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        GLOBAL_REGISTERED_BOOKINGS.clear()

    def test_registered_vendor_login_and_booking_display(self):
        # 1. Vendor registers with catering service
        reg_res = self.app.post('/vendor_register', data={
            'accept_terms_vendor': 'on',
            'name': 'Shahi Royal Caterers',
            'email': 'shahi_test@shubhlo.com',
            'phone': '9876543999',
            'service': 'catering',
            'description': 'Delicious Royal Catering',
            'price': '45000',
            'password': 'vendorpassword123',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        # 2. Customer logs in on Customer Client and makes a booking selecting Shahi Royal Caterers
        cust_client = app.test_client()
        with cust_client.session_transaction() as cust_sess:
            cust_sess['user'] = 'customer_rohan@example.com'
            cust_sess['booking_info'] = {
                'name': 'Rohan Verma',
                'email': 'customer_rohan@example.com',
                'phone': '9111122222',
                'catering': 'Shahi Royal Caterers',
                'event_date': '2026-12-10',
                'amount': 45000.0,
                'terms_accepted': True
            }

        cust_res = cust_client.post('/process-payment', data={
            'payment_method': 'UPI / QR Code',
            'transaction_id': 'TXN11223344'
        }, follow_redirects=True)
        self.assertEqual(cust_res.status_code, 200)

        # 3. Vendor logs in from a FRESH browser client
        fresh_vendor_client = app.test_client()
        login_res = fresh_vendor_client.post('/vendor_login', data={
            'email': 'shahi_test@shubhlo.com',
            'password': 'vendorpassword123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        v_dash_res = fresh_vendor_client.get('/vendor_dashboard')
        self.assertEqual(v_dash_res.status_code, 200)
        html = v_dash_res.get_data(as_text=True)

        # Verify Vendor Dashboard loaded registered vendor name & booking
        self.assertIn('Shahi Royal Caterers', html)
        self.assertIn('2026-12-10', html)
        self.assertIn('Masked by Owner', html)

if __name__ == '__main__':
    unittest.main()
