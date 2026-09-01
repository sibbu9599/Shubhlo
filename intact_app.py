import os, json, re, py_compile

brain_dir = r'C:\Users\Shailendra Singh\.gemini\antigravity-ide\brain'
target_app = r'c:\Users\Shailendra Singh\OneDrive\Desktop\celebrato project\app.py'

routes = {}

def add_route(func_name, code_str):
    code_str = code_str.strip()
    if func_name not in routes or len(code_str) > len(routes[func_name]):
        routes[func_name] = code_str

for root, dirs, files in os.walk(brain_dir):
    for f in files:
        if f in ['transcript_full.jsonl', 'transcript.jsonl']:
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                for line in fp:
                    if 'app.py' in line:
                        try:
                            data = json.loads(line)
                            for tc in data.get('tool_calls', []):
                                args = tc.get('args', {})
                                c = args.get('CodeContent') or args.get('ReplacementContent')
                                tf = args.get('TargetFile', '')
                                if c and 'app.py' in tf:
                                    blocks = re.split(r'\n(?=@app\.route|def )', c)
                                    for b in blocks:
                                        b_str = b.strip()
                                        if b_str.startswith('@app.route') or b_str.startswith('def '):
                                            m = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', b_str)
                                            if m:
                                                add_route(m.group(1), b_str)
                        except:
                            pass

