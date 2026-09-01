import os
import glob
from app import app
from flask import render_template, session
from jinja2.exceptions import TemplateNotFound
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
    'business_name': 'Test Vendor Services'
}

with app.test_request_context('/'):
    session['user_id'] = 1
    session['user_name'] = 'Test User'
    session['user_email'] = 'test@example.com'
    session['role'] = 'customer'
    session['vendor_id'] = 1
    session['is_owner'] = True

    for tpath in template_files:
        tname = os.path.relpath(tpath, "templates").replace("\\", "/")
        try:
            rendered = render_template(
                tname,
                booking=dummy_booking,
                vendor=dummy_vendor,
                vendors=[dummy_vendor],
                services=[],
                user={'name': 'Test', 'email': 'test@example.com'},
                customer={'name': 'Test', 'email': 'test@example.com'},
                receipt=dummy_booking
            )
            print(f"[OK] {tname}")
        except BuildError as be:
            print(f"!!! [BUILD ERROR] in {tname}: {be}")
            import traceback
            traceback.print_exc()
        except TemplateNotFound as tnf:
            print(f"[NOT FOUND] {tname}")
        except Exception as e:
            print(f"!!! [{type(e).__name__}] in {tname}: {e}")
