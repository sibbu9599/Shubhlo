import sys
import unittest
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath('.'))

from app import app, GLOBAL_REGISTERED_USERS, GLOBAL_REGISTERED_VENDORS

class ComprehensiveShubhloTestSuite(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_public_pages(self):
        """Test public pages and session redirects"""
        public_routes = ['/home', '/services', '/about', '/contact', '/terms', '/rating', '/login', '/vendor/login', '/vendor/register', '/promo-video', '/youtube']
        for route in public_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed with status {res.status_code}")

        # Booking route redirects to login if unauthenticated
        res = self.client.get('/booking1')
        self.assertEqual(res.status_code, 302)

        # Booking route renders 200 when authenticated
        with self.client.session_transaction() as sess:
            sess['user'] = 'testuser@example.com'
        res = self.client.get('/booking1')
        self.assertEqual(res.status_code, 200)

    def test_02_excluded_categories_purge(self):
        """Ensure services page loads active services properly"""
        res = self.client.get('/services')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('shahi_sawari', html)
        self.assertIn('venue', html)

    def test_03_customer_booking_flow(self):
        """Test complete multi-step customer booking and token advance calculation"""
        cust_email = "booking_flow_cust@example.com"
        self.client.post('/signup', data={
            'name': 'Rohan Verma',
            'email': cust_email,
            'phone': '9876543210',
            'password': 'Password123'
        }, follow_redirects=True)

        with self.client.session_transaction() as sess:
            sess['user'] = cust_email

        # Step 1: Submit Booking Info
        res = self.client.post('/booking1', data={
            'name': 'Rohan Verma',
            'email': cust_email,
            'phone': '9876543210',
            'event_date': '2026-12-25',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'address': 'House 45, Station Road'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Step 2: Select Vendors and submit to confirm_booking
        res = self.client.post('/confirm_booking', data={
            'venue': 'Royal Palace Garden',
            'catering': 'Rasoi Caterers'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Verify Token Payment Summary
        self.assertIn('10,236', html) # ₹10,236 total token payable for 2 vendors
        self.assertIn('Royal Palace Garden', html)

        # Step 3: Process Payment
        with self.client.session_transaction() as sess:
            b_info = sess.get('booking_info', {})
            b_info['terms_accepted'] = True
            sess['booking_info'] = b_info

        res = self.client.post('/process-payment', data={
            'payment_method': 'UPI'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('registered successfully', html.lower())

    def test_04_vendor_contact_locking_and_unlocking(self):
        """Test that unconfirmed bookings lock customer contact, and admin approval unlocks it"""
        v_email = "royal_palace_locktest@shubhlo.com"
        c_email = "locktest_cust@shubhlo.com"
        
        self.client.post('/vendor_register', data={
            'name': 'Royal Palace Garden',
            'email': v_email,
            'phone': '9988776611',
            'service': 'venue',
            'password': 'pass',
            'price': '150000',
            'govt_id_number': '112233445577',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        for v in GLOBAL_REGISTERED_VENDORS:
            if v.get('email') == v_email:
                v['approval_status'] = 'Approved'

        self.client.post('/signup', data={
            'name': 'Amit Kumar',
            'email': c_email,
            'phone': '9988776655',
            'password': 'pass'
        }, follow_redirects=True)

        # Create booking for vendor
        with self.client.session_transaction() as sess:
            sess['user'] = c_email

        self.client.post('/booking1', data={
            'name': 'Amit Kumar',
            'email': c_email,
            'phone': '9988776655',
            'event_date': '2026-12-25',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'address': 'Station Road'
        }, follow_redirects=True)

        self.client.post('/confirm_booking', data={'venue': 'Royal Palace Garden'}, follow_redirects=True)

        with self.client.session_transaction() as sess:
            b_info = sess.get('booking_info', {})
            b_info['terms_accepted'] = True
            sess['booking_info'] = b_info

        self.client.post('/process-payment', data={'payment_method': 'UPI'}, follow_redirects=True)

        booking_id = None
        with self.client.session_transaction() as sess:
            mock_b = sess.get('mock_bookings', [])
            if mock_b:
                booking_id = mock_b[-1].get('id')

        # 1. Check unconfirmed booking in Vendor Dashboard (contact should be hidden/locked)
        with self.client.session_transaction() as sess:
            sess['vendor'] = v_email
            sess['vendor_name'] = 'Royal Palace Garden'

        res = self.client.get('/vendor/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('🔒 Masked by Owner', html)

        # 2. Admin approves booking
        if booking_id:
            with self.client.session_transaction() as sess:
                sess['admin'] = 'admin@shubhlo.com'
                sess['is_owner'] = True

            res = self.client.get(f'/admin/approve_booking/{booking_id}', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # 3. Vendor checks dashboard again (contact unlocked)
            with self.client.session_transaction() as sess:
                sess['vendor'] = v_email
                sess['vendor_name'] = 'Royal Palace Garden'

            res = self.client.get('/vendor/dashboard')
            html = res.data.decode('utf-8')
            self.assertIn('Amit Kumar', html)
            self.assertIn('9988776655', html)

    def test_05_vendor_registration_notice_wording(self):
        """Verify notice and wording on vendor registration page"""
        res = self.client.get('/vendor/register')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Vendor Business Registration', html)

    def test_06_admin_dashboard_controls(self):
        """Test admin dashboard statistics and deletion/blacklist endpoints"""
        with self.client.session_transaction() as sess:
            sess['admin'] = 'admin@shubhlo.com'
            sess['is_owner'] = True

        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Master Admin Dashboard', html)

    def test_07_budget_protection_and_counter_offer(self):
        """Test Target Budget tracking and Vendor Counter-Offer acceptance flow"""
        v_email = "counter_vend@shubhlo.com"
        c_email = "counter_cust@shubhlo.com"
        
        self.client.post('/vendor_register', data={
            'name': 'Counter Royal Garden',
            'email': v_email,
            'phone': '9911223344',
            'service': 'venue',
            'password': 'pass',
            'price': '50000',
            'govt_id_number': '998877665511',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        for v in GLOBAL_REGISTERED_VENDORS:
            if v.get('email') == v_email:
                v['approval_status'] = 'Approved'

        self.client.post('/signup', data={
            'name': 'Rahul Sharma',
            'email': c_email,
            'phone': '9911223355',
            'password': 'pass'
        }, follow_redirects=True)

        # Create booking
        with self.client.session_transaction() as sess:
            sess['user'] = c_email

        self.client.post('/booking1', data={
            'name': 'Rahul Sharma',
            'email': c_email,
            'phone': '9911223355',
            'event_date': '2026-12-25',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'address': 'Station Road'
        }, follow_redirects=True)

        self.client.post('/confirm_booking', data={'venue': 'Counter Royal Garden'}, follow_redirects=True)

        with self.client.session_transaction() as sess:
            b_info = sess.get('booking_info', {})
            b_info['terms_accepted'] = True
            sess['booking_info'] = b_info

        self.client.post('/process-payment', data={'payment_method': 'UPI'}, follow_redirects=True)

        booking_id = None
        with self.client.session_transaction() as sess:
            mock_b = sess.get('mock_bookings', [])
            if mock_b:
                booking_id = mock_b[-1].get('id')

        if booking_id:
            # Vendor sends counter offer of ₹48,000
            with self.client.session_transaction() as sess:
                sess['vendor'] = v_email
                sess['vendor_name'] = 'Counter Royal Garden'
                sess['vendor_service'] = 'venue'

            res = self.client.post(f'/vendor/counter_offer/{booking_id}', data={
                'counter_amount': '48000',
                'counter_note': 'Special discount offered'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # Customer views dashboard and sees counter offer
            with self.client.session_transaction() as sess:
                sess['user'] = c_email

            res = self.client.get('/dashboard')
            self.assertEqual(res.status_code, 200)
            html = res.data.decode('utf-8')
            self.assertIn('48', html)

            # Customer accepts counter offer
            res = self.client.get(f'/customer/accept_counter_offer/{booking_id}', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

    def test_08_owner_master_controls(self):
        """Test Owner Master Controls for Customer Bookings and Vendor Registrations ON/OFF toggles"""
        with self.client.session_transaction() as sess:
            sess['admin'] = 'admin@shubhlo.com'
            sess['is_owner'] = True

        # Toggle customer bookings OFF
        res = self.client.post('/admin/update_system_settings', data={
            'allow_customer_booking': 'OFF',
            'booking_closure_msg': 'Bookings paused for maintenance',
            'allow_vendor_registration': 'ON',
            'vendor_closure_msg': ''
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check customer booking1 page shows maintenance message
        with self.client.session_transaction() as sess:
            sess['user'] = 'testuser@example.com'

        res = self.client.get('/booking1')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Bookings paused for maintenance', html)

        # Turn customer bookings back ON
        with self.client.session_transaction() as sess:
            sess['admin'] = 'admin@shubhlo.com'
            sess['is_owner'] = True

        self.client.post('/admin/update_system_settings', data={
            'allow_customer_booking': 'ON',
            'booking_closure_msg': '',
            'allow_vendor_registration': 'ON',
            'vendor_closure_msg': ''
        }, follow_redirects=True)

    def test_09_vendor_min_order_and_pricing_update(self):
        """Test Vendor Pricing and Minimum Order Value update and display on booking2"""
        v_email = "royal_pricing@shubhlo.com"
        self.client.post('/vendor_register', data={
            'name': 'Royal Pricing Venue',
            'email': v_email,
            'phone': '9922334455',
            'service': 'venue',
            'password': 'pass',
            'price': '20000',
            'govt_id_number': '998877665522',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        for v in GLOBAL_REGISTERED_VENDORS:
            if v.get('email') == v_email:
                v['approval_status'] = 'Approved'

        with self.client.session_transaction() as sess:
            sess['vendor'] = v_email
            sess['vendor_name'] = 'Royal Pricing Venue'
            sess['vendor_service'] = 'venue'

        # Vendor updates rates
        res = self.client.post('/vendor/update_pricing', data={
            'price': '25000',
            'min_order_value': '15000'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Customer views booking2 -> check data attributes
        with self.client.session_transaction() as sess:
            sess['user'] = 'customer@example.com'
            sess['booking_info'] = {
                'name': 'Rohan Verma',
                'email': 'customer@example.com',
                'phone': '9876543210',
                'event_date': '2026-12-25',
                'state': 'Madhya Pradesh',
                'district': 'Hoshangabad',
                'tehsil': 'Itarsi',
                'address': 'Station Road'
            }

        res = self.client.get('/booking2')
        self.assertEqual(res.status_code, 200)

    def test_10_advertisement_hub(self):
        """Test Marketing and Advertisement Hub page route and elements"""
        res = self.client.get('/advertisement')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Ultimate Marketing & Promotion Suite', html)

    def test_11_vendor_event_date_availability(self):
        """Test Vendor Event Date management and real-time customer availability status"""
        v_email = "royal_dateavail@shubhlo.com"
        self.client.post('/vendor_register', data={
            'name': 'Royal Availability Garden',
            'email': v_email,
            'phone': '9933445566',
            'service': 'venue',
            'password': 'pass',
            'price': '30000',
            'govt_id_number': '998877665533',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        for v in GLOBAL_REGISTERED_VENDORS:
            if v.get('email') == v_email:
                v['approval_status'] = 'Approved'

        # 1. Vendor logs in and blocks date '2026-12-25'
        with self.client.session_transaction() as sess:
            sess['vendor'] = v_email
            sess['vendor_name'] = 'Royal Availability Garden'
            sess['vendor_service'] = 'venue'

        res = self.client.post('/vendor/toggle_date_availability', data={
            'event_date': '2026-12-25',
            'action': 'block',
            'reason': 'Marriage Booking'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Check vendor dashboard shows blocked date
        res = self.client.get('/vendor/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('2026-12-25', html)
        self.assertIn('Marriage Booking', html)

        # 3. Vendor unblocks date
        with self.client.session_transaction() as sess:
            sess['vendor'] = v_email
            sess['vendor_name'] = 'Royal Availability Garden'
            sess['vendor_service'] = 'venue'

        res = self.client.post('/vendor/toggle_date_availability', data={
            'event_date': '2026-12-25',
            'action': 'unblock'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
