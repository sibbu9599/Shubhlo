import unittest
import sys
from unittest.mock import patch
sys.stdout.reconfigure(encoding='utf-8')
from app import app, get_db_connection

class TestSafeDealGuaranteeAndRefund(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.get_db_connection', return_value=None)
    def test_alternate_vendor_and_refund_flow(self, mock_db):
        with self.app.session_transaction() as sess:
            sess['user'] = 'testcustomer@shubhlo.com'
            sess['user_name'] = 'Test Customer'
            sess['mock_bookings'] = [
                {
                    'id': 101,
                    'email': 'testcustomer@shubhlo.com',
                    'name': 'Test Customer',
                    'phone': '9876543210',
                    'event_date': '2026-11-25',
                    'venue': 'Royal Palace Itarsi',
                    'amount': 50000.0,
                    'advance_paid': 5118.0,
                    'token_deposit': 5000.0,
                    'booking_status': 'Confirmed',
                    'status': 'Confirmed',
                    'is_otp_verified': False,
                    'tehsil': 'Itarsi',
                    'district': 'Hoshangabad'
                },
                {
                    'id': 102,
                    'email': 'testcustomer@shubhlo.com',
                    'name': 'Test Customer',
                    'phone': '9876543210',
                    'event_date': '2026-12-10',
                    'venue': 'Grand Heritage Venue',
                    'amount': 60000.0,
                    'advance_paid': 5118.0,
                    'token_deposit': 5000.0,
                    'booking_status': 'Confirmed',
                    'status': 'Confirmed',
                    'is_otp_verified': False,
                    'tehsil': 'Itarsi',
                    'district': 'Hoshangabad'
                }
            ]
            sess['mock_vendors'] = [
                {'name': 'Royal Palace Itarsi', 'service': 'venue', 'tehsil': 'Itarsi', 'district': 'Hoshangabad', 'approval_status': 'Approved'},
                {'name': 'Shubh Shagun Marriage Garden', 'service': 'venue', 'tehsil': 'Itarsi', 'district': 'Hoshangabad', 'approval_status': 'Approved'}
            ]

        # 1. Customer requests Free Alternate Vendor for Booking 101
        res1 = self.app.post('/booking/report_deal_issue/101', data={
            'resolution_choice': 'alternate_vendor',
            'deal_issue_reason': 'Vendor ne pehle tay kiye rate se zyada manga',
            'custom_note': 'Vendor asked for 20k extra for lighting'
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        self.assertIn('Safe Guarantee'.encode('utf-8'), res1.data)

        with self.app.session_transaction() as sess:
            b101 = next(b for b in sess['mock_bookings'] if b['id'] == 101)
            self.assertEqual(b101['dispute_status'], 'Alternate Vendor Assigned')
            self.assertIn('Shubh Shagun Marriage Garden', b101['venue'])

        # 2. Customer requests 100% Token Refund for Booking 102
        res2 = self.app.post('/booking/report_deal_issue/102', data={
            'resolution_choice': 'refund',
            'deal_issue_reason': 'Customer changed personal mind',
            'custom_note': 'Event venue shifted to private home'
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn('रिफंड अनुरोध दर्ज'.encode('utf-8'), res2.data)

        with self.app.session_transaction() as sess:
            b102 = next(b for b in sess['mock_bookings'] if b['id'] == 102)
            self.assertEqual(b102['dispute_status'], 'Refund Requested')
            self.assertEqual(b102['booking_status'], 'Refund Requested')
            self.assertEqual(b102['refund_status'], 'Pending Approval')
            self.assertEqual(b102['refund_amount'], 5118.0)

        # 3. Owner approves 100% refund
        with self.app.session_transaction() as sess:
            sess['admin'] = 'owner@shubhlo.com'

        res3 = self.app.post('/owner/process_refund/102', follow_redirects=True)
        self.assertEqual(res3.status_code, 200)

        with self.app.session_transaction() as sess:
            b102_updated = next(b for b in sess['mock_bookings'] if b['id'] == 102)
            self.assertEqual(b102_updated['refund_status'], 'Refund Completed')
            self.assertEqual(b102_updated['dispute_status'], 'Refund Completed')
            self.assertEqual(b102_updated['booking_status'], 'Refunded')

        print("✓ [TEST PASS] 100% Safe Deal Guarantee (Alternate Vendor Reassignment & 100% Refund Processing) verified successfully!")

if __name__ == '__main__':
    unittest.main()
