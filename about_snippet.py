import sys
import unittest
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath('.'))

from app import app

class ComprehensiveCelebratoTestSuite(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_public_pages(self):
        """Test public pages and session redirects"""
        public_routes = ['/services', '/about', '/contact', '/terms', '/rating', '/api/allowed-locations', '/login', '/vendor/login', '/vendor/register']
        for route in public_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed with status {res.status_code}")

        # Home redirects to login if unauthenticated
        res = self.client.get('/home')
        self.assertEqual(res.status_code, 302)

        # Home renders 200 when authenticated
        with self.client.session_transaction() as sess:
            sess['user'] = 'testuser@example.com'
        res = self.client.get('/home')
        self.assertEqual(res.status_code, 200)

    def test_02_excluded_categories_purge(self):
        """Ensure Pandit and Mocktail are completely excluded from services page"""
        res = self.client.get('/services')
        html = res.data.decode('utf-8')
        self.assertNotIn('Pandit & Priest', html)
        self.assertNotIn('Mocktail & Juice', html)
        self.assertNotIn('pandit', html.lower())
        self.assertNotIn('mocktail', html.lower())

    def test_03_customer_booking_flow(self):
        """Test complete multi-step customer booking and ₹5,100 token advance calculation"""
        # Set logged-in customer session
        with self.client.session_transaction() as sess:
            sess['user'] = 'rohan@example.com'
            sess['user_name'] = 'Rohan Verma'

        # Step 1: Submit event location & date details (booking1)
        res = self.client.post('/booking1', data={
            'name': 'Rohan Verma',
            'email': 'rohan@example.com',
            'phone': '9876543210',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'event_date': '2026-11-20',
            'address': 'House 45, Station Road'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Step 2: Render booking2 vendor selection page
        res = self.client.get('/booking2')
        self.assertEqual(res.status_code, 200)

        # Step 3: Select vendors and submit to confirm_booking
        res = self.client.post('/confirm_booking', data={
            'venue': 'Royal Palace Garden',
            'catering': 'Shahi Royal Caterers'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        
        # Token Advance for 2 services should be 2 * 5100 = 10,200
        self.assertIn('10,200', html)
        self.assertNotIn('Grand Total (कुल लागत)', html) # Grand total estimate must be purged

        # Step 4: Accept Terms & Proceed to Pay
        res = self.client.post('/pay', data={'accept_terms': 'on'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Step 5: Process Payment
        res = self.client.post('/process-payment', data={
            'name': 'Rohan Verma',
            'email': 'rohan@example.com',
            'phone': '9876543210',
            'amount': '150000.00',
            'token_advance': '10200.00',
            'method': 'upi'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_04_vendor_contact_locking_and_unlocking(self):
        """Test that unconfirmed bookings lock customer contact, and admin approval unlocks it"""
        with self.client.session_transaction() as sess:
            sess['vendor'] = 'royal_palace@celebrato.com'
            sess['vendor_name'] = 'Royal Palace Garden'
            sess['vendor_service'] = 'venue'
            sess['vendor_id'] = 101
            sess['mock_bookings'] = [{
                'id': 501,
                'name': 'Amit Kumar',
                'email': 'amit@example.com',
                'phone': '9123456789',
                'address': 'Secret Street 12',
                'state': 'Madhya Pradesh',
                'district': 'Hoshangabad',
                'tehsil': 'Itarsi',
                'event_date': '2026-12-01',
                'venue': 'Royal Palace Garden',
                'amount': 50000,
                'advance_paid': 5100,
                'payment_status': 'Token Paid',
                'booking_status': 'Pending' # Initial state
            }]

        # 1. Vendor dashboard view when Pending -> Must be LOCKED
        res = self.client.get('/vendor/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Locked / एडमिन की पुष्टि का इंतज़ार', html)
        self.assertIn('Hidden until Master Admin Confirms', html)
        self.assertNotIn('Secret Street 12', html)

        # 2. Admin approves booking
        with self.client.session_transaction() as sess:
            sess['admin'] = 'admin@celebrato.com'
        
        res = self.client.post('/admin/approve_booking/501', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 3. Vendor dashboard view when Confirmed -> Must be UNLOCKED
        with self.client.session_transaction() as sess:
            sess['vendor'] = 'royal_palace@celebrato.com'
            sess['vendor_name'] = 'Royal Palace Garden'
            sess['vendor_service'] = 'venue'
        
        res = self.client.get('/vendor/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Amit Kumar', html)
        self.assertIn('9123456789', html)
        self.assertIn('Secret Street 12', html)

    def test_05_vendor_registration_notice_wording(self):
        """Verify bilingual notice and 1-week timeline wording on vendor registration page"""
        res = self.client.get('/vendor/register')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('within 1 week (7 days)', html)
        self.assertIn('1 हफ्ते (7 दिनों) के भीतर', html)
        self.assertIn('₹4,500', html)
        self.assertNotIn('Starting Price (₹)', html)

    def test_06_admin_dashboard_controls(self):
        """Test admin dashboard statistics and deletion/blacklist endpoints"""
        with self.client.session_transaction() as sess:
            sess['admin'] = 'admin@celebrato.com'

        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Owner Control Panel', html)
        self.assertIn('Admin Earnings', html)
        self.assertIn('Vendor Payables', html)

if __name__ == '__main__':
    unittest.main()
