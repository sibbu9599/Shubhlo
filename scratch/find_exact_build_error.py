import os
import glob
from app import app
from flask import render_template, session
from werkzeug.routing import BuildError

template_files = glob.glob("templates/**/*.html", recursive=True)

dummy_booking = {
    'booking_id': 'BK12345',
    'id': 1,
    'customer_name': 'Test User',
    'customer_email': 'test@example.com',
    'customer_phone': '9876543210',
    'service_name': 'Catering',
    'event_date': '2026-12-25',
    'guest_count': 100,
    'total_price': 50000,
    'paid_amount': 10000,
    'due_amount': 40000,
    'advance_paid': 10000,
    'payment_status': 'Advance Paid',
    'created_at': '2026-08-31 12:00:00',
    'status': 'Confirmed',
    'selected_services': ['Catering', 'DJ']
}

dummy_vendor = {
    'id': 1,
    'name': 'Test Vendor',
    'email': 'vendor@example.com',
    'phone': '9876543210',
    'service_type': 'Catering',
    'status': 'Approved',
    'business_name': 'Test Vendor Services',
    'service': 'catering'
}

dummy_service = {'service': 'venue', 'price': 50000}

sessions_to_test = [
    {}, # Anonymous / Logged out
    {'user': 'customer@example.com', 'user_id': 1, 'user_name': 'Customer Test', 'role': 'customer'},
    {'vendor': 'vendor@example.com', 'vendor_id': 1, 'vendor_name': 'Vendor Test', 'role': 'vendor'},
    {'admin': 'admin@example.com', 'role': 'admin'},
    {'is_owner': True, 'admin': 'owner@example.com', 'role': 'owner'}
]

print("=== DEEP TEMPLATE RENDERING TEST FOR BUILDERRORS & RENDERING ERRORS ===")

for sess_idx, sess in enumerate(sessions_to_test):
    with app.test_request_context('/'):
        session.clear()
        session.update(sess)

        for tpath in template_files:
            tname = os.path.relpath(tpath, "templates").replace("\\", "/")
            try:
                rendered = render_template(
                    tname,
                    booking=dummy_booking,
                    booking_item=dummy_booking,
                    b=dummy_booking,
                    vendor=dummy_vendor,
                    v=dummy_vendor,
                    vendors=[dummy_vendor],
                    services=[dummy_service],
                    all_services=[dummy_service, {'service': 'dj'}],
                    user={'name': 'Test', 'email': 'test@example.com'},
                    customer={'name': 'Test', 'email': 'test@example.com'},
                    receipt=dummy_booking,
                    permitted_locations=[{'id': 1, 'state': 'MP', 'district': 'Indore', 'tehsil': 'Indore'}],
                    contact_messages=[{'id': 1, 'name': 'John', 'email': 'j@e.com', 'phone': '999', 'message': 'Hi'}],
                    blacklisted_users=[],
                    tehsils=['Indore', 'Itarsi'],
                    deposit_credit=0.0,
                    platform_fee=0.0,
                    tax_amount=0.0,
                    grand_total=50000.0,
                    items=[]
                )
            except BuildError as be:
                print(f"[BUILD ERROR] session #{sess_idx} on template '{tname}': {be}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                print(f"[{type(e).__name__}] session #{sess_idx} on template '{tname}': {e}")
