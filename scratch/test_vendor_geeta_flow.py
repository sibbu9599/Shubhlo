import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_BOOKINGS

class TestVendorGeetaFullLifecycle(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        GLOBAL_REGISTERED_VENDORS[:] = [v for v in GLOBAL_REGISTERED_VENDORS if v.get('email') != 'geeta@shubhlo.com']
        GLOBAL_REGISTERED_BOOKINGS[:] = [b for b in GLOBAL_REGISTERED_BOOKINGS if b.get('decoration') != 'Geeta Mehendi Art']

    def test_geeta_vendor_registration_approval_booking_and_dashboard_unlock(self):
        # 1. Geeta registers as Vendor
        geeta_client = app.test_client()
        reg_res = geeta_client.post('/vendor_register', data={
            'accept_terms_vendor': 'on',
            'name': 'Geeta Mehendi Art',
            'email': 'geeta@shubhlo.com',
            'phone': '9876599999',
            'service': 'decoration',
            'description': 'Bridal Mehendi & Event Decoration',
            'price': '15000',
            'password': 'geeta123password',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        # Get Geeta's unique vendor ID
        geeta_v = next((v for v in GLOBAL_REGISTERED_VENDORS if v['email'] == 'geeta@shubhlo.com'), None)
        self.assertIsNotNone(geeta_v)
        geeta_id = geeta_v['id']
        self.assertEqual(geeta_v['approval_status'], 'Pending')

        # 2. Owner approves Geeta Vendor Registration
        owner_client = app.test_client()
        with owner_client.session_transaction() as o_sess:
            o_sess['admin'] = 'owner@shubhlo.com'
            o_sess['is_owner'] = True

        app_v_res = owner_client.post(f'/admin/vendor/approve/{geeta_id}', follow_redirects=True)
        self.assertEqual(app_v_res.status_code, 200)

        # Verify Geeta is now Approved
        self.assertEqual(geeta_v['approval_status'], 'Approved')

        # 3. Customer books Geeta Mehendi Art
        cust_client = app.test_client()
        with cust_client.session_transaction() as cust_sess:
            cust_sess['user'] = 'customer_priya@example.com'
            cust_sess['booking_info'] = {
                'name': 'Priya Patel',
                'email': 'customer_priya@example.com',
                'phone': '9812345678',
                'decoration': 'Geeta Mehendi Art',
                'event_date': '2026-12-28',
                'amount': 15000.0,
                'terms_accepted': True
            }

        pay_res = cust_client.post('/process-payment', data={
            'payment_method': 'UPI / QR Code',
            'transaction_id': 'TXN_GEETA_01'
        }, follow_redirects=True)
        self.assertEqual(pay_res.status_code, 200)

        b_item = next((b for b in GLOBAL_REGISTERED_BOOKINGS if b.get('decoration') == 'Geeta Mehendi Art'), None)
        self.assertIsNotNone(b_item)
        booking_id = b_item['id']

        # 4. Owner approves booking and unlocks contact details to Geeta
        app_b_res = owner_client.post(f'/owner/approve_and_unlock/{booking_id}', follow_redirects=True)
        self.assertEqual(app_b_res.status_code, 200)
        self.assertEqual(b_item['status'], 'Confirmed')

        # 5. Geeta logs in to Vendor Dashboard on a fresh client
        geeta_fresh_client = app.test_client()
        login_res = geeta_fresh_client.post('/vendor_login', data={
            'email': 'geeta@shubhlo.com',
            'password': 'geeta123password'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        dash_res = geeta_fresh_client.get('/vendor_dashboard')
        self.assertEqual(dash_res.status_code, 200)
        html = dash_res.get_data(as_text=True)

        # Verify Geeta sees the unlocked customer booking
        self.assertIn('Geeta Mehendi Art', html)
        self.assertIn('Booking Approved by Owner', html)
        self.assertIn('Priya Patel', html)
        self.assertIn('9812345678', html)

if __name__ == '__main__':
    unittest.main()
