import unittest
import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.abspath("."))

from app import app

class TestVendorBookingVisibility(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_vendor_dashboard_booking_matching(self):
        with self.app as client:
            with client.session_transaction() as sess:
                sess['vendor'] = 'vendor_test@example.com'
                sess['vendor_name'] = 'Test Vendor Security'
                sess['vendor_service'] = 'security_guard'
                sess['mock_vendors'] = [{
                    'id': 888,
                    'name': 'Test Vendor Security',
                    'email': 'vendor_test@example.com',
                    'phone': '9876543210',
                    'service': 'security_guard',
                    'description': 'Security Guard Service',
                    'price': 15000.00,
                    'photo': '/static/image/logo.png',
                    'approval_status': 'Approved'
                }]
                sess['mock_bookings'] = [{
                    'id': 501,
                    'name': 'Customer Rahul',
                    'email': 'rahul@example.com',
                    'phone': '9876543210',
                    'event_date': '2026-11-20',
                    'amount': 15000.00,
                    'booking_status': 'Confirmed',
                    'security_guard': 'Test Vendor Security',
                    'selected_vendors': [{
                        'category': 'Security Guard',
                        'raw_category': 'security_guard',
                        'name': 'Test Vendor Security',
                        'price': 15000.00
                    }]
                }]
                sess['mock_verifications'] = [{
                    'booking_id': 501,
                    'vendor_name': 'Test Vendor Security',
                    'service_type': 'security_guard',
                    'status': 'Pending',
                    'verified_at': None
                }]

            res = client.get('/vendor_dashboard')
            self.assertEqual(res.status_code, 200)
            html = res.data.decode('utf-8')
            self.assertIn("Booking #501", html)

if __name__ == "__main__":
    unittest.main()
