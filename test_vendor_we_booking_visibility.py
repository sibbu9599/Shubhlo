import sys
import os
import unittest

sys.path.insert(0, os.path.abspath('.'))
from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_BOOKINGS, GLOBAL_MOCK_VERIFICATIONS

class TestVendorWeBookingVisibility(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_vendor_we_registration_booking_and_dashboard_display(self):
        """Test registering vendor 'we', creating a customer booking for 'we', and verifying dashboard display."""
        vendor_email = "we_vendor@shubhlo.com"
        vendor_phone = "9876543299"
        vendor_name = "Shubh Beauty & Bridal Makeover"
        vendor_pass = "VendorPass123"

        # 1. Register vendor 'we'
        v_data = {
            'name': vendor_name,
            'email': vendor_email,
            'phone': vendor_phone,
            'service': 'makeup',
            'description': 'Top makeup artist in town.',
            'price': '15000',
            'password': vendor_pass,
            'accept_terms_vendor': 'on'
        }
        res = self.client.post('/vendor_register', data=v_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Mark vendor as Approved in both global list and session mock list
        for v in GLOBAL_REGISTERED_VENDORS:
            if v.get('email') == vendor_email:
                v['approval_status'] = 'Approved'

        with self.client.session_transaction() as sess:
            mock_v = sess.get('mock_vendors', [])
            for v in mock_v:
                if v.get('email') == vendor_email:
                    v['approval_status'] = 'Approved'
            sess['mock_vendors'] = mock_v

        # 2. Customer login & booking for vendor 'we'
        cust_email = "cust_we_test@example.com"
        self.client.post('/signup', data={
            'name': 'Customer For We',
            'email': cust_email,
            'phone': '9123456789',
            'password': 'Password123'
        }, follow_redirects=True)

        # Step 1: customer details
        with self.client.session_transaction() as sess:
            sess['user'] = cust_email

        b1_res = self.client.post('/booking1', data={
            'name': 'Customer For We',
            'email': cust_email,
            'phone': '9123456789',
            'event_date': '2026-11-15',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'address': 'Main Road Itarsi House 123'
        }, follow_redirects=True)
        self.assertEqual(b1_res.status_code, 200)

        # Step 2: Select vendor for makeup service
        b2_res = self.client.post('/confirm_booking', data={
            'makeup': vendor_name
        }, follow_redirects=True)
        self.assertEqual(b2_res.status_code, 200)

        # Step 3: Accept terms & Pay
        with self.client.session_transaction() as sess:
            b_info = sess.get('booking_info', {})
            b_info['terms_accepted'] = True
            sess['booking_info'] = b_info

        res_pay = self.client.post('/process-payment', data={'payment_method': 'UPI'}, follow_redirects=True)
        self.assertEqual(res_pay.status_code, 200)

        # Get created booking ID
        created_booking_id = GLOBAL_REGISTERED_BOOKINGS[-1]['id']

        # 3. Owner approves and unlocks booking
        res_owner = self.client.post(f'/owner/approve_and_unlock/{created_booking_id}', follow_redirects=True)
        self.assertEqual(res_owner.status_code, 200)

        # 4. Vendor 'we' login
        res_vlogin = self.client.post('/vendor_login', data={
            'email': vendor_email,
            'password': vendor_pass
        }, follow_redirects=True)
        self.assertEqual(res_vlogin.status_code, 200)

        # 5. Access vendor dashboard and assert unlocked booking details are displayed
        res_dash = self.client.get('/vendor_dashboard')
        self.assertEqual(res_dash.status_code, 200)
        html = res_dash.data.decode('utf-8', errors='ignore')

        self.assertIn('Customer For We', html)
        self.assertIn('9123456789', html)
        self.assertIn('2026-11-15', html)
        self.assertIn('Booking Approved by Owner', html)
        print("\n[PASS] Owner-confirmed Vendor 'we' booking and unlocked customer details successfully displayed in Vendor Dashboard!")

if __name__ == '__main__':
    unittest.main()