header = """from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
import os
import random

app = Flask(__name__)
app.secret_key = "shubhlo_super_secret_key"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOW_ALL_LOCATIONS = True

@app.template_filter('format_date_indian')
def format_date_indian(value):
    if not value:
        return ""
    try:
        if isinstance(value, str):
            parts = value.split('-')
            if len(parts) == 3:
                return f"{parts[2]}/{parts[1]}/{parts[0]}"
        elif hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')
    except Exception:
        pass
    return str(value)

def get_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='shubhlo_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def migrate_db_schema():
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW COLUMNS FROM booking LIKE 'advance_paid'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE booking ADD COLUMN advance_paid DECIMAL(10, 2) DEFAULT 0.00")
                    conn.commit()

                cursor.execute("SHOW COLUMNS FROM booking LIKE 'target_budget'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE booking ADD COLUMN target_budget DECIMAL(10, 2) DEFAULT NULL")
                    conn.commit()

                cursor.execute("SHOW COLUMNS FROM booking LIKE 'budget_flexible'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE booking ADD COLUMN budget_flexible VARCHAR(20) DEFAULT 'Negotiable'")
                    conn.commit()

                cursor.execute("SHOW COLUMNS FROM booking LIKE 'counter_offer_amount'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE booking ADD COLUMN counter_offer_amount DECIMAL(10, 2) DEFAULT NULL")
                    conn.commit()

                cursor.execute("SHOW COLUMNS FROM booking LIKE 'counter_note'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE booking ADD COLUMN counter_note TEXT DEFAULT NULL")
                    conn.commit()

                cursor.execute("SHOW COLUMNS FROM booking LIKE 'counter_offer_status'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE booking ADD COLUMN counter_offer_status VARCHAR(20) DEFAULT 'Pending'")
                    conn.commit()

                cursor.execute("SHOW COLUMNS FROM vendor LIKE 'min_order_value'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE vendor ADD COLUMN min_order_value DECIMAL(10, 2) DEFAULT 0.00")
                    conn.commit()

                cursor.execute("SHOW TABLES LIKE 'vendor_availability'")
                if not cursor.fetchone():
                    cursor.execute(\"\"\"
                        CREATE TABLE vendor_availability (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            vendor_id INT NOT NULL,
                            event_date DATE NOT NULL,
                            status VARCHAR(20) DEFAULT 'Blocked',
                            reason VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (vendor_id) REFERENCES vendor(id) ON DELETE CASCADE
                        )
                    \"\"\")
                    conn.commit()

                cursor.execute("SHOW TABLES LIKE 'permitted_locations'")
                if not cursor.fetchone():
                    cursor.execute(\"\"\"
                        CREATE TABLE permitted_locations (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            state VARCHAR(100) NOT NULL,
                            district VARCHAR(100) NOT NULL,
                            tehsil VARCHAR(100) NOT NULL
                        )
                    \"\"\")
                    cursor.execute(\"\"\"
                        INSERT INTO permitted_locations (state, district, tehsil) VALUES
                        ('Madhya Pradesh', 'Hoshangabad', 'Itarsi'),
                        ('Madhya Pradesh', 'Hoshangabad', 'Sohagpur'),
                        ('Madhya Pradesh', 'Hoshangabad', 'Pipariya'),
                        ('Madhya Pradesh', 'Hoshangabad', 'Narmadapuram'),
                        ('Madhya Pradesh', 'Indore', 'Indore'),
                        ('Madhya Pradesh', 'Bhopal', 'Bhopal')
                    \"\"\")
                    conn.commit()

                cursor.execute("SHOW TABLES LIKE 'system_settings'")
                if not cursor.fetchone():
                    print("Creating 'system_settings' table...")
                    cursor.execute(\"\"\"
                        CREATE TABLE system_settings (
                            setting_key VARCHAR(50) PRIMARY KEY,
                            setting_value VARCHAR(50) DEFAULT 'ON',
                            custom_message TEXT DEFAULT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    \"\"\")
                    cursor.execute(\"\"\"
                        INSERT IGNORE INTO system_settings (setting_key, setting_value, custom_message) VALUES
                        ('allow_customer_booking', 'ON', 'Customer bookings are temporarily paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा ग्राहक बुकिंग फ़िलहाल बंद है।'),
                        ('allow_vendor_registration', 'ON', 'New vendor registrations are currently paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा नया वेंडर रजिस्ट्रेशन फ़िलहाल बंद है।')
                    \"\"\")
                    conn.commit()

                print("Database migration checks complete.")
        except Exception as e:
            print(f"Error during database migration: {e}")
        finally:
            conn.close()

def get_system_setting(setting_key):
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT setting_value, custom_message FROM system_settings WHERE setting_key=%s", (setting_key,))
                row = cursor.fetchone()
                if row:
                    return row['setting_value'], row['custom_message']
        except Exception as e:
            print(f"Error fetching system setting {setting_key}: {e}")
        finally:
            conn.close()

    mock_settings = session.get('mock_system_settings', {
        'allow_customer_booking': {'value': 'ON', 'msg': 'Customer bookings are temporarily paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा ग्राहक बुकिंग फ़िलहाल बंद है।'},
        'allow_vendor_registration': {'value': 'ON', 'msg': 'New vendor registrations are currently paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा नया वेंडर रजिस्ट्रेशन फ़िलहाल बंद है।'}
    })
    st = mock_settings.get(setting_key, {'value': 'ON', 'msg': ''})
    return st.get('value', 'ON'), st.get('msg', '')

FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "")
SMTP_SENDER_EMAIL = os.environ.get("SMTP_SENDER_EMAIL", "your-email@gmail.com")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "xxxx xxxx xxxx xxxx")

def send_email_otp(recipient_email, otp):
    if not recipient_email or "@" not in recipient_email:
        return False
    if SMTP_SENDER_EMAIL == "your-email@gmail.com":
        print(f"[SMTP SKIPPED]: Set SMTP_SENDER_EMAIL and SMTP_APP_PASSWORD env vars to send real emails.")
        return False
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Shubhlo Password Reset OTP"
        body = f"Hello, Your Shubhlo password reset OTP is {otp}. It is valid for 5 minutes. Regards, Shubhlo Team"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_SENDER_EMAIL, SMTP_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[SMTP EMAIL SENT TO {recipient_email}]: OTP {otp} dispatched.")
        return True
    except Exception as e:
        print(f"SMTP Dispatch Error to {recipient_email}: {e}")
        return False

def send_sms_notification(recipient_type, phone, message):
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO simulated_sms (recipient, phone, message) VALUES (%s, %s, %s)",
                    (recipient_type, phone, message)
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving simulated SMS: {e}")
        finally:
            conn.close()
    else:
        mock_sms = session.get('mock_sms', [])
        mock_sms.append({
            'id': len(mock_sms) + 1,
            'recipient': recipient_type,
            'phone': phone,
            'message': message
        })
        session['mock_sms'] = mock_sms
        session.modified = True
    print(f"[{recipient_type.upper()} NOTIFICATION to {phone}]: {message}")

def is_blacklisted(value):
    if not value:
        return False
    clean_val = str(value).strip().lower()
    if clean_val.isdigit():
        clean_val = clean_val[-10:]
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                if clean_val.isdigit():
                    cursor.execute("SELECT id FROM blacklist WHERE value = %s OR value LIKE %s", (clean_val, f"%{clean_val}"))
                else:
                    cursor.execute("SELECT id FROM blacklist WHERE value = %s", (clean_val,))
                if cursor.fetchone():
                    return True
        except Exception as e:
            print(f"Error checking blacklist: {e}")
        finally:
            conn.close()
    else:
        mock_blacklist = session.get('mock_blacklist', [])
        for entry in mock_blacklist:
            b_val = str(entry.get('value', '')).strip().lower()
            if b_val.isdigit():
                b_val = b_val[-10:]
            if clean_val == b_val:
                return True
    return False

MOCK_VENDORS = {
    'venue': [
        {'id': 1, 'name': 'Royal Palace Garden (Mock)', 'price': 150000.00, 'description': 'Grand marriage garden with large capacity and scenic view.', 'photo': '/static/vanue.png', 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Itarsi'},
        {'id': 2, 'name': 'Green Meadow Lawns (Mock)', 'price': 120000.00, 'description': 'Elegant open lawns for outdoor pre-wedding and reception.', 'photo': '/static/vanue.png', 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Sohagpur'}
    ],
    'catering': [
        {'id': 3, 'name': 'Shahi Caterers (Mock)', 'price': 50000.00, 'description': 'Excellent multi-cuisine wedding catering services.', 'photo': '/static/catering.png', 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Itarsi'},
        {'id': 4, 'name': 'Spicy Bites Catering (Mock)', 'price': 45000.00, 'description': 'Specialize in spicy chat, street food, and delicious desserts.', 'photo': '/static/catering.png', 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Sohagpur'}
    ]
}

def fetch_vendors_by_service(service_name, tehsil=None):
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                if tehsil:
                    cursor.execute(
                        \"\"\"SELECT v.id, v.name, v.price, COALESCE(v.min_order_value, 0) AS min_order_value, v.description, v.photo, v.state, v.district, v.tehsil,
                        COALESCE(AVG(r.stars), 0) AS average_rating,
                        COUNT(r.id) AS rating_count
                        FROM vendor v
                        LEFT JOIN rating r ON v.name = r.vendor_name
                        WHERE v.service=%s AND v.tehsil=%s AND (v.approval_status IS NULL OR v.approval_status='Approved')
                        GROUP BY v.id, v.name, v.price, v.min_order_value, v.description, v.photo, v.state, v.district, v.tehsil\"\"\",
                        (service_name, tehsil)
                    )
                else:
                    cursor.execute(
                        \"\"\"SELECT v.id, v.name, v.price, COALESCE(v.min_order_value, 0) AS min_order_value, v.description, v.photo, v.state, v.district, v.tehsil,
                        COALESCE(AVG(r.stars), 0) AS average_rating,
                        COUNT(r.id) AS rating_count
                        FROM vendor v
                        LEFT JOIN rating r ON v.name = r.vendor_name
                        WHERE v.service=%s AND (v.approval_status IS NULL OR v.approval_status='Approved')
                        GROUP BY v.id, v.name, v.price, v.min_order_value, v.description, v.photo, v.state, v.district, v.tehsil\"\"\",
                        (service_name,)
                    )
                vendors = cursor.fetchall()
                for v in vendors:
                    v['average_rating'] = float(v['average_rating']) if v.get('average_rating') else 0.0
                return vendors if vendors else MOCK_VENDORS.get(service_name, [])
        except Exception as e:
            print(f"Error fetching vendors for {service_name}: {e}")
            return MOCK_VENDORS.get(service_name, [])
        finally:
            conn.close()
    return MOCK_VENDORS.get(service_name, [])
"""

