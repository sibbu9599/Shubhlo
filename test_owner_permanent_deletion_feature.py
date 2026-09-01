import unittest, sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app, GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_USERS, is_email_or_phone_registered

class TestOwnerPermanentDeletionFeature(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_owner_permanent_deletion(self):
        # 1. Register a Customer & a Vendor
        c_email = "delete_target_cust@shubhlo.com"
        c_phone = "8877665544"
        v_email = "delete_target_vend@shubhlo.com"
        v_phone = "7766554433"

        self.app.post('/signup', data={'name': 'Delete Cust', 'email': c_email, 'phone': c_phone, 'password': 'p'}, follow_redirects=True)
        self.app.post('/vendor_register', data={'name': 'Delete Vend', 'email': v_email, 'phone': v_phone, 'service': ['venue'], 'description': 'd', 'govt_id_number': '123', 'password': 'p', 'price': '100', 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Itarsi', 'accept_terms_vendor': 'on'}, follow_redirects=True)

        self.assertTrue(any(u.get('email') == c_email or u.get('phone') == c_phone for u in GLOBAL_REGISTERED_USERS))
        self.assertTrue(any(v.get('email') == v_email or v.get('phone') == v_phone for v in GLOBAL_REGISTERED_VENDORS))
        print("\n[PASS 1] Customer and Vendor registered successfully!")

        # 2. Log in as Owner
        with self.app.session_transaction() as sess:
            sess['admin'] = 'owner@shubhlo.com'
            sess['is_owner'] = True

        # Find customer & vendor IDs
        cust_entry = next((u for u in GLOBAL_REGISTERED_USERS if u.get('email') == c_email), None)
        vend_entry = next((v for v in GLOBAL_REGISTERED_VENDORS if v.get('email') == v_email), None)

        cust_id = cust_entry.get('id', 1) if cust_entry else 1
        vend_id = vend_entry.get('id', 1) if vend_entry else 1

        # 3. Owner Deletes Customer
        del_c_res = self.app.post(f'/owner/customer/delete/{cust_id}', follow_redirects=True)
        self.assertEqual(del_c_res.status_code, 200)
        self.assertFalse(is_email_or_phone_registered(c_email, c_phone))
        print("[PASS 2] Customer account PERMANENTLY DELETED by Owner!")

        # 4. Owner Deletes Vendor
        del_v_res = self.app.post(f'/owner/vendor/delete/{vend_id}', follow_redirects=True)
        self.assertEqual(del_v_res.status_code, 200)
        self.assertFalse(is_email_or_phone_registered(v_email, v_phone))
        print("[PASS 3] Vendor account PERMANENTLY DELETED by Owner!")

        # 5. Verify re-registration with those deleted credentials now succeeds!
        re_signup = self.app.post('/signup', data={'name': 'New Cust', 'email': c_email, 'phone': c_phone, 'password': 'p'}, follow_redirects=True)
        self.assertEqual(re_signup.status_code, 200)
        self.assertTrue(any(u.get('email') == c_email or u.get('phone') == c_phone for u in GLOBAL_REGISTERED_USERS))
        print("[PASS 4] Re-registration with deleted credentials successfully allowed!")

if __name__ == '__main__':
    unittest.main()
