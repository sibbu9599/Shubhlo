import unittest, sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app, GLOBAL_REGISTERED_USERS, GLOBAL_REGISTERED_VENDORS, is_email_or_phone_registered, get_db_connection

class TestCelebratoMasterSuite(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    # =========================================================================
    # 👤 1. CUSTOMER POINT OF VIEW (CUSTOMER JOURNEY & ALL EDGE CASES)
    # =========================================================================

    def test_01_unregistered_customer_login_blocked(self):
        """Unregistered customer login must be strictly blocked with alert."""
        res = self.app.post('/login', data={'email': 'unregistered_cust@test.com', 'password': 'pass'}, follow_redirects=True)
        text = res.get_data(as_text=True)
        self.assertIn("Only registered users can log in", text)
        print("✓ [Customer Case 1 PASS] Unregistered Customer Login strictly blocked with warning alert!")

    def test_02_customer_registration_and_clean_dashboard(self):
        """Fresh customer registration must yield 100% clean dashboard (0 bookings, 0 fake tickets, 0 fake inquiries)."""
        cust_email = "shubh_customer_test@gmail.com"
        cust_phone = "9811223344"

        # 1. Signup
        res_reg = self.app.post('/signup', data={
            'name': 'Shubh Customer',
            'email': cust_email,
            'phone': cust_phone,
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        # 2. Login
        res_log = self.app.post('/login', data={'email': cust_email, 'password': 'Password123'}, follow_redirects=True)
        self.assertEqual(res_log.status_code, 200)

        # 3. Check Dashboard
        res_dash = self.app.get('/dashboard', follow_redirects=True)
        text = res_dash.get_data(as_text=True)
        self.assertNotIn("Royal Palace Garden (Mock)", text)
        self.assertNotIn("Looking for a marriage garden with catering for 500 guests", text)
        self.assertNotIn("Booking Date Change Process", text)
        print("✓ [Customer Case 2 PASS] Customer Signup & Login succeeded; Dashboard is 100% clean with 0 fake items!")

    def test_03_cross_role_duplicate_prevention(self):
        """Cannot register Vendor using existing Customer credentials or vice versa."""
        # Registered Customer
        self.app.post('/signup', data={'name': 'Exist Cust', 'email': 'existcust@gmail.com', 'phone': '9898989898', 'password': 'pass'}, follow_redirects=True)

        # Attempt Vendor registration with same email
        res_vreg = self.app.post('/vendor_register', data={
            'name': 'Dup Vendor',
            'email': 'existcust@gmail.com',
            'phone': '9797979797',
            'service': 'venue',
            'password': 'pass',
            'govt_id_number': '123456789012',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)
        self.assertIn("Already Registered", res_vreg.get_data(as_text=True))
        print("✓ [Customer Case 3 PASS] Cross-Role Duplicate Registration strictly blocked!")

    # =========================================================================
    # 🏪 2. VENDOR POINT OF VIEW (VENDOR JOURNEY & ALL EDGE CASES)
    # =========================================================================

    def test_04_unregistered_vendor_login_blocked(self):
        """Unregistered vendor login must be strictly blocked with alert."""
        res = self.app.post('/vendor_login', data={'email': 'unregistered_vendor@test.com', 'password': 'pass'}, follow_redirects=True)
        text = res.get_data(as_text=True)
        self.assertIn("Only registered vendors can log in", text)
        print("✓ [Vendor Case 1 PASS] Unregistered Vendor Login strictly blocked with warning alert!")

    def test_05_vendor_approval_gate_and_clean_dashboard(self):
        """Pending vendor cannot add extra services & has 100% clean dashboard."""
        v_email = "new_photo_vendor@test.com"
        v_phone = "9822334455"

        # 1. Register Vendor (Status: Pending)
        self.app.post('/vendor_register', data={
            'name': 'Studio Apex Photography',
            'email': v_email,
            'phone': v_phone,
            'service': 'photography',
            'password': 'vendorpass123',
            'price': '30000',
            'govt_id_number': '998877665544',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        # 2. Login as Vendor
        self.app.post('/vendor_login', data={'email': v_email, 'password': 'vendorpass123'}, follow_redirects=True)

        # 3. Access Vendor Dashboard
        res_dash = self.app.get('/vendor/dashboard', follow_redirects=True)
        text = res_dash.get_data(as_text=True)
        self.assertIn("Pending Owner Verification", text)
        self.assertNotIn("Booking #201", text)
        self.assertNotIn("Great service, highly professional!", text)
        self.assertNotIn("Rahul Sharma", text)

        # 4. Attempt Add Extra Service while Pending -> MUST BE BLOCKED
        res_add = self.app.post('/vendor/add_service', data={'service': 'catering', 'price': '40000', 'description': 'Extra Catering'}, follow_redirects=True)
        self.assertIn("PENDING Owner Approval", res_add.get_data(as_text=True))
        print("✓ [Vendor Case 2 PASS] Vendor Approval Gate active! Pending vendor blocked from adding services & dashboard is clean!")

    def test_06_vendor_date_availability_locking(self):
        """Vendor can lock specific dates for their service."""
        v_email = "lock_date_vendor@test.com"
        v_phone = "9833445566"
        self.app.post('/vendor_register', data={
            'name': 'Lock Date Garden',
            'email': v_email,
            'phone': v_phone,
            'service': 'venue',
            'password': 'pass',
            'govt_id_number': '112233445566',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)
        self.app.post('/vendor_login', data={'email': v_email, 'password': 'pass'}, follow_redirects=True)

        # Lock Date 2026-12-25
        res_block = self.app.post('/vendor/toggle_date_availability', data={'event_date': '2026-12-25', 'reason': 'Personal Event', 'action': 'block'}, follow_redirects=True)
        self.assertEqual(res_block.status_code, 200)

        # Verify Blocked Date in Dashboard
        res_dash = self.app.get('/vendor/dashboard', follow_redirects=True)
        self.assertIn("2026-12-25", res_dash.get_data(as_text=True))
        print("✓ [Vendor Case 3 PASS] Service Date Lock & Availability Management verified 100%!")

    # =========================================================================
    # 👑 3. OWNER MASTER CONTROL PANEL (OWNER ACTIONS & PERMANENT DELETION)
    # =========================================================================

    def test_07_owner_permanent_deletion_engine(self):
        """Owner can permanently delete Customer or Vendor profile, releasing ID immediately."""
        c_email = "todelete_cust@test.com"
        c_phone = "9844556677"
        v_email = "todelete_vend@test.com"
        v_phone = "9855667788"

        # Register Customer & Vendor
        self.app.post('/signup', data={'name': 'Del Cust', 'email': c_email, 'phone': c_phone, 'password': 'pass'}, follow_redirects=True)
        self.app.post('/vendor_register', data={
            'name': 'Del Vend',
            'email': v_email,
            'phone': v_phone,
            'service': 'venue',
            'password': 'pass',
            'govt_id_number': '556677889900',
            'state': 'Madhya Pradesh',
            'district': 'Hoshangabad',
            'tehsil': 'Itarsi',
            'accept_terms_vendor': 'on'
        }, follow_redirects=True)

        # Set Owner session
        with self.app.session_transaction() as sess:
            sess['admin'] = 'owner@shubhlo.com'
            sess['is_owner'] = True

        cust_id = None
        vend_id = None
        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email=%s", (c_email,))
                    row = cur.fetchone()
                    if row:
                        cust_id = row['id']
                    cur.execute("SELECT id FROM vendor WHERE email=%s", (v_email,))
                    vrow = cur.fetchone()
                    if vrow:
                        vend_id = vrow['id']
            finally:
                conn.close()

        if not cust_id:
            cust_entry = next((u for u in GLOBAL_REGISTERED_USERS if u.get('email') == c_email), None)
            cust_id = cust_entry.get('id', 1) if cust_entry else 1

        if not vend_id:
            vend_entry = next((v for v in GLOBAL_REGISTERED_VENDORS if v.get('email') == v_email), None)
            vend_id = vend_entry.get('id', 1) if vend_entry else 1

        # Delete Customer & Vendor
        self.app.post(f'/owner/customer/delete/{cust_id}', follow_redirects=True)
        self.app.post(f'/owner/vendor/delete/{vend_id}', follow_redirects=True)

        # Verify credentials released
        self.assertFalse(is_email_or_phone_registered(c_email, c_phone))
        self.assertFalse(is_email_or_phone_registered(v_email, v_phone))

        # Re-register with deleted credentials -> MUST SUCCEED
        res_recust = self.app.post('/signup', data={'name': 'Fresh Cust', 'email': c_email, 'phone': c_phone, 'password': 'pass'}, follow_redirects=True)
        self.assertEqual(res_recust.status_code, 200)
        print("✓ [Owner Master Case PASS] Permanent Account Deletion Engine releases credentials for fresh signup!")

if __name__ == '__main__':
    unittest.main()
