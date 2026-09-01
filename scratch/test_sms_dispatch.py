import unittest
import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.abspath("."))

from app import send_sms_notification, dispatch_fast2sms, dispatch_twilio

class TestSMSDispatch(unittest.TestCase):

    def test_mock_sms_dispatch(self):
        """Verify that send_sms_notification runs without raising exceptions and outputs log."""
        try:
            send_sms_notification("Customer", "9876543210", "Your Celebrato OTP is 123456. Valid for 5 mins.")
            success = True
        except Exception as e:
            print(f"SMS test failed: {e}")
            success = False
        self.assertTrue(success)

    def test_invalid_phone_handling(self):
        """Verify that dispatch_fast2sms returns False gracefully for invalid phone numbers."""
        os.environ["FAST2SMS_API_KEY"] = "dummy_test_key"
        res = dispatch_fast2sms("invalid_phone", "Test OTP 1234")
        self.assertFalse(res)
        os.environ.pop("FAST2SMS_API_KEY", None)

if __name__ == "__main__":
    unittest.main()