# Assemble in logical order
ordered_funcs = [
    'home', 'index', 'about', 'services', 'contact', 'advertisement',
    'login', 'signup', 'logout', 'forget_password', 'verify_reset_otp', 'reset_password',
    'admin_dashboard', 'admin_update_system_settings', 'admin_approve_vendor', 'admin_reject_vendor',
    'admin_add_allowed_location', 'admin_delete_allowed_location', 'get_allowed_locations',
    'admin_approve_booking', 'admin_reject_booking', 'admin_delete_booking', 'admin_delete_vendor',
    'admin_edit_vendor', 'admin_delete_message', 'admin_delete_sms', 'admin_clear_all_sms', 'admin_blacklist_add',
    'vendor_login', 'vendor_register', 'vendor_register_new', 'vendor_dashboard', 'vendor_verify_otp',
    'vendor_update', 'vendor_update_pricing', 'vendor_switch_service', 'vendor_add_service',
    'vendor_toggle_date_availability', 'vendor_logout', 'vendor_counter_offer',
    'booking1', 'booking2', 'booking_verification', 'confirm_booking', 'pay', 'process_payment', 'quick_inquiry',
    'user_respond_counter_offer', 'reassign_booking', 'cancel_booking'
]

full_app_parts = [header]

for fn in ordered_funcs:
    if fn in routes:
        full_app_parts.append(routes[fn])

# Include any remaining routes
for fn, code_str in routes.items():
    if fn not in ordered_funcs and fn not in ['migrate_db_schema', 'get_system_setting', 'send_email_otp', 'send_sms_notification', 'is_blacklisted', 'fetch_vendors_by_service', 'get_db_connection', 'format_date_indian']:
        full_app_parts.append(code_str)

tail = """if __name__ == '__main__':
    migrate_db_schema()
    app.run(debug=True, host='0.0.0.0', port=8080)
"""

full_app_parts.append(tail)

full_app_code = '\n\n'.join(full_app_parts)
full_app_code = full_app_code.replace('Celebrato', 'Shubhlo').replace('celebrato', 'shubhlo')

with open(target_app, 'w', encoding='utf-8') as f:
    f.write(full_app_code)

print(f"Reconstructed app.py ({len(full_app_code)} bytes). Compiling...")
py_compile.compile(target_app, doraise=True)
print("SUCCESS: app.py compiled cleanly with zero syntax errors!")
