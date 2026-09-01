from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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
                    cursor.execute("""
                        CREATE TABLE vendor_availability (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            vendor_id INT NOT NULL,
                            event_date DATE NOT NULL,
                            status VARCHAR(20) DEFAULT 'Blocked',
                            reason VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (vendor_id) REFERENCES vendor(id) ON DELETE CASCADE
                        )
                    """)
                    conn.commit()

                cursor.execute("SHOW TABLES LIKE 'permitted_locations'")
                if not cursor.fetchone():
                    cursor.execute("""
                        CREATE TABLE permitted_locations (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            state VARCHAR(100) NOT NULL,
                            district VARCHAR(100) NOT NULL,
                            tehsil VARCHAR(100) NOT NULL
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO permitted_locations (state, district, tehsil) VALUES
                        ('Madhya Pradesh', 'Hoshangabad', 'Itarsi'),
                        ('Madhya Pradesh', 'Hoshangabad', 'Sohagpur'),
                        ('Madhya Pradesh', 'Hoshangabad', 'Pipariya'),
                        ('Madhya Pradesh', 'Hoshangabad', 'Narmadapuram'),
                        ('Madhya Pradesh', 'Indore', 'Indore'),
                        ('Madhya Pradesh', 'Bhopal', 'Bhopal')
                    """)
                    conn.commit()

                cursor.execute("SHOW TABLES LIKE 'system_settings'")
                if not cursor.fetchone():
                    print("Creating 'system_settings' table...")
                    cursor.execute("""
                        CREATE TABLE system_settings (
                            setting_key VARCHAR(50) PRIMARY KEY,
                            setting_value VARCHAR(50) DEFAULT 'ON',
                            custom_message TEXT DEFAULT NULL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute("""
                        INSERT IGNORE INTO system_settings (setting_key, setting_value, custom_message) VALUES
                        ('allow_customer_booking', 'ON', 'Customer bookings are temporarily paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा ग्राहक बुकिंग फ़िलहाल बंद है।'),
                        ('allow_vendor_registration', 'ON', 'New vendor registrations are currently paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा नया वेंडर रजिस्ट्रेशन फ़िलहाल बंद है।')
                    """)
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
    try:
        print(f"[{recipient_type.upper()} NOTIFICATION to {phone}]: {message}")
    except Exception:
        print(f"[{recipient_type.upper()} NOTIFICATION to {phone}]: [SMS message contains non-ASCII characters]")

GLOBAL_REGISTERED_USERS = []
GLOBAL_REGISTERED_VENDORS = []
GLOBAL_VENDOR_AVAILABILITY = []
GLOBAL_SYSTEM_SETTINGS = {}
GLOBAL_VENDOR_RATINGS = {}

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
                        """SELECT v.id, v.name, v.price, COALESCE(v.min_order_value, 0) AS min_order_value, v.description, v.photo, v.state, v.district, v.tehsil,
                        COALESCE(AVG(r.stars), 0) AS average_rating,
                        COUNT(r.id) AS rating_count
                        FROM vendor v
                        LEFT JOIN rating r ON v.name = r.vendor_name
                        WHERE v.service=%s AND v.tehsil=%s AND (v.approval_status IS NULL OR v.approval_status='Approved')
                        GROUP BY v.id, v.name, v.price, v.min_order_value, v.description, v.photo, v.state, v.district, v.tehsil""",
                        (service_name, tehsil)
                    )
                else:
                    cursor.execute(
                        """SELECT v.id, v.name, v.price, COALESCE(v.min_order_value, 0) AS min_order_value, v.description, v.photo, v.state, v.district, v.tehsil,
                        COALESCE(AVG(r.stars), 0) AS average_rating,
                        COUNT(r.id) AS rating_count
                        FROM vendor v
                        LEFT JOIN rating r ON v.name = r.vendor_name
                        WHERE v.service=%s AND (v.approval_status IS NULL OR v.approval_status='Approved')
                        GROUP BY v.id, v.name, v.price, v.min_order_value, v.description, v.photo, v.state, v.district, v.tehsil""",
                        (service_name,)
                    )
                vendors = cursor.fetchall()
                for v in vendors:
                    v['average_rating'] = float(v['average_rating']) if v.get('average_rating') else 0.0
                return vendors if vendors else MOCK_VENDORS.get(service_name, [])
        except Exception as e:
            print(f"Error fetching vendors for {service_name}: {e}")
            registered = [v for v in GLOBAL_REGISTERED_VENDORS if v.get('service') == service_name and v.get('approval_status') == 'Approved']
            return MOCK_VENDORS.get(service_name, []) + registered
        finally:
            conn.close()
    registered = [v for v in GLOBAL_REGISTERED_VENDORS if v.get('service') == service_name and v.get('approval_status') == 'Approved']
    return MOCK_VENDORS.get(service_name, []) + registered


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

# Advertisement & Marketing Hub (प्रचार एवं विज्ञापन केंद्र)

@app.route('/index')
def index():
    return redirect(url_for('home'))

# Home Page (Publicly accessible to everyone)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/servies')
def servies():
    return services()

@app.route('/services')
def services():
    conn = get_db_connection()
    db_vendors = []
    
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM vendor WHERE approval_status='Approved'")
                db_vendors = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching services data from DB: {e}")
        finally:
            conn.close()

    mock_vendors = session.get('mock_vendors', [])
    user_vendors = [v for v in mock_vendors if v.get('approval_status', 'Approved') == 'Approved']
    
    # Combine DB vendors + User registered mock vendors
    all_registered = list(db_vendors) + list(user_vendors)

    # Complete Seed Catalog for all active categories
    default_seed_vendors = [
        {
            'id': 1, 'name': 'Rajput Band & Shahi Sawari', 'email': 'rajput@shubhlo.com', 'phone': '9876543201',
            'service': 'shahi_sawari', 'description': 'Premium bagghis and royal entries with decorated horses.',
            'photo': '/static/image/HOURES.png', 'price': 15000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 2, 'name': 'Milan Garden & Palace', 'email': 'milan@shubhlo.com', 'phone': '9876543202',
            'service': 'venue', 'description': 'Massive wedding lawns with premium stage setup and dynamic lights.',
            'photo': '/static/image/vanue.png', 'price': 120000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 3, 'name': 'Rock DJ Setup & Sound', 'email': 'djrock@shubhlo.com', 'phone': '9876543203',
            'service': 'dj', 'description': 'Heavy bass JBL sound system, laser lights, and dynamic fog screen.',
            'photo': '/static/image/DJ.png', 'price': 22000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Sohagpur', 'approval_status': 'Approved'
        },
        {
            'id': 4, 'name': 'Rasoi Caterers & Sweets', 'email': 'rasoi@shubhlo.com', 'phone': '9876543204',
            'service': 'catering', 'description': 'Pure veg delicious multi-cuisine buffet for up to 2000 guests.',
            'photo': '/static/image/catering.png', 'price': 85000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 5, 'name': 'Royal Security Force', 'email': 'security1@shubhlo.com', 'phone': '9876543222',
            'service': 'security_guard', 'description': 'Professional event bouncers and security guards.',
            'photo': '/static/image/security.png', 'price': 12000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 6, 'name': 'Style & Grace Makeup Studio', 'email': 'makeup1@shubhlo.com', 'phone': '9876543224',
            'service': 'makeup', 'description': 'Bridal makeup, party makeover, and hairstyling.',
            'photo': '/static/makeup.png', 'price': 15000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 7, 'name': 'Radhika Mehendi Art', 'email': 'radhika@shubhlo.com', 'phone': '9876543226',
            'service': 'mehendi', 'description': 'Bridal Rajasthani and Arabic mehendi designs.',
            'photo': '/static/image/mehendi.png', 'price': 8000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 8, 'name': 'Royal Punjabi Dhol Group', 'email': 'punjabidhol@shubhlo.com', 'phone': '9876543228',
            'service': 'dhol_band', 'description': 'Punjabi dhol group with traditional wedding beats.',
            'photo': '/static/image/dhol_band.png', 'price': 15000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 10, 'name': 'Bollywood Dance Academy', 'email': 'danceacademy@shubhlo.com', 'phone': '9876543232',
            'service': 'choreographer', 'description': 'Specialized sangeet wedding choreography, couples entries, and group dances.',
            'photo': '/static/image/choreographer.png', 'price': 20000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 11, 'name': 'Dream Event Planners', 'email': 'dreamplanners@shubhlo.com', 'phone': '9876543234',
            'service': 'wedding_planner', 'description': 'Full-service event planning, coordination, theme curation, and execution.',
            'photo': '/static/image/wedding_planner.png', 'price': 50000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 12, 'name': 'Anchor Rohit & Team', 'email': 'rohit@shubhlo.com', 'phone': '9876543236',
            'service': 'anchor', 'description': 'Professional emcee and stage host for wedding sangeet, reception, and games.',
            'photo': '/static/image/anchor.png', 'price': 15000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 13, 'name': 'Royal Pyro & Fireworks', 'email': 'pyro@shubhlo.com', 'phone': '9876543238',
            'service': 'fireworks', 'description': 'Luxury cold pyro sparklers, event entry fog, aerial fireworks, and sound effects.',
            'photo': '/static/image/fireworks.png', 'price': 15000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 14, 'name': 'Moments Photography & Studio', 'email': 'photo@shubhlo.com', 'phone': '9876543244',
            'service': 'photography', 'description': 'Candid wedding photography, cinematic teaser films, and drone coverage.',
            'photo': '/static/image/camera.png', 'price': 35000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 15, 'name': 'Royal Car & Transport Rental', 'email': 'transport@shubhlo.com', 'phone': '9876543246',
            'service': 'transport', 'description': 'Luxury cars for groom, AC buses, and traveler vans for guests.',
            'photo': '/static/image/transpoter.png', 'price': 18000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 16, 'name': 'Grand Theme Decorators', 'email': 'decor@shubhlo.com', 'phone': '9876543248',
            'service': 'decoration', 'description': 'Theme flower decorations, royal mandate stage setups, and entrance gates.',
            'photo': '/static/image/decoration.png', 'price': 45000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 17, 'name': 'Royal Invitation Cards & Gifts', 'email': 'cards@shubhlo.com', 'phone': '9876543250',
            'service': 'invitation_card', 'description': 'Digital video invitations, velvet royal boxes, and customized wedding cards.',
            'photo': '/static/image/invitation_card.png', 'price': 12000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        },
        {
            'id': 18, 'name': 'Royal Mewari Safa House', 'email': 'royalmewari@shubhlo.com', 'phone': '9876543242',
            'service': 'safa', 'description': 'Traditional Mewari and Jodhpuri royal safa tying services, premium fabrics for groom and guests.',
            'photo': '/static/image/safa.png', 'price': 8000, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad',
            'tehsil': 'Itarsi', 'approval_status': 'Approved'
        }
    ]

    # Combine registered with seed vendors without duplicates
    registered_keys = {(v.get('email'), v.get('service')) for v in all_registered if v.get('email') and v.get('service')}
    final_vendors = list(all_registered)
    
    for sv in default_seed_vendors:
        if (sv['email'], sv['service']) not in registered_keys:
            final_vendors.append(sv)

    active_tehsils = {v['tehsil'] for v in final_vendors if v.get('tehsil')}
    sorted_tehsils = sorted(list(active_tehsils))

    return render_template(
        'services.html',
        vendors=final_vendors,
        tehsils=sorted_tehsils
    )

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        message_type = request.form.get('message_type', 'General Inquiry')
        message = request.form.get('message', '').strip()

        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        new_msg = {
            'id': len(GLOBAL_CONTACT_MESSAGES) + 1,
            'name': name,
            'phone': phone,
            'email': email,
            'message_type': message_type,
            'message': message,
            'status': 'New',
            'owner_reply': '',
            'created_at': now_str
        }
        GLOBAL_CONTACT_MESSAGES.insert(0, new_msg)

        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS contact_messages (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(255),
                            phone VARCHAR(50),
                            email VARCHAR(255),
                            message_type VARCHAR(100),
                            message TEXT,
                            status VARCHAR(50) DEFAULT 'New',
                            owner_reply TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cursor.execute(
                        "INSERT INTO contact_messages (name, phone, email, message_type, message, status) VALUES (%s, %s, %s, %s, %s, %s)",
                        (name, phone, email, message_type, message, 'New')
                    )
                    conn.commit()
            except Exception as e:
                print(f"Error saving contact message to DB: {e}")
            finally:
                conn.close()

        if 'mock_contact_messages' not in session:
            session['mock_contact_messages'] = []
        session['mock_contact_messages'].insert(0, new_msg)
        session.modified = True

        flash("Thank you! Your message has been received successfully. Our team will contact you soon.", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/advertisement')
def advertisement():
    return render_template('advertisement.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Please enter both email/phone and password. / कृपया ईमेल/फ़ोन और पासवर्ड दोनों दर्ज करें।", "danger")
            return render_template('login.html')

        # Owner Special Account
        if email == "owner@shubhlo.com" and password == "owner123":
            session['admin'] = email
            session['is_owner'] = True
            flash("Welcome Master Owner! Full system control activated. 👑", "success")
            return redirect(url_for('owner_dashboard'))

        # Admin Special Account
        if email == "admin@shubhlo.com" and password == "admin123":
            session['admin'] = email
            flash("Welcome Admin!", "success")
            return redirect(url_for('admin_dashboard'))

        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE (email=%s OR phone=%s) AND password=%s", (email, email, password))
                    user = cursor.fetchone()
                    if user:
                        session['user'] = user['email']
                        session['user_name'] = user.get('name', 'Customer')
                        flash(f"Welcome back, {session['user_name']}! Login successful 🎉", "success")
                        return redirect(url_for('home'))
                    else:
                        flash("Invalid email/phone or password! Only registered users can log in. / गलत ईमेल/फ़ोन या पासवर्ड! केवल पंजीकृत ग्राहक ही लॉगिन कर सकते हैं।", "danger")
                        return render_template('login.html')
            except Exception as e:
                flash(f"Login error: {e}", "danger")
                return render_template('login.html')
            finally:
                conn.close()
        else:
            # Fallback/Simulated Mode for Mock Users
            mock_users = session.get('mock_users', [
                {'name': 'Demo User', 'email': 'user@shubhlo.com', 'phone': '9876543210', 'password': 'user123'}
            ])
            user = next((u for u in mock_users if (str(u.get('email', '')).lower() == email.lower() or str(u.get('phone', '')) == email) and str(u.get('password', '')) == password), None)
            if user:
                session['user'] = user['email']
                session['user_name'] = user.get('name', 'Customer')
                flash(f"Welcome back, {session['user_name']}! Login successful 🎉", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid email/phone or password! Only registered users can log in. / गलत ईमेल/फ़ोन या पासवर्ड! केवल पंजीकृत ग्राहक ही लॉगिन कर सकते हैं।", "danger")
                return render_template('login.html')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Email and Password are required! / ईमेल और पासवर्ड आवश्यक हैं!", "danger")
            return redirect(url_for('signup'))

        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE email=%s OR phone=%s", (email, phone))
                    if cursor.fetchone():
                        flash("Account with this email or phone already exists. Please login! / इस ईमेल या फ़ोन से खाता पहले से मौजूद है। कृपया लॉगिन करें!", "info")
                        return redirect(url_for('login'))

                    cursor.execute("""
                        INSERT INTO users (name, email, phone, password)
                        VALUES (%s, %s, %s, %s)
                    """, (name or email.split('@')[0], email, phone, password))
                    conn.commit()
                    session['user'] = email
                    session['user_name'] = name or email.split('@')[0]
                    flash("Account created successfully! Welcome to Shubhlo 🎉", "success")
                    return redirect(url_for('home'))
            except Exception as e:
                print(f"Signup DB Error: {e}")
                conn.rollback()
            finally:
                conn.close()

        # Fallback Mock Users mode
        mock_users = session.get('mock_users', [
            {'name': 'Demo User', 'email': 'user@shubhlo.com', 'phone': '9876543210', 'password': 'user123'}
        ])
        if is_email_or_phone_registered(email, phone) or any(u.get('email') == email or (phone and u.get('phone') == phone) for u in mock_users):
            flash("Account with this email or phone already exists. Please login! / इस ईमेल या फ़ोन से खाता पहले से मौजूद है। कृपया लॉगिन करें!", "info")
            return redirect(url_for('login'), code=303)

        new_u = {
            'name': name or email.split('@')[0].capitalize(),
            'email': email,
            'phone': phone,
            'password': password
        }
        mock_users.append(new_u)
        if not any(u['email'] == email for u in GLOBAL_REGISTERED_USERS):
            GLOBAL_REGISTERED_USERS.append(new_u)
        session['mock_users'] = mock_users
        session['user'] = email
        session['user_name'] = new_u['name']
        session.modified = True

        flash("Account registered successfully! Welcome to Shubhlo 🎉", "success")
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/register', methods=['GET', 'POST'])
def signup_alias():
    return signup()

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('admin', None)
    session.pop('vendor', None)
    session.pop('user_name', None)
    session.pop('vendor_name', None)
    session.pop('vendor_service', None)
    session.pop('vendor_id', None)
    session.pop('booking_info', None)
    flash("You have been logged out successfully! / आप सफलतापूर्वक लॉग आउट हो गए हैं।", "info")
    return redirect(url_for('home'))

@app.route('/forget-password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        role = request.form.get('role')
        
        if not user_id or not role:
            flash("Role and Email/Phone are required.", "danger")
            return redirect(url_for('forget_password'))

        import random
        import time

        conn = get_db_connection()
        email_to_reset = None
        phone_to_reset = None
        account_found = False

        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    if role == 'customer':
                        # Find Customer in users table
                        cursor.execute("SELECT * FROM users WHERE email=%s", (user_id,))
                        user = cursor.fetchone()
                        if user:
                            account_found = True
                            email_to_reset = user['email']
                    elif role == 'vendor':
                        # Find Vendor in vendor table (check both email and phone)
                        cursor.execute("SELECT * FROM vendor WHERE email=%s OR phone=%s", (user_id, user_id))
                        vendor = cursor.fetchone()
                        if vendor:
                            account_found = True
                            email_to_reset = vendor['email']
                            phone_to_reset = vendor['phone']
            except Exception as e:
                flash(f"Database error: {e}", "danger")
                return redirect(url_for('forget_password'))
            finally:
                conn.close()
        else:
            # Fallback mock mode
            flash("Database offline. Running in fallback simulation mode.", "warning")
            if role == 'customer':
                # Accept any user_id matching email structure
                if '@' in user_id:
                    account_found = True
                    email_to_reset = user_id
            elif role == 'vendor':
                # Check if it exists in session['mock_vendors']
                session_vendors = session.get('mock_vendors', [])
                matched_v = next((v for v in session_vendors if v['email'] == user_id or v['phone'] == user_id), None)
                if matched_v:
                    account_found = True
                    email_to_reset = matched_v['email']
                    phone_to_reset = matched_v['phone']
                else:
                    # If not registered, let's allow a default simulated user
                    if '@' in user_id or len(user_id) >= 10:
                        account_found = True
                        email_to_reset = user_id if '@' in user_id else f"{user_id}@mockvendor.com"
                        phone_to_reset = user_id if not '@' in user_id else "9876543210"

        if not account_found:
            flash(f"No registered {role} found with details: {user_id}", "danger")
            return redirect(url_for('forget_password'))

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Save reset info in session
        session['reset_otp'] = otp
        session['reset_email'] = email_to_reset
        session['reset_role'] = role
        session['reset_expiry'] = time.time() + 300 # valid for 5 mins
        session.modified = True

        # Send simulated SMS/Notification
        recipient_id = phone_to_reset if (phone_to_reset and role == 'vendor') else email_to_reset
        notification_msg = f"Your Shubhlo password reset OTP is {otp}. Valid for 5 minutes."
        send_sms_notification(role.capitalize(), recipient_id, notification_msg)

        flash(f"OTP sent successfully! (For testing, OTP: {otp})", "success")
        return redirect(url_for('verify_reset_otp'))

    return render_template('forgot_password.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
@app.route('/forgot-password', methods=['GET', 'POST'])
def forget_password_alias():
    return forget_password()

@app.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if 'reset_otp' not in session or 'reset_email' not in session:
        flash("Please request an OTP first.", "warning")
        return redirect(url_for('forget_password'))

    import time
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        
        # Check expiry
        if time.time() > session.get('reset_expiry', 0):
            flash("OTP has expired. Please request a new one.", "danger")
            # clean up
            session.pop('reset_otp', None)
            session.pop('reset_email', None)
            session.pop('reset_role', None)
            session.pop('reset_expiry', None)
            return redirect(url_for('forget_password'))

        if entered_otp and entered_otp.strip() == session.get('reset_otp'):
            session['reset_otp_verified'] = True
            session.modified = True
            flash("OTP verified successfully! Set your new password.", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP! Please try again.", "danger")
            return redirect(url_for('verify_reset_otp'))

    return render_template('verify_reset_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_otp_verified'):
        flash("Unauthorized access. Verify OTP first.", "danger")
        return redirect(url_for('forget_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            flash("All password fields are required.", "danger")
            return redirect(url_for('reset_password'))

        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('reset_password'))

        email = session.get('reset_email')
        role = session.get('reset_role')

        conn = get_db_connection()
        db_success = False

        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    if role == 'customer':
                        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
                    elif role == 'vendor':
                        cursor.execute("UPDATE vendor SET password=%s WHERE email=%s", (new_password, email))
                    conn.commit()
                    db_success = True
            except Exception as e:
                flash(f"Database error during reset: {e}", "danger")
                return redirect(url_for('reset_password'))
            finally:
                conn.close()
        else:
            # Fallback mock mode
            if role == 'vendor':
                session_vendors = session.get('mock_vendors', [])
                updated = False
                for v in session_vendors:
                    if v['email'] == email:
                        v['password'] = new_password
                        updated = True
                if updated:
                    session['mock_vendors'] = session_vendors
                    session.modified = True
            db_success = True # mark as simulated success

        if db_success:
            # Clear all reset session variables
            session.pop('reset_otp', None)
            session.pop('reset_email', None)
            session.pop('reset_role', None)
            session.pop('reset_expiry', None)
            session.pop('reset_otp_verified', None)
            session.modified = True

            flash("Password updated successfully! Please login with your new password.", "success")
            if role == 'vendor':
                return redirect(url_for('vendor_login'))
            else:
                return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash("Unauthorized access. Admin login required.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    bookings = []
    sms_logs = []
    all_vendors = []
    contact_messages = []
    allowed_locations = []

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Fetch all bookings
                cursor.execute("SELECT * FROM booking ORDER BY created_at DESC")
                bookings = cursor.fetchall()

                # For each booking, fetch verification records
                for b in bookings:
                    cursor.execute(
                        "SELECT vendor_name, service_type, status, verified_at FROM booking_verification WHERE booking_id=%s",
                        (b['id'],)
                    )
                    b['verifications'] = cursor.fetchall()

                # Fetch all simulated SMS logs
                cursor.execute("SELECT * FROM simulated_sms ORDER BY created_at DESC")
                sms_logs = cursor.fetchall()

                # Fetch all vendors for Admin Approval & Verification
                cursor.execute("SELECT * FROM vendor ORDER BY created_at DESC")
                all_vendors = cursor.fetchall()

                # Fetch contact messages (Feedback/Complaints/Enquiries)
                cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
                contact_messages = cursor.fetchall()

                # Fetch allowed locations
                cursor.execute("SELECT * FROM allowed_locations ORDER BY state, district, tehsil")
                allowed_locations = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching admin dashboard data: {e}")
        finally:
            conn.close()
    else:
        # Fallback simulation
        mock_bookings = session.get('mock_bookings', [])
        import copy
        bookings = copy.deepcopy(mock_bookings)
        mock_verifications = session.get('mock_verifications', [])
        
        for b in bookings:
            b['verifications'] = [
                v for v in mock_verifications if v['booking_id'] == b['id']
            ]
            
        sms_logs = session.get('mock_sms', [])
        sms_logs = copy.deepcopy(sms_logs)
        all_vendors = session.get('mock_vendors', [])
        contact_messages = session.get('mock_contact_messages', [])
        contact_messages = copy.deepcopy(contact_messages)

        # Mock locations
        if 'mock_allowed_locations' not in session:
            session['mock_allowed_locations'] = [
                {'id': 1, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Itarsi'},
                {'id': 2, 'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Sohagpur'},
                {'id': 3, 'state': 'Madhya Pradesh', 'district': 'Bhopal', 'tehsil': 'Berasia'},
                {'id': 4, 'state': 'Madhya Pradesh', 'district': 'Bhopal', 'tehsil': 'Kolar'},
                {'id': 5, 'state': 'Maharashtra', 'district': 'Pune', 'tehsil': 'Haveli'},
                {'id': 6, 'state': 'Maharashtra', 'district': 'Pune', 'tehsil': 'Mulshi'},
                {'id': 7, 'state': 'Maharashtra', 'district': 'Mumbai', 'tehsil': 'Andheri'},
                {'id': 8, 'state': 'Maharashtra', 'district': 'Mumbai', 'tehsil': 'Borivali'}
            ]
            session.modified = True
        allowed_locations = session['mock_allowed_locations']

    return render_template(
        'admin_dashboard.html',
        bookings=bookings,
        sms_logs=sms_logs,
        all_vendors=all_vendors,
        contact_messages=contact_messages,
        allowed_locations=allowed_locations,
        total_bookings=len(bookings)
    )

@app.route('/admin/update_system_settings', methods=['POST'])
@app.route('/admin/toggle_master_control', methods=['POST'])
def admin_update_system_settings():
    if 'admin' not in session:
        flash("Unauthorized access. Admin login required.", "danger")
        return redirect(url_for('login'))

    booking_status = request.form.get('allow_customer_booking', 'ON')
    booking_msg = request.form.get('booking_closure_msg', 'Customer bookings are temporarily paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा ग्राहक बुकिंग फ़िलहाल बंद है।')

    vendor_status = request.form.get('allow_vendor_registration', 'ON')
    vendor_msg = request.form.get('vendor_closure_msg', 'New vendor registrations are currently paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा नया वेंडर रजिस्ट्रेशन फ़िलहाल बंद है।')

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, custom_message) 
                    VALUES ('allow_customer_booking', %s, %s)
                    ON DUPLICATE KEY UPDATE setting_value=%s, custom_message=%s
                """, (booking_status, booking_msg, booking_status, booking_msg))

                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, custom_message) 
                    VALUES ('allow_vendor_registration', %s, %s)
                    ON DUPLICATE KEY UPDATE setting_value=%s, custom_message=%s
                """, (vendor_status, vendor_msg, vendor_status, vendor_msg))

                conn.commit()
                flash("Owner Master Controls saved successfully! / प्लेटफॉर्म मास्टर सेटिंग्स सफलतापूर्वक अपडेट की गईं!", "success")
        except Exception as e:
            flash(f"Error updating system settings: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock mode fallback
        session['mock_system_settings'] = {
            'allow_customer_booking': {'value': booking_status, 'msg': booking_msg},
            'allow_vendor_registration': {'value': vendor_status, 'msg': vendor_msg}
        }
        session.modified = True
        flash("Owner Master Controls saved successfully (Simulated)! / मास्टर सेटिंग्स अपडेट हुईं (सिम्युलेटेड)!", "success")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/vendor/approve/<int:vendor_id>', methods=['POST'])
def admin_approve_vendor(vendor_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    approved_tehsil = None
    approved_district = None
    approved_state = None

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT state, district, tehsil, email, phone FROM vendor WHERE id=%s", (vendor_id,))
                v_row = cursor.fetchone()
                if v_row:
                    v_email = v_row.get('email')
                    v_phone = v_row.get('phone')
                    approved_state = v_row.get('state') or 'Madhya Pradesh'
                    approved_district = v_row.get('district') or 'Hoshangabad'
                    approved_tehsil = v_row.get('tehsil') or 'Itarsi'

                    # Approve all service records registered under this vendor's email or phone
                    if v_email or v_phone:
                        cursor.execute("UPDATE vendor SET approval_status='Approved' WHERE (email=%s AND email != '') OR (phone=%s AND phone != '')", (v_email, v_phone))
                    else:
                        cursor.execute("UPDATE vendor SET approval_status='Approved' WHERE id=%s", (vendor_id,))

                    # Auto add Tehsil location to allowed_locations table if not present
                    cursor.execute("SELECT id FROM allowed_locations WHERE tehsil=%s AND district=%s", (approved_tehsil, approved_district))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO allowed_locations (state, district, tehsil) VALUES (%s, %s, %s)", (approved_state, approved_district, approved_tehsil))
                else:
                    cursor.execute("UPDATE vendor SET approval_status='Approved' WHERE id=%s", (vendor_id,))

                conn.commit()
                flash(f"Vendor #{vendor_id} and all registered services Approved! Automatically linked to Tehsil '{approved_tehsil}' for customer bookings. 🎉", "success")
        except Exception as e:
            flash(f"Error approving vendor: {e}", "danger")
        finally:
            conn.close()
    else:
        session_vendors = session.get('mock_vendors', [])
        target_v = next((v for v in session_vendors if v['id'] == vendor_id), None)
        target_email = target_v.get('email') if target_v else None
        target_phone = target_v.get('phone') if target_v else None

        for v in session_vendors:
            if v['id'] == vendor_id or (target_email and v.get('email') == target_email) or (target_phone and v.get('phone') == target_phone):
                v['approval_status'] = 'Approved'
                if not approved_tehsil:
                    approved_tehsil = v.get('tehsil', 'Itarsi')
                    approved_district = v.get('district', 'Hoshangabad')
                    approved_state = v.get('state', 'Madhya Pradesh')
        session['mock_vendors'] = session_vendors
        
        # Add to mock allowed_locations if not present
        if 'mock_allowed_locations' not in session:
            session['mock_allowed_locations'] = []
        if approved_tehsil and not any(loc['tehsil'].lower() == approved_tehsil.lower() for loc in session['mock_allowed_locations']):
            session['mock_allowed_locations'].append({
                'id': len(session['mock_allowed_locations']) + 1,
                'state': approved_state or 'Madhya Pradesh',
                'district': approved_district or 'Hoshangabad',
                'tehsil': approved_tehsil
            })
        session.modified = True
        flash(f"Vendor #{vendor_id} and all registered services Approved! Tehsil '{approved_tehsil}' is now active for customer bookings. 🎉", "success")
        
    referrer = request.referrer
    if referrer and ('owner/dashboard' in referrer or 'owner' in referrer):
        return redirect(url_for('owner_dashboard'))
    return redirect(url_for('admin_dashboard'))

# Admin reject vendor

@app.route('/admin/vendor/reject/<int:vendor_id>', methods=['POST'])
def admin_reject_vendor(vendor_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT email, phone FROM vendor WHERE id=%s", (vendor_id,))
                v_row = cursor.fetchone()
                if v_row:
                    v_email = v_row.get('email')
                    v_phone = v_row.get('phone')
                    cursor.execute("UPDATE vendor SET approval_status='Rejected' WHERE (email=%s AND email != '') OR (phone=%s AND phone != '')", (v_email, v_phone))
                else:
                    cursor.execute("UPDATE vendor SET approval_status='Rejected' WHERE id=%s", (vendor_id,))
                conn.commit()
                flash(f"Vendor #{vendor_id} (and associated service entries) Rejected.", "info")
        except Exception as e:
            flash(f"Error rejecting vendor: {e}", "danger")
        finally:
            conn.close()
    else:
        session_vendors = session.get('mock_vendors', [])
        target_v = next((v for v in session_vendors if v['id'] == vendor_id), None)
        target_email = target_v.get('email') if target_v else None
        target_phone = target_v.get('phone') if target_v else None

        for v in session_vendors:
            if v['id'] == vendor_id or (target_email and v.get('email') == target_email) or (target_phone and v.get('phone') == target_phone):
                v['approval_status'] = 'Rejected'
        session['mock_vendors'] = session_vendors
        session.modified = True
        flash(f"Vendor #{vendor_id} Rejected (Simulated).", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/allowed-locations/add', methods=['POST'])
def admin_add_allowed_location():
    if 'admin' not in session:
        return redirect(url_for('login'))
        
    state = request.form.get('state')
    district = request.form.get('district')
    tehsil = request.form.get('tehsil')
    
    if not state or not district or not tehsil:
        flash("Please select State, District, and Tehsil.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT IGNORE INTO allowed_locations (state, district, tehsil) VALUES (%s, %s, %s)",
                    (state, district, tehsil)
                )
                conn.commit()
                flash(f"Successfully permitted location: {state} > {district} > {tehsil}! 🎉", "success")
        except Exception as e:
            flash(f"Error permitting location: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock session fallback
        mock_locs = session.get('mock_allowed_locations', [])
        # Check duplicate
        if any(l['state'] == state and l['district'] == district and l['tehsil'] == tehsil for l in mock_locs):
            flash(f"Location {state} > {district} > {tehsil} is already permitted.", "warning")
        else:
            new_id = 900 + len(mock_locs)
            mock_locs.append({'id': new_id, 'state': state, 'district': district, 'tehsil': tehsil})
            session['mock_allowed_locations'] = mock_locs
            session.modified = True
            flash(f"Successfully permitted location (Mock): {state} > {district} > {tehsil}! 🎉", "success")
            
    return redirect(url_for('admin_dashboard'))

# Admin Delete Allowed Location

@app.route('/admin/allowed-locations/delete/<int:loc_id>', methods=['POST'])
def admin_delete_allowed_location(loc_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM allowed_locations WHERE id=%s", (loc_id,))
                conn.commit()
                flash("Location permission removed successfully.", "success")
        except Exception as e:
            flash(f"Error removing location permission: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock session fallback
        mock_locs = session.get('mock_allowed_locations', [])
        mock_locs = [l for l in mock_locs if l['id'] != loc_id]
        session['mock_allowed_locations'] = mock_locs
        session.modified = True
        flash("Location permission removed successfully (Mock).", "success")
        
    return redirect(url_for('admin_dashboard'))

# API endpoint for allowed locations

@app.route('/api/allowed-locations')
def get_allowed_locations():
    if ALLOW_ALL_LOCATIONS:
        import json
        try:
            with open('static/locations.js', 'r', encoding='utf-8') as f:
                content = f.read()
                json_str = content.replace("window.locationData = ", "").strip()
                if json_str.endswith(";"):
                    json_str = json_str[:-1].strip()
                return jsonify(json.loads(json_str))
        except Exception as e:
            print(f"Error loading allowed locations from locations.js: {e}")
            # Fall through to standard queries on error

    conn = get_db_connection()
    loc_dict = {}
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT state, district, tehsil FROM allowed_locations ORDER BY state, district, tehsil")
                rows = cursor.fetchall()
                for r in rows:
                    state = r['state']
                    district = r['district']
                    tehsil = r['tehsil']
                    if state not in loc_dict:
                        loc_dict[state] = {}
                    if district not in loc_dict[state]:
                        loc_dict[state][district] = []
                    if tehsil not in loc_dict[state][district]:
                        loc_dict[state][district].append(tehsil)
        except Exception as e:
            print(f"Error fetching allowed locations: {e}")
        finally:
            conn.close()
    else:
        # Mock/Session Fallback
        mock_locs = session.get('mock_allowed_locations', [
            {'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Itarsi'},
            {'state': 'Madhya Pradesh', 'district': 'Hoshangabad', 'tehsil': 'Sohagpur'},
            {'state': 'Madhya Pradesh', 'district': 'Bhopal', 'tehsil': 'Berasia'},
            {'state': 'Madhya Pradesh', 'district': 'Bhopal', 'tehsil': 'Kolar'},
            {'state': 'Maharashtra', 'district': 'Pune', 'tehsil': 'Haveli'},
            {'state': 'Maharashtra', 'district': 'Pune', 'tehsil': 'Mulshi'},
            {'state': 'Maharashtra', 'district': 'Mumbai', 'tehsil': 'Andheri'},
            {'state': 'Maharashtra', 'district': 'Mumbai', 'tehsil': 'Borivali'}
        ])
        for r in mock_locs:
            state = r['state']
            district = r['district']
            tehsil = r['tehsil']
            if state not in loc_dict:
                loc_dict[state] = {}
            if district not in loc_dict[state]:
                loc_dict[state][district] = []
            if tehsil not in loc_dict[state][district]:
                loc_dict[state][district].append(tehsil)
    
    # If empty, default to Hoshangabad/Bhopal MP
    if not loc_dict:
        loc_dict = {
            "Madhya Pradesh": {
                "Hoshangabad": ["Itarsi", "Sohagpur"],
                "Bhopal": ["Berasia", "Kolar"]
            }
        }
    return jsonify(loc_dict)

@app.route('/admin/booking/approve/<int:booking_id>', methods=['GET', 'POST'])
@app.route('/admin/approve_booking/<int:booking_id>', methods=['GET', 'POST'])
@app.route('/admin/approve_booking', methods=['GET', 'POST'], defaults={'booking_id': 1})
def admin_approve_booking(booking_id=1):
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE booking SET booking_status='Confirmed' WHERE id=%s", (booking_id,))
                cursor.execute("SELECT name, phone, event_date, otp FROM booking WHERE id=%s", (booking_id,))
                b_row = cursor.fetchone()
                conn.commit()
                
                if b_row:
                    c_msg = f"Dear {b_row['name']}, your Event Booking #{booking_id} for {b_row['event_date']} has been APPROVED & CONFIRMED by Shubhlo Admin! Customer contact details unlocked for vendors. - Shubhlo"
                    send_sms_notification('Customer', b_row['phone'], c_msg)
                
                flash(f"Customer Booking #{booking_id} Approved & Confirmed successfully! Customer contact details unlocked. 🎉", "success")
        except Exception as e:
            flash(f"Error approving customer booking: {e}", "danger")
        finally:
            conn.close()
    else:
        mock_bookings = session.get('mock_bookings', [])
        for mb in mock_bookings:
            if mb['id'] == booking_id:
                mb['booking_status'] = 'Confirmed'
                c_msg = f"Dear {mb['name']}, your Event Booking #{booking_id} for {mb['event_date']} has been APPROVED & CONFIRMED by Shubhlo Admin! - Shubhlo"
                mock_sms = session.get('mock_sms', [])
                mock_sms.append({
                    'recipient': 'Customer',
                    'phone': mb['phone'],
                    'message': c_msg
                })
                session['mock_sms'] = mock_sms
        session['mock_bookings'] = mock_bookings
        session.modified = True
        flash(f"Customer Booking #{booking_id} Approved (Simulated)! Customer contact details unlocked. 🎉", "success")
    return redirect(url_for('admin_dashboard'))

# Admin reject customer booking

@app.route('/admin/booking/reject/<int:booking_id>', methods=['POST'])
@app.route('/admin/reject_booking/<int:booking_id>', methods=['POST'])
@app.route('/admin/reject_booking', methods=['POST'], defaults={'booking_id': 1})
def admin_reject_booking(booking_id=1):
    if 'admin' not in session:
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE booking SET booking_status='Cancelled' WHERE id=%s", (booking_id,))
                cursor.execute("SELECT name, phone, event_date FROM booking WHERE id=%s", (booking_id,))
                b_row = cursor.fetchone()
                conn.commit()
                if b_row:
                    c_msg = f"Dear {b_row['name']}, your booking #{booking_id} for {b_row['event_date']} was REJECTED/CANCELLED by Admin. - Shubhlo"
                    send_sms_notification('Customer', b_row['phone'], c_msg)
            flash(f"Booking #{booking_id} has been REJECTED.", "info")
        except Exception as e:
            flash(f"Error rejecting booking: {e}", "danger")
        finally:
            conn.close()
    else:
        # Fallback simulation
        mock_bookings = session.get('mock_bookings', [])
        found_b = next((b for b in mock_bookings if b['id'] == booking_id), None)
        if found_b:
            found_b['booking_status'] = 'Cancelled'
            session['mock_bookings'] = mock_bookings
            session.modified = True
            flash(f"Booking #{booking_id} REJECTED (Mock Mode).", "info")

    return redirect(url_for('admin_dashboard'))

# Ratings Page

@app.route('/admin/booking/delete/<int:booking_id>', methods=['POST'])
def admin_delete_booking(booking_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Also delete associated verifications first, though FK ON DELETE CASCADE handles it
                cursor.execute("DELETE FROM booking_verification WHERE booking_id=%s", (booking_id,))
                cursor.execute("DELETE FROM booking WHERE id=%s", (booking_id,))
                conn.commit()
                flash(f"Booking #{booking_id} permanently deleted.", "success")
        except Exception as e:
            flash(f"Error deleting booking: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock/Session Fallback
        mock_bookings = session.get('mock_bookings', [])
        mock_bookings = [mb for mb in mock_bookings if mb['id'] != booking_id]
        session['mock_bookings'] = mock_bookings
        session.modified = True
        flash(f"Booking #{booking_id} deleted (Simulated).", "success")
    return redirect(url_for('admin_dashboard'))

# Admin Delete Vendor

@app.route('/admin/vendor/delete/<int:vendor_id>', methods=['POST'])
@app.route('/owner/vendor/delete/<int:vendor_id>', methods=['POST'])
@app.route('/admin/vendor/delete', methods=['POST'], defaults={'vendor_id': 1})
def admin_delete_vendor(vendor_id=1):
    if not (session.get('admin') or session.get('is_owner')):
        flash("Unauthorized access. Owner permission required. / केवल ऑनर्स को अधिकार प्राप्त है।", "danger")
        return redirect(url_for('login'))

    target_email = None
    target_phone = None

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT email, phone FROM vendor WHERE id=%s", (vendor_id,))
                v_row = cursor.fetchone()
                if v_row:
                    target_email = v_row.get('email')
                    target_phone = v_row.get('phone')
                    cursor.execute("DELETE FROM vendor WHERE (email=%s AND email != '') OR (phone=%s AND phone != '')", (target_email, target_phone))
                else:
                    cursor.execute("DELETE FROM vendor WHERE id=%s", (vendor_id,))
                conn.commit()
                flash(f"Vendor #{vendor_id} and all registered services PERMANENTLY DELETED by Owner! / वेंडर खाता #{vendor_id} पूरी तरह डिलीट कर दिया गया है!", "success")
        except Exception as e:
            flash(f"Error deleting vendor: {e}", "danger")
        finally:
            conn.close()

    # Always clean up from memory lists
    GLOBAL_REGISTERED_VENDORS[:] = [
        v for v in GLOBAL_REGISTERED_VENDORS
        if not (str(v.get('id')) == str(vendor_id) or (target_email and v.get('email') == target_email) or (target_phone and v.get('phone') == target_phone))
    ]

    mock_vendors = session.get('mock_vendors', [])
    if mock_vendors:
        session['mock_vendors'] = [
            v for v in mock_vendors
            if not (str(v.get('id')) == str(vendor_id) or (target_email and v.get('email') == target_email) or (target_phone and v.get('phone') == target_phone))
        ]
        session.modified = True

    flash(f"Vendor #{vendor_id} PERMANENTLY DELETED by Owner! / वेंडर खाता पूरी तरह डिलीट हुआ!", "success")
    return redirect(request.referrer or url_for('owner_dashboard'))


# Admin & Owner Delete Customer

@app.route('/admin/vendor/edit/<int:vendor_id>', methods=['POST'])
def admin_edit_vendor(vendor_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    price = request.form.get('price', 0.00)
    approval_status = request.form.get('approval_status')
    
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE vendor SET name=%s, phone=%s, email=%s, price=%s, approval_status=%s WHERE id=%s""",
                    (name, phone, email, price, approval_status, vendor_id)
                )
                conn.commit()
                flash(f"Vendor #{vendor_id} details updated successfully.", "success")
        except Exception as e:
            flash(f"Error updating vendor: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock/Session Fallback
        mock_vendors = session.get('mock_vendors', [])
        for v in mock_vendors:
            if v['id'] == vendor_id:
                v['name'] = name
                v['phone'] = phone
                v['email'] = email
                v['price'] = float(price)
                v['approval_status'] = approval_status
        session['mock_vendors'] = mock_vendors
        session.modified = True
        flash(f"Vendor #{vendor_id} details updated (Simulated).", "success")
    return redirect(url_for('admin_dashboard'))

# Admin Delete Message

@app.route('/admin/message/delete/<int:msg_id>', methods=['POST'])
def admin_delete_message(msg_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM contact_messages WHERE id=%s", (msg_id,))
                conn.commit()
                flash(f"Message #{msg_id} permanently deleted.", "success")
        except Exception as e:
            flash(f"Error deleting message: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock/Session Fallback
        mock_messages = session.get('mock_contact_messages', [])
        mock_messages = [m for m in mock_messages if m['id'] != msg_id]
        session['mock_contact_messages'] = mock_messages
        session.modified = True
        flash(f"Message #{msg_id} deleted (Simulated).", "success")
    return redirect(url_for('admin_dashboard'))

# Admin Delete Single SMS Log

@app.route('/admin/sms/delete/<int:sms_id>', methods=['POST'])
def admin_delete_sms(sms_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM simulated_sms WHERE id=%s", (sms_id,))
                conn.commit()
                flash(f"SMS Log #{sms_id} deleted.", "success")
        except Exception as e:
            flash(f"Error deleting SMS log: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock/Session Fallback
        mock_sms = session.get('mock_sms', [])
        mock_sms = [s for s in mock_sms if s['id'] != sms_id]
        session['mock_sms'] = mock_sms
        session.modified = True
        flash(f"SMS Log #{sms_id} deleted (Simulated).", "success")
    return redirect(url_for('admin_dashboard'))

# Admin Clear All SMS Logs

@app.route('/admin/sms/clear-all', methods=['POST'])
def admin_clear_all_sms():
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE simulated_sms")
                conn.commit()
                flash("All simulated SMS logs cleared successfully.", "success")
        except Exception as e:
            flash(f"Error clearing SMS logs: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock/Session Fallback
        session['mock_sms'] = []
        session.modified = True
        flash("All simulated SMS logs cleared (Simulated).", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/blacklist/add', methods=['POST'])
def admin_blacklist_add():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    b_type = request.form.get('type')
    b_val = request.form.get('value')
    reason = request.form.get('reason', '')

    if not b_val:
        flash("Blacklist value cannot be empty.", "danger")
        return redirect(url_for('admin_dashboard'))

    clean_val = b_val.strip().lower()
    if b_type == 'Phone':
        clean_val = ''.join(filter(str.isdigit, clean_val))[-10:]
        if len(clean_val) != 10:
            flash("Please enter a valid 10-digit mobile number.", "danger")
            return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO blacklist (type, value, reason) VALUES (%s, %s, %s)",
                    (b_type, clean_val, reason)
                )
                conn.commit()
                flash(f"Successfully blacklisted {b_val}!", "success")
        except Exception as e:
            flash(f"Error blacklisting value: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock session fallback
        if 'mock_blacklist' not in session:
            session['mock_blacklist'] = []
        if any(entry['value'] == clean_val for entry in session['mock_blacklist']):
            flash(f"{b_val} is already blacklisted (Simulated).", "warning")
        else:
            mock_id = 100 + len(session['mock_blacklist'])
            session['mock_blacklist'].append({
                'id': mock_id,
                'type': b_type,
                'value': clean_val,
                'reason': reason,
                'created_at': '2026-07-29'
            })
            session.modified = True
            flash(f"Successfully blacklisted {b_val} (Simulated)!", "success")
            
    return redirect(url_for('admin_dashboard'))

# Admin Blacklist Delete

@app.route('/vendor_login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Please enter both vendor email/phone and password. / कृपया वेंडर ईमेल/फ़ोन और पासवर्ड दोनों दर्ज करें।", "danger")
            return render_template('vendor_login.html')

        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM vendor WHERE (email=%s OR phone=%s) AND password=%s", (email, email, password))
                    v = cursor.fetchone()
                    if v:
                        session['vendor'] = v['email']
                        session['vendor_name'] = v['name']
                        session['vendor_service'] = v['service']
                        session['vendor_id'] = v['id']
                        flash(f"Vendor Login successful! Welcome {v['name']} 🎉", "success")
                        return redirect(url_for('vendor_dashboard'))
                    else:
                        flash("Invalid vendor email/phone or password! Only registered vendors can log in. / गलत वेंडर ईमेल/फ़ोन या पासवर्ड! केवल पंजीकृत वेंडर ही लॉगिन कर सकते हैं।", "danger")
                        return render_template('vendor_login.html')
            except Exception as e:
                print(f"Error logging in vendor: {e}")
                flash(f"Vendor login error: {e}", "danger")
                return render_template('vendor_login.html')
            finally:
                conn.close()
        else:
            # Fallback mock mode: check registered mock vendors
            default_mock_vendors = [
                {'id': 101, 'name': 'Royal Palace Garden (Mock)', 'email': 'vendor@shubhlo.com', 'phone': '9876543210', 'password': 'vendor123', 'service': 'venue'},
                {'id': 102, 'name': 'Shahi Caterers (Mock)', 'email': 'shahi@shubhlo.com', 'phone': '9876543211', 'password': 'vendor123', 'service': 'catering'}
            ]
            session_vendors = session.get('mock_vendors', [])
            all_vendors = session_vendors + default_mock_vendors

            v = next((x for x in all_vendors if (str(x.get('email', '')).lower() == email.lower() or str(x.get('phone', '')) == email) and str(x.get('password', '')) == password), None)
            if v:
                session['vendor'] = v['email']
                session['vendor_name'] = v['name']
                session['vendor_service'] = v.get('service', 'venue')
                session['vendor_id'] = v.get('id', 101)
                flash(f"Vendor Login successful! Welcome {v['name']} 🎉", "success")
                return redirect(url_for('vendor_dashboard'))
            else:
                flash("Invalid vendor email/phone or password! Only registered vendors can log in. / गलत वेंडर ईमेल/फ़ोन या पासवर्ड! केवल पंजीकृत वेंडर ही सही पासवर्ड से लॉगिन कर सकते हैं।", "danger")
                return render_template('vendor_login.html')

    return render_template('vendor_login.html')

@app.route('/vendor/login', methods=['GET', 'POST'])
@app.route('/vendor-login', methods=['GET', 'POST'])
def vendor_login_alias():
    return vendor_login()

@app.route('/vendor_register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        # Verify vendor terms and conditions checkbox
        accept_terms = request.form.get('accept_terms_vendor')
        if not accept_terms:
            flash("You must agree to the Vendor Terms & Conditions to register. / पंजीकरण करने के लिए आपको नियम और शर्तों से सहमत होना होगा।", "danger")
            return redirect(url_for('vendor_register'))

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        selected_services = request.form.getlist('service')
        if not selected_services and request.form.get('service'):
            selected_services = [request.form.get('service')]
        description = request.form.get('description')
        price = request.form.get('price', 0.00)
        password = request.form.get('password', 'password123')
        state = request.form.get('state', 'Madhya Pradesh')
        district = request.form.get('district', 'Hoshangabad')
        tehsil = request.form.get('tehsil', 'Itarsi')
        photo = request.files.get('photo')

        if not selected_services:
            flash("Please select at least one service category. / कृपया कम से कम एक सेवा श्रेणी चुनें।", "danger")
            return redirect(url_for('vendor_register'))

        primary_service = selected_services[0]

        photo_filename = None
        if photo and photo.filename != "":
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            # Save uploaded vendor photo
            photo_filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename).replace('\\', '/')
            photo.save(photo_filename)
            if not photo_filename.startswith('/'):
                photo_filename = '/' + photo_filename

        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    # Check if vendor already exists with same email OR phone
                    cursor.execute("SELECT * FROM vendor WHERE email=%s OR phone=%s", (email, phone))
                    existing_vendor = cursor.fetchone()

                    if existing_vendor:
                        return render_template('vendor_register.html', registration_status='already_registered')
                    else:
                        first_v_id = None
                        for idx, s_cat in enumerate(selected_services):
                            cursor.execute(
                                """INSERT INTO vendor (name, email, phone, service, description, photo, password, price, state, district, tehsil, approval_status) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')""",
                                (name, email, phone, s_cat, description, photo_filename, password, price, state, district, tehsil)
                            )
                            if idx == 0:
                                first_v_id = cursor.lastrowid
                        conn.commit()
                        
                        # Auto log in the vendor
                        session['vendor'] = email
                        session['vendor_name'] = name
                        session['vendor_service'] = primary_service
                        session['vendor_id'] = first_v_id
                        
                        return render_template('vendor_register.html', registration_status='success')
            except Exception as e:
                flash(f"Error registering vendor: {e}", "danger")
            finally:
                conn.close()
        else:
            # Fallback mock mode simulation
            if 'mock_vendors' not in session:
                session['mock_vendors'] = []

            # Seed some mock vendor emails and phones for duplicate testing
            seed_emails = ['royal@shubhlo.com', 'meadow@shubhlo.com', 'shahi@shubhlo.com', 'djrock@shubhlo.com', 'dream@shubhlo.com', 'luxury@shubhlo.com', 'photo@shubhlo.com', 'sawari@shubhlo.com', 'card@shubhlo.com']
            seed_phones = ['9876543210', '9876543211', '9876543212', '9876543213', '9876543214', '9876543215', '9876543216', '9876543217', '9876543218']

            is_duplicate = (
                any(v['email'] == email or v['phone'] == phone for v in session['mock_vendors']) or
                email in seed_emails or
                phone in seed_phones
            )

            if is_duplicate:
                return render_template('vendor_register.html', registration_status='already_registered')
            else:
                first_v_id = None
                for idx, s_cat in enumerate(selected_services):
                    new_v_id = 800 + len(session['mock_vendors'])
                    new_v = {
                        'id': new_v_id,
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'service': s_cat,
                        'description': description,
                        'photo': photo_filename,
                        'password': password,
                        'price': float(price),
                        'state': state,
                        'district': district,
                        'tehsil': tehsil,
                        'approval_status': 'Pending'
                    }
                    session['mock_vendors'].append(new_v)
                    if not any(v['email'] == email and v['service'] == s_cat for v in GLOBAL_REGISTERED_VENDORS):
                        GLOBAL_REGISTERED_VENDORS.append(new_v)
                    if idx == 0:
                        first_v_id = new_v_id
                
                session.modified = True
                
                # Auto log in the vendor
                session['vendor'] = email
                session['vendor_name'] = name
                session['vendor_service'] = primary_service
                session['vendor_id'] = first_v_id
                
                return render_template('vendor_register.html', registration_status='success')

        return redirect(url_for('vendor_register'))

    return render_template('vendor_register.html')

@app.route('/vendor/register', methods=['GET', 'POST'])
@app.route('/vendor-registration', methods=['GET', 'POST'])
def vendor_register_alias():
    return vendor_register()


@app.route('/vendor_dashboard')
def vendor_dashboard():
    if 'vendor' not in session:
        flash("Please log in first to access the vendor dashboard.", "warning")
        return redirect(url_for('vendor_login'))

    email = session['vendor']
    vendor_name = session['vendor_name']
    service_type = session.get('vendor_service')

    conn = get_db_connection()
    bookings = []
    vendor_details = {}
    all_services = []

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Fetch all registered services for this email first
                cursor.execute("SELECT id, service, price FROM vendor WHERE email=%s", (email,))
                all_services = cursor.fetchall()

                if all_services:
                    valid_services = [s['service'] for s in all_services]
                    if not service_type or service_type not in valid_services:
                        service_type = all_services[0]['service']
                        session['vendor_service'] = service_type
                        session['vendor_id'] = all_services[0]['id']

                # Fetch active vendor details
                cursor.execute("SELECT * FROM vendor WHERE email=%s AND service=%s", (email, service_type))
                vendor_details = cursor.fetchone()
                
                # Fetch rating summary for this vendor name
                if vendor_details:
                    cursor.execute(
                        "SELECT COALESCE(AVG(stars), 0) AS avg_rating, COUNT(id) AS rate_count FROM rating WHERE vendor_name=%s",
                        (vendor_details['name'],)
                    )
                    r_summary = cursor.fetchone()
                    vendor_details['avg_rating'] = float(r_summary['avg_rating']) if r_summary and r_summary['avg_rating'] else 0.0
                    vendor_details['rate_count'] = r_summary['rate_count'] if r_summary else 0

                    # Fetch list of reviews
                    cursor.execute(
                        "SELECT stars, feedback, created_at FROM rating WHERE vendor_name=%s AND feedback != '' ORDER BY created_at DESC",
                        (vendor_details['name'],)
                    )
                    vendor_details['reviews'] = cursor.fetchall()
                
                # Fetch bookings matching the vendor name and service category
                valid_columns = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card']
                if service_type in valid_columns:
                    query = f"SELECT * FROM booking WHERE {service_type}=%s ORDER BY event_date DESC"
                    cursor.execute(query, (vendor_name,))
                    bookings = cursor.fetchall()
                    
                    # Fetch OTP verification status for each booking
                    for b in bookings:
                        cursor.execute(
                            "SELECT status, verified_at FROM booking_verification WHERE booking_id=%s AND vendor_name=%s AND service_type=%s",
                            (b['id'], vendor_name, service_type)
                        )
                        v_row = cursor.fetchone()
                        if v_row:
                            b['verification_status'] = v_row['status']
                            b['verified_at'] = v_row['verified_at']
                        else:
                            b['verification_status'] = 'Pending'
                            b['verified_at'] = None
                else:
                    bookings = []
        except Exception as e:
            print(f"Error fetching vendor bookings: {e}")
        finally:
            conn.close()
    else:
        # Mock details and bookings with session checks
        session_vendors = session.get('mock_vendors', [])
        matched_v = next((v for v in session_vendors if v['email'] == email and v['service'] == service_type), None)
        if not matched_v:
            # Fallback to first matched email if active service is not found
            matched_v = next((v for v in session_vendors if v['email'] == email), None)
            if matched_v:
                session['vendor_service'] = matched_v['service']
                session['vendor_id'] = matched_v['id']
                service_type = matched_v['service']
        
        if matched_v:
            vendor_details = {
                'id': matched_v['id'],
                'name': matched_v['name'],
                'email': matched_v['email'],
                'phone': matched_v['phone'],
                'service': matched_v['service'],
                'description': matched_v['description'],
                'price': matched_v['price'],
                'photo': matched_v['photo'] or '/static/image/logo.png',
                'state': matched_v.get('state', 'Madhya Pradesh'),
                'district': matched_v.get('district', 'Hoshangabad'),
                'tehsil': matched_v.get('tehsil', 'Itarsi'),
                'approval_status': matched_v.get('approval_status', 'Pending')
            }
        else:
            vendor_details = {
                'id': 1,
                'name': vendor_name,
                'email': email,
                'phone': '9876543210',
                'service': service_type,
                'description': 'Excellent event services provider.',
                'price': 15000.00,
                'photo': '/static/image/logo.png',
                'state': 'Madhya Pradesh',
                'district': 'Hoshangabad',
                'tehsil': 'Itarsi',
                'approval_status': 'Approved'
            }
        
        # Calculate rating for mock vendor
        mock_vendor_ratings = session.get('mock_vendor_ratings', [])
        v_ratings = [r for r in mock_vendor_ratings if r.get('vendor_name') == vendor_details['name']]
        if v_ratings:
            vendor_details['avg_rating'] = round(sum(r['stars'] for r in v_ratings) / len(v_ratings), 1)
            vendor_details['rate_count'] = len(v_ratings)
            vendor_details['reviews'] = [
                {
                    'stars': r['stars'], 
                    'feedback': r.get('feedback', ''), 
                    'created_at': '2026-07-25 10:55:50'
                } for r in v_ratings if r.get('feedback')
            ]
        else:
            val_sum = sum(ord(c) for c in vendor_details['name'])
            vendor_details['avg_rating'] = round(4.0 + (val_sum % 11) * 0.1, 1)
            vendor_details['rate_count'] = 3 + (val_sum % 8)
            vendor_details['reviews'] = [
                {'stars': 5, 'feedback': 'Great service, highly professional!', 'created_at': '2026-07-20 12:00:00'},
                {'stars': 4, 'feedback': 'Good experience overall. On time.', 'created_at': '2026-07-22 15:30:00'}
            ]

        # Populate all_services for mock
        all_services = [
            {'id': v['id'], 'service': v['service'], 'price': v['price']} 
            for v in session_vendors if v['email'] == email
        ]
        if not all_services:
            all_services = [{'id': vendor_details['id'], 'service': vendor_details['service'], 'price': vendor_details['price']}]
        
        # Load simulated bookings matching this vendor from session
        mock_bookings = session.get('mock_bookings', [])
        bookings = []
        for mb in mock_bookings:
            if mb.get(service_type) == vendor_name:
                mb_copy = mb.copy()
                mock_verifications = session.get('mock_verifications', [])
                mv = next((v for v in mock_verifications if v['booking_id'] == mb['id'] and v['vendor_name'] == vendor_name and v['service_type'] == service_type), None)
                if mv:
                    mb_copy['verification_status'] = mv['status']
                    mb_copy['verified_at'] = mv['verified_at']
                else:
                    mb_copy['verification_status'] = 'Pending'
                    mb_copy['verified_at'] = None
                bookings.append(mb_copy)

        if not bookings:
            bookings = []

        mock_avail = list(session.get('mock_vendor_availability', [])) + list(GLOBAL_VENDOR_AVAILABILITY)
        blocked_dates = [
            m for m in mock_avail
            if (str(m.get('vendor_id')) == str(vendor_details.get('id')) or (vendor_name and m.get('vendor_name') == vendor_name))
        ]

    return render_template(
        'vendor_dashboard.html',
        vendor=vendor_details,
        all_services=all_services,
        bookings=bookings,
        blocked_dates=blocked_dates,
        total_bookings=len(bookings)
    )

@app.route('/vendor/dashboard')
def vendor_dashboard_alias():
    return vendor_dashboard()

@app.route('/vendor/verify-otp', methods=['POST'])
def vendor_verify_otp():
    if 'vendor' not in session:
        flash("Please log in first to verify OTP.", "warning")
        return redirect(url_for('vendor_login'))

    booking_id = request.form.get('booking_id')
    otp = request.form.get('otp')
    vendor_name = session['vendor_name']
    service_type = session['vendor_service']

    if not booking_id or not otp:
        flash("Booking ID and OTP are required.", "danger")
        return redirect(url_for('vendor_dashboard'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT otp FROM booking WHERE id=%s", (booking_id,))
                b_row = cursor.fetchone()
                if b_row and b_row['otp'] == otp.strip():
                    cursor.execute(
                        """UPDATE booking_verification 
                           SET status='Verified', verified_at=CURRENT_TIMESTAMP 
                           WHERE booking_id=%s AND vendor_name=%s AND service_type=%s""",
                        (booking_id, vendor_name, service_type)
                    )
                    conn.commit()
                    flash(f"OTP Verified Successfully for Booking #{booking_id}! 🎉", "success")
                else:
                    flash("Invalid OTP entered. Please verify with the customer.", "danger")
        except Exception as e:
            flash(f"Error during OTP verification: {e}", "danger")
        finally:
            conn.close()
    else:
        # Fallback simulation
        mock_bookings = session.get('mock_bookings', [])
        found_b = next((mb for mb in mock_bookings if str(mb['id']) == str(booking_id)), None)
        
        if found_b and found_b.get('otp') == otp.strip():
            mock_verifications = session.get('mock_verifications', [])
            updated = False
            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for mv in mock_verifications:
                if str(mv['booking_id']) == str(booking_id) and mv['vendor_name'] == vendor_name and mv['service_type'] == service_type:
                    mv['status'] = 'Verified'
                    mv['verified_at'] = now_str
                    updated = True
            
            if not updated:
                mock_verifications.append({
                    'booking_id': int(booking_id),
                    'vendor_name': vendor_name,
                    'service_type': service_type,
                    'status': 'Verified',
                    'verified_at': now_str
                })
            session['mock_verifications'] = mock_verifications
            flash(f"OTP Verified Successfully (Simulated) for Booking #{booking_id}! 🎉", "success")
        else:
            flash("Invalid OTP (Simulated). Please check again.", "danger")

    return redirect(url_for('vendor_dashboard'))

@app.route('/vendor/update', methods=['POST'])
def vendor_update():
    if 'vendor' not in session:
        return redirect(url_for('vendor_login'))

    email = session['vendor']
    active_service = session.get('vendor_service')
    phone = request.form.get('phone')
    description = request.form.get('description')
    price = request.form.get('price', 0.00)
    state = request.form.get('state')
    district = request.form.get('district')
    tehsil = request.form.get('tehsil')
    photo = request.files.get('photo')

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Update basic info and location for all services under this email
                cursor.execute(
                    "UPDATE vendor SET phone=%s, state=%s, district=%s, tehsil=%s WHERE email=%s",
                    (phone, state, district, tehsil, email)
                )
                
                # Update active service details (price, description)
                cursor.execute(
                    "UPDATE vendor SET description=%s, price=%s WHERE email=%s AND service=%s",
                    (description, price, email, active_service)
                )
                
                # Update photo if provided for active service only
                if photo and photo.filename != "":
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    photo_filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename).replace('\\', '/')
                    photo.save(photo_filename)
                    cursor.execute("UPDATE vendor SET photo=%s WHERE email=%s AND service=%s", (photo_filename, email, active_service))
                
                conn.commit()
                
                # Update session name/service in case they were modified
                cursor.execute("SELECT name, service FROM vendor WHERE email=%s AND service=%s", (email, active_service))
                v_data = cursor.fetchone()
                if v_data:
                    session['vendor_name'] = v_data['name']
                    session['vendor_service'] = v_data['service']
                flash("Profile updated successfully for this service!", "success")
        except Exception as e:
            flash(f"Error updating profile: {e}", "danger")
        finally:
            conn.close()
    else:
        # Update session mock vendors
        session_vendors = session.get('mock_vendors', [])
        for v in session_vendors:
            if v['email'] == email:
                v['phone'] = phone
                v['state'] = state
                v['district'] = district
                v['tehsil'] = tehsil
            if v['email'] == email and v['service'] == active_service:
                v['description'] = description
                v['price'] = float(price)
                if photo and photo.filename != "":
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    photo_filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename).replace('\\', '/')
                    photo.save(photo_filename)
                    if not photo_filename.startswith('/'):
                        photo_filename = '/' + photo_filename
                    v['photo'] = photo_filename
        session['mock_vendors'] = session_vendors
        session.modified = True
        flash("Profile updated successfully (Simulated - no DB connection)!", "success")

    return redirect(url_for('vendor_dashboard'))


# Switch active service category

@app.route('/vendor/update_pricing', methods=['POST'])
def vendor_update_pricing():
    if 'vendor' not in session:
        flash("Please log in as a vendor first. / कृपया पहले वेंडर के रूप में लॉग इन करें।", "warning")
        return redirect(url_for('vendor_login'))

    email = session['vendor']
    active_service = session.get('vendor_service')
    price_raw = request.form.get('price', '0')
    min_order_raw = request.form.get('min_order_value', '0')

    # Strict check: Must be approved by Shubhlo Owner
    conn = get_db_connection()
    is_approved = False
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT approval_status FROM vendor WHERE email=%s", (email,))
                rows = cursor.fetchall()
                is_approved = any(r.get('approval_status') == 'Approved' for r in rows)
        except Exception as e:
            print(f"Error checking vendor approval: {e}")
        finally:
            conn.close()
    else:
        all_pool = list(session.get('mock_vendors', [])) + GLOBAL_REGISTERED_VENDORS
        is_approved = any(v.get('email') == email and v.get('approval_status') == 'Approved' for v in all_pool)

    if not is_approved:
        flash("Your account is currently PENDING Owner Approval. You cannot update pricing until approved by Owner. / आपका खाता अभी स्वीकृति हेतु लंबित (Pending) है। ऑनर्स द्वारा स्वीकृति के बाद ही आप रेट अपडेट कर सकते हैं।", "danger")
        return redirect(url_for('vendor_dashboard'))

    price = float(price_raw) if price_raw and str(price_raw).strip() else 0.00
    min_order = float(min_order_raw) if min_order_raw and str(min_order_raw).strip() else 0.00

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE vendor SET price=%s, min_order_value=%s WHERE email=%s AND service=%s",
                    (price, min_order, email, active_service)
                )
                conn.commit()
                flash("Service price and Minimum Order limit updated successfully! / सेवा मूल्य व न्यूनतम ऑर्डर सीमा सफलतापूर्वक अपडेट की गई!", "success")
        except Exception as e:
            flash(f"Error updating pricing: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock mode fallback
        session_vendors = session.get('mock_vendors', [])
        for v in session_vendors:
            if v['email'] == email and v['service'] == active_service:
                v['price'] = price
                v['min_order_value'] = min_order
        session['mock_vendors'] = session_vendors
        session.modified = True
        flash("Service pricing & minimum order updated (Simulated)! / रेट व मिनिमम ऑर्डर अपडेट हुआ (सिम्युलेटेड)!", "success")

    return redirect(url_for('vendor_dashboard'))

@app.route('/vendor/switch_service/<service_name>', methods=['GET', 'POST'])
@app.route('/vendor/switch_service', methods=['GET', 'POST'])
def vendor_switch_service(service_name=None):
    if 'vendor' not in session:
        return redirect(url_for('vendor_login'))

    if not service_name:
        service_name = request.args.get('service_name') or request.form.get('service_name', 'venue')

    email = session['vendor']
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, service FROM vendor WHERE email=%s AND service=%s", (email, service_name))
                v_data = cursor.fetchone()
                if v_data:
                    session['vendor_service'] = v_data['service']
                    session['vendor_id'] = v_data['id']
                    session['vendor_name'] = v_data['name']
                    flash(f"Switched view to {service_name.upper()} service.", "success")
                else:
                    session['vendor_service'] = service_name
                    flash(f"Switched view to {service_name.upper()} service.", "success")
        except Exception as e:
            print(f"Error switching vendor service: {e}")
        finally:
            conn.close()
    else:
        # Mock mode
        all_registered = list(session.get('mock_vendors', [])) + GLOBAL_REGISTERED_VENDORS
        matched_v = next((v for v in all_registered if v.get('email') == email and v.get('service') == service_name), None)
        if matched_v:
            session['vendor_service'] = matched_v.get('service')
            session['vendor_id'] = matched_v.get('id')
            session['vendor_name'] = matched_v.get('name')
            flash(f"Switched view to {service_name.upper()} service.", "success")
        else:
            session['vendor_service'] = service_name
            flash(f"Switched view to {service_name.upper()} service.", "success")

    return redirect(url_for('vendor_dashboard'))


# Add another service category for existing vendor

@app.route('/vendor/add-service', methods=['POST'])
@app.route('/vendor/add_service', methods=['POST'])
def vendor_add_service():
    if 'vendor' not in session:
        return redirect(url_for('vendor_login'))
    
    email = session['vendor']
    new_service = request.form.get('service')
    description = request.form.get('description')
    price = request.form.get('price', 0.00)
    photo = request.files.get('photo')
    
    if not new_service:
        flash("Please select a service category.", "danger")
        return redirect(url_for('vendor_dashboard'))

    # Strict Pending Owner Approval Check
    conn = get_db_connection()
    v_status = 'Approved'
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT approval_status FROM vendor WHERE email=%s LIMIT 1", (email,))
                v_row = cursor.fetchone()
                if v_row:
                    v_status = v_row.get('approval_status', 'Pending')
        except Exception:
            pass
        finally:
            conn.close()
    else:
        session_vendors = session.get('mock_vendors', [])
        base_v = next((v for v in GLOBAL_REGISTERED_VENDORS if v['email'] == email), None) or next((v for v in session_vendors if v['email'] == email), None)
        if base_v:
            v_status = base_v.get('approval_status', 'Pending')

    if v_status != 'Approved':
        flash("Cannot add new services while PENDING Owner Approval. / ऑनर द्वारा अप्रूव किए जाने तक नई सेवा नहीं जोड़ सकते।", "warning")
        return redirect(url_for('vendor_dashboard'))
        
    photo_filename = None
    if photo and photo.filename != "":
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        photo_filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename).replace('\\', '/')
        photo.save(photo_filename)
        if not photo_filename.startswith('/'):
            photo_filename = '/' + photo_filename
            
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Fetch profile fields from first row
                cursor.execute("SELECT name, phone, password, state, district, tehsil FROM vendor WHERE email=%s LIMIT 1", (email,))
                base_vendor = cursor.fetchone()
                if base_vendor:
                    # Check if service is already registered for this email
                    cursor.execute("SELECT * FROM vendor WHERE email=%s AND service=%s", (email, new_service))
                    if cursor.fetchone():
                        flash(f"You have already registered the {new_service.upper()} service category.", "danger")
                    else:
                        cursor.execute(
                            """INSERT INTO vendor (name, email, phone, service, description, photo, password, price, state, district, tehsil, approval_status) 
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Approved')""",
                            (base_vendor['name'], email, base_vendor['phone'], new_service, description, photo_filename, base_vendor['password'], price, base_vendor['state'], base_vendor['district'], base_vendor['tehsil'])
                        )
                        conn.commit()
                        new_id = cursor.lastrowid
                        flash(f"Successfully added new service category: {new_service.upper()}!", "success")
                        
                        # Auto switch to the new service category
                        session['vendor_service'] = new_service
                        session['vendor_id'] = new_id
        except Exception as e:
            flash(f"Error adding service: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock mode
        session_vendors = session.get('mock_vendors', [])
        base_vendor = next((v for v in session_vendors if v['email'] == email), None)
        if base_vendor:
            if any(v['email'] == email and v['service'] == new_service for v in session_vendors):
                flash(f"You have already registered the {new_service.upper()} service category.", "danger")
            else:
                new_v_id = 850 + len(session_vendors)
                new_v = {
                    'id': new_v_id,
                    'name': base_vendor['name'],
                    'email': email,
                    'phone': base_vendor['phone'],
                    'service': new_service,
                    'description': description,
                    'photo': photo_filename,
                    'password': base_vendor['password'],
                    'price': float(price),
                    'state': base_vendor['state'],
                    'district': base_vendor['district'],
                    'tehsil': base_vendor['tehsil'],
                    'approval_status': 'Approved'
                }
                session_vendors.append(new_v)
                session['mock_vendors'] = session_vendors
                session.modified = True
                session['vendor_service'] = new_service
                session['vendor_id'] = new_v_id
                flash(f"Successfully added new service category: {new_service.upper()} (Mock)!", "success")

    return redirect(url_for('vendor_dashboard'))

@app.route('/vendor/toggle_date_availability', methods=['POST'])
def vendor_toggle_date_availability():
    if 'vendor' not in session:
        flash("Please log in first to manage event dates. / कृपया तिथि प्रबंधन के लिए पहले वेंडर लॉग इन करें।", "warning")
        return redirect(url_for('vendor_login'))

    email = session['vendor']
    active_service = session.get('vendor_service')
    vendor_id = session.get('vendor_id')
    event_date = request.form.get('event_date')
    action = request.form.get('action', 'block')
    reason = request.form.get('reason', 'Busy / Already Booked / व्यस्त या बुक')

    if not event_date:
        flash("Please select a valid date. / कृपया एक सही तिथि चुनें!", "danger")
        return redirect(url_for('vendor_dashboard'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM vendor WHERE email=%s AND service=%s", (email, active_service))
                v_row = cursor.fetchone()
                if v_row:
                    vendor_id = v_row['id']
                elif not vendor_id:
                    cursor.execute("SELECT id FROM vendor WHERE email=%s LIMIT 1", (email,))
                    v_row = cursor.fetchone()
                    if v_row:
                        vendor_id = v_row['id']

                if action == 'unblock':
                    cursor.execute("DELETE FROM vendor_availability WHERE vendor_id=%s AND event_date=%s", (vendor_id, event_date))
                    flash(f"Date {event_date} is now OPEN for bookings! / {event_date} अब बुकिंग के लिए उपलब्ध है!", "success")
                else:
                    cursor.execute("SELECT id FROM vendor_availability WHERE vendor_id=%s AND event_date=%s", (vendor_id, event_date))
                    if not cursor.fetchone():
                        cursor.execute(
                            "INSERT INTO vendor_availability (vendor_id, event_date, status, reason) VALUES (%s, %s, 'Blocked', %s)",
                            (vendor_id, event_date, reason)
                        )
                    flash(f"Date {event_date} marked as BUSY / BLOCKED! / {event_date} व्यस्त मार्क कर दी गई है!", "info")
                conn.commit()
        except Exception as e:
            flash(f"Error managing event date: {e}", "danger")
        finally:
            conn.close()
    else:
        mock_avail = session.get('mock_vendor_availability', [])
        v_name = session.get('vendor_name')
        v_id = session.get('vendor_id') or 1
        if action == 'unblock':
            session['mock_vendor_availability'] = [
                m for m in mock_avail 
                if not ((str(m.get('vendor_id')) == str(v_id) or (v_name and m.get('vendor_name') == v_name)) and str(m.get('event_date')) == str(event_date))
            ]
            flash(f"Date {event_date} is now OPEN for bookings (Simulated)! / {event_date} बुकिंग के लिए उपलब्ध की गई!", "success")
        else:
            if not any((str(m.get('vendor_id')) == str(v_id) or (v_name and m.get('vendor_name') == v_name)) and str(m.get('event_date')) == str(event_date) for m in mock_avail):
                mock_avail.append({
                    'id': len(mock_avail) + 1,
                    'vendor_id': v_id,
                    'vendor_name': v_name,
                    'event_date': event_date,
                    'status': 'Blocked',
                    'reason': reason
                })
                session['mock_vendor_availability'] = mock_avail
            flash(f"Date {event_date} marked as BUSY (Simulated)! / {event_date} व्यस्त मार्क की गई!", "info")
        session.modified = True

    return redirect(url_for('vendor_dashboard'))

# Marketing & Advertisement Hub Route

@app.route('/vendor/logout')
@app.route('/vendor_logout')
@app.route('/vendor-logout')
def vendor_logout():
    session.pop('vendor', None)
    session.pop('vendor_name', None)
    session.pop('vendor_service', None)
    session.pop('vendor_id', None)
    flash("Vendor logged out successfully! / वेंडर सफलतापूर्वक लॉग आउट हो गए हैं।", "info")
    return redirect(url_for('vendor_login'))

@app.route('/vendor/counter_offer/<int:booking_id>', methods=['POST'])
def vendor_counter_offer(booking_id):
    if 'vendor' not in session:
        flash("Please log in as vendor first / कृपया पहले वेंडर के रूप में लॉग इन करें।", "warning")
        return redirect(url_for('vendor_login'))

    counter_amount = request.form.get('counter_amount')
    counter_note = request.form.get('counter_note', '')

    if not counter_amount or float(counter_amount) <= 0:
        flash("Please enter a valid counter offer price / कृपया सही काउंटर ऑफर राशि दर्ज करें!", "danger")
        return redirect(url_for('vendor_dashboard'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE booking 
                       SET counter_offer_amount=%s, counter_offer_note=%s, counter_offer_status='Pending' 
                       WHERE id=%s""",
                    (counter_amount, counter_note, booking_id)
                )
                conn.commit()
                flash(f"Counter offer of ₹{float(counter_amount):,.2f} sent to customer! / ₹{float(counter_amount):,.2f} का कस्टम काउंटर ऑफर ग्राहक को सफलतापूर्वक भेज दिया गया है!", "success")
        except Exception as e:
            flash(f"Error sending counter offer: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock mode fallback
        mock_bookings = session.get('mock_bookings', [])
        for b in mock_bookings:
            if b.get('id') == booking_id:
                b['counter_offer_amount'] = float(counter_amount)
                b['counter_offer_note'] = counter_note
                b['counter_offer_status'] = 'Pending'
        session['mock_bookings'] = mock_bookings
        session.modified = True
        flash(f"Counter offer of ₹{float(counter_amount):,.2f} sent to customer (Simulated)! / ₹{float(counter_amount):,.2f} का कस्टम प्रस्ताव ग्राहक को भेजा गया (सिम्युलेटेड)!", "success")

    return redirect(url_for('vendor_dashboard'))


@app.route('/booking1', methods=['GET', 'POST'])
def booking1():
    if 'user' not in session:
        flash("Please log in first to make a booking.", "warning")
        return redirect(url_for('login'))

    b_status, b_msg = get_system_setting('allow_customer_booking')
    booking_closed = (b_status == 'OFF')

    if request.method == 'POST':
        if booking_closed:
            flash(b_msg or "Customer bookings are currently PAUSED by Shubhlo Owner. Please check back soon! / ऑनर्स द्वारा ग्राहक बुकिंग फ़िलहाल बंद है।", "danger")
            return redirect(url_for('booking1'))
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        state = request.form.get('state')
        district = request.form.get('district')
        tehsil = request.form.get('tehsil')
        event_date = request.form.get('event_date')
        target_budget = request.form.get('target_budget')
        budget_flexible = request.form.get('budget_flexible', 'Negotiable')
        session['booking_info'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'address': address,
            'state': state,
            'district': district,
            'tehsil': tehsil,
            'event_date': event_date,
            'target_budget': float(target_budget) if target_budget and target_budget.strip() else None,
            'budget_flexible': budget_flexible
        }
        return redirect(url_for('booking2', **request.form))
    return render_template('booking1.html', booking_system_closed=booking_closed, closure_msg=b_msg)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    return booking1()

@app.route('/booking2', methods=['GET', 'POST'])
def booking2():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Store step 1 inputs in session
    booking_info = session.get('booking_info', {})
    if request.method == 'POST':
        name = request.form.get('name') or booking_info.get('name')
        email = request.form.get('email') or booking_info.get('email')
        phone = request.form.get('phone') or booking_info.get('phone')
        address = request.form.get('address') or booking_info.get('address')
        state = request.form.get('state') or booking_info.get('state')
        district = request.form.get('district') or booking_info.get('district')
        tehsil = request.form.get('tehsil') or booking_info.get('tehsil')
        event_date = request.form.get('event_date') or booking_info.get('event_date')
        target_budget_raw = request.form.get('target_budget') or booking_info.get('target_budget')
        budget_flexible = request.form.get('budget_flexible') or booking_info.get('budget_flexible', 'Negotiable')
    else:
        name = request.args.get('name') or booking_info.get('name')
        email = request.args.get('email') or booking_info.get('email')
        phone = request.args.get('phone') or booking_info.get('phone')
        address = request.args.get('address') or booking_info.get('address')
        state = request.args.get('state') or booking_info.get('state')
        district = request.args.get('district') or booking_info.get('district')
        tehsil = request.args.get('tehsil') or booking_info.get('tehsil')
        event_date = request.args.get('event_date') or booking_info.get('event_date')
        target_budget_raw = request.args.get('target_budget') or booking_info.get('target_budget')
        budget_flexible = request.args.get('budget_flexible') or booking_info.get('budget_flexible', 'Negotiable')

    target_budget = float(target_budget_raw) if target_budget_raw and str(target_budget_raw).strip() else None

    # If any mandatory Step 1 field is missing, redirect back
    if not (name and email and phone and event_date):
        flash("Please complete the Customer Details form first.", "warning")
        return redirect(url_for('booking1'))

    # Validate Phone (must be exactly 10 digits starting with 6, 7, 8, or 9)
    phone_clean = ''.join(c for c in str(phone or '') if c.isdigit())
    if not phone_clean or len(phone_clean) != 10 or phone_clean[0] not in '6789':
        flash("Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9 / कृपया 6, 7, 8 या 9 से शुरू होने वाला सही 10-अंकीय मोबाइल नंबर दर्ज करें!", "danger")
        return redirect(url_for('booking1'))

    # Validate Address (minimum 10 characters required)
    if not address or len(str(address).strip()) < 10:
        flash("Please enter a complete address with house no., street/colony, and landmark (minimum 10 characters) / पता कम से कम 10 अक्षरों का होना चाहिए, जिसमें मकान नंबर व सड़क विवरण शामिल हो!", "danger")
        return redirect(url_for('booking1'))

    if is_blacklisted(email) or is_blacklisted(phone):
        flash("This email or phone number is blacklisted on Shubhlo due to spam or violation of terms.", "danger")
        return redirect(url_for('booking1'))

    session['booking_info'] = {
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'state': state,
        'district': district,
        'tehsil': tehsil,
        'event_date': event_date,
        'target_budget': target_budget,
        'budget_flexible': budget_flexible
    }

    # Fetch dynamic options from the vendor database or use mock fallbacks filtered by selected tehsil
    venues = fetch_vendors_by_service('venue', tehsil)
    caterings = fetch_vendors_by_service('catering', tehsil)
    djs = fetch_vendors_by_service('dj', tehsil)
    decorations = fetch_vendors_by_service('decoration', tehsil)
    transports = fetch_vendors_by_service('transport', tehsil)
    photography = fetch_vendors_by_service('photography', tehsil)
    shahi_sawari = fetch_vendors_by_service('shahi_sawari', tehsil)
    invitation_card = fetch_vendors_by_service('invitation_card', tehsil)
    security_guards = fetch_vendors_by_service('security_guard', tehsil)
    makeups = fetch_vendors_by_service('makeup', tehsil)
    mehendis = fetch_vendors_by_service('mehendi', tehsil)
    dhol_bands = fetch_vendors_by_service('dhol_band', tehsil)
    pandits = fetch_vendors_by_service('pandit', tehsil)
    choreographers = fetch_vendors_by_service('choreographer', tehsil)
    wedding_planners = fetch_vendors_by_service('wedding_planner', tehsil)
    anchors = fetch_vendors_by_service('anchor', tehsil)
    fireworks_list = fetch_vendors_by_service('fireworks', tehsil)
    mocktails = fetch_vendors_by_service('mocktail', tehsil)
    safas = fetch_vendors_by_service('safa', tehsil)

    return render_template(
        'booking2.html',
        venues=venues,
        caterings=caterings,
        djs=djs,
        decorations=decorations,
        transports=transports,
        photography=photography,
        shahi_sawari=shahi_sawari,
        invitation_card=invitation_card,
        security_guards=security_guards,
        makeups=makeups,
        mehendis=mehendis,
        dhol_bands=dhol_bands,
        pandits=pandits,
        choreographers=choreographers,
        wedding_planners=wedding_planners,
        anchors=anchors,
        fireworks_list=fireworks_list,
        mocktails=mocktails,
        safas=safas,
        tehsil=tehsil,
        target_budget=target_budget,
        budget_flexible=budget_flexible
    )

@app.route('/confirm-booking', methods=['GET', 'POST'])
@app.route('/confirm_booking', methods=['GET', 'POST'])
def confirm_booking():
    if 'user' not in session:
        return redirect(url_for('login'))

    booking_info = session.get('booking_info')
    if not booking_info:
        flash("Booking session lost. Please start over.", "danger")
        return redirect(url_for('booking1'))

    categories_list = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card']
    fallback_prices = {
        'venue': 150000, 
        'catering': 50000, 
        'dj': 20000, 
        'decoration': 30000, 
        'transport': 25000,
        'photography': 40000,
        'shahi_sawari': 35000,
        'invitation_card': 15000
    }

    if request.method == 'POST':
        # Get selections from Booking Step 2
        for cat in categories_list:
            booking_info[cat] = request.form.get(cat, "")

    # Compile detailed selected vendor objects
    amount = 0.00
    selected_vendors = []
    conn = get_db_connection()

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                for cat in categories_list:
                    v_name = booking_info.get(cat)
                    if v_name and v_name.strip() != "":
                        cursor.execute("SELECT name, service, price, photo, description FROM vendor WHERE name=%s", (v_name,))
                        v_row = cursor.fetchone()
                        if v_row:
                            v_price = float(v_row['price'])
                            v_photo = v_row.get('photo') or '/static/image/logo.png'
                            v_desc = v_row.get('description') or 'Professional event service.'
                        else:
                            v_price = float(fallback_prices.get(cat, 0.00))
                            v_photo = '/static/image/logo.png'
                            v_desc = 'Verified event vendor.'
                        
                        amount += v_price
                        selected_vendors.append({
                            'category': cat.replace('_', ' ').title(),
                            'raw_category': cat,
                            'name': v_name,
                            'price': v_price,
                            'photo': v_photo,
                            'description': v_desc
                        })
        except Exception as e:
            print(f"Error calculating total booking price: {e}")
        finally:
            conn.close()
    else:
        # Fallback sum matching mock data
        for cat in categories_list:
            v_name = booking_info.get(cat)
            if v_name and v_name.strip() != "":
                # Search mock vendors first
                m_list = MOCK_VENDORS.get(cat, [])
                m_found = next((m for m in m_list if m['name'] == v_name), None)
                if m_found:
                    v_price = float(m_found['price'])
                    v_photo = m_found.get('photo', '/static/image/logo.png')
                    v_desc = m_found.get('description', 'High quality event service provider.')
                else:
                    v_price = float(fallback_prices.get(cat, 0.00))
                    v_photo = '/static/image/logo.png'
                    v_desc = 'Verified event vendor.'

                amount += v_price
                selected_vendors.append({
                    'category': cat.replace('_', ' ').title(),
                    'raw_category': cat,
                    'name': v_name,
                    'price': v_price,
                    'photo': v_photo,
                    'description': v_desc
                })

    booking_info['amount'] = amount
    booking_info['selected_vendors'] = selected_vendors
    session['booking_info'] = booking_info

    return render_template(
        'confirm_booking.html',
        booking=booking_info,
        selected_vendors=selected_vendors,
        total_amount=amount
    )

@app.route('/pay', methods=['GET', 'POST'])
def pay():
    if 'user' not in session:
        return redirect(url_for('login'))

    booking_info = session.get('booking_info')
    if not booking_info:
        flash("No active booking session found.", "warning")
        return redirect(url_for('booking1'))

    if request.method == 'POST':
        # Accept terms checkbox check
        accept_terms = request.form.get('accept_terms')
        if not accept_terms:
            flash("Please accept the terms and conditions to proceed.", "danger")
            return redirect(url_for('confirm_booking'))
        booking_info['terms_accepted'] = True
        session['booking_info'] = booking_info
    else:
        # GET request: must have accepted terms in this session previously
        if not booking_info.get('terms_accepted'):
            flash("Please accept the terms and conditions first.", "warning")
            return redirect(url_for('confirm_booking'))

    num_selected = len(booking_info.get('selected_vendors', [])) or 1
    total_token_payable = booking_info.get('total_token_payable') or (num_selected * 5118.00)

    return render_template(
        'pay.html',
        name=booking_info.get('name'),
        email=booking_info.get('email'),
        phone=booking_info.get('phone'),
        amount=booking_info.get('amount'),
        payable_token_amount=total_token_payable,
        num_vendors=num_selected
    )

@app.route('/process-payment', methods=['POST'])
def process_payment():
    if 'user' not in session:
        return redirect(url_for('login'))

    booking_info = session.get('booking_info')
    if not booking_info:
        flash("No active booking session found to process. / कोई सक्रिय बुकिंग सत्र नहीं मिला।", "warning")
        return redirect(url_for('booking1'))

    if not booking_info.get('terms_accepted'):
        flash("Please accept the terms and conditions first. / कृपया पहले नियम व शर्तें स्वीकार करें।", "warning")
        return redirect(url_for('confirm_booking'))

    payment_method = request.form.get('payment_method', 'UPI')
    transaction_id = f"TXN{os.urandom(4).hex().upper()}"
    
    total_amount = float(booking_info.get('amount', 50000.00))
    token_deposit = min(5000.00, round(total_amount * 0.10, 2)) if total_amount > 0 else 5000.00

    conn = get_db_connection()
    new_booking_id = None

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO booking (name, email, phone, address, state, district, tehsil, event_date, amount, token_deposit, payment_status, payment_method, transaction_id, status, booking_status, venue, catering, dj, decoration, transport, photography, shahi_sawari, invitation_card)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Paid', %s, %s, 'Pending Owner Approval', 'Pending', %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    booking_info.get('name'),
                    booking_info.get('email'),
                    booking_info.get('phone'),
                    booking_info.get('address'),
                    booking_info.get('state'),
                    booking_info.get('district'),
                    booking_info.get('tehsil'),
                    booking_info.get('event_date'),
                    total_amount,
                    token_deposit,
                    payment_method,
                    transaction_id,
                    booking_info.get('venue', ''),
                    booking_info.get('catering', ''),
                    booking_info.get('dj', ''),
                    booking_info.get('decoration', ''),
                    booking_info.get('transport', ''),
                    booking_info.get('photography', ''),
                    booking_info.get('shahi_sawari', ''),
                    booking_info.get('invitation_card', '')
                ))
                new_booking_id = cursor.lastrowid
                
                # Insert verifications
                categories_list = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card']
                for cat in categories_list:
                    v_name = booking_info.get(cat)
                    if v_name and v_name.strip() != "":
                        cursor.execute(
                            "INSERT INTO booking_verification (booking_id, vendor_name, service_type, status) VALUES (%s, %s, %s, 'Pending')",
                            (new_booking_id, v_name, cat)
                        )
                conn.commit()
        except Exception as e:
            print(f"DB process_payment Error: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    # Session mock fallback if DB offline or new_booking_id not generated
    if not new_booking_id:
        mock_bookings = session.get('mock_bookings', [])
        new_booking_id = 200 + len(mock_bookings) + 1
        new_b = {
            'id': new_booking_id,
            'name': booking_info.get('name'),
            'email': booking_info.get('email'),
            'phone': booking_info.get('phone'),
            'address': booking_info.get('address'),
            'state': booking_info.get('state'),
            'district': booking_info.get('district'),
            'tehsil': booking_info.get('tehsil'),
            'event_date': booking_info.get('event_date'),
            'amount': total_amount,
            'token_deposit': token_deposit,
            'payment_status': 'Paid',
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            'status': 'Pending Owner Approval',
            'booking_status': 'Pending Owner Approval',
            'venue': booking_info.get('venue', ''),
            'catering': booking_info.get('catering', ''),
            'dj': booking_info.get('dj', ''),
            'decoration': booking_info.get('decoration', ''),
            'transport': booking_info.get('transport', ''),
            'photography': booking_info.get('photography', ''),
            'shahi_sawari': booking_info.get('shahi_sawari', ''),
            'invitation_card': booking_info.get('invitation_card', '')
        }
        mock_bookings.append(new_b)
        session['mock_bookings'] = mock_bookings

        # Add mock verifications
        mock_verifications = session.get('mock_verifications', [])
        categories_list = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card']
        for cat in categories_list:
            v_name = booking_info.get(cat)
            if v_name and v_name.strip() != "":
                mock_verifications.append({
                    'booking_id': new_booking_id,
                    'vendor_name': v_name,
                    'service_type': cat,
                    'status': 'Pending',
                    'verified_at': None
                })
        session['mock_verifications'] = mock_verifications

    # Send SMS Confirmation
    c_msg = f"Dear {booking_info.get('name')}, your Shubhlo Event Booking #{new_booking_id} has been registered! Token Deposit: ₹{token_deposit}. Status: Pending Owner Approval (48 Hours). - Shubhlo"
    send_sms_notification('Customer', booking_info.get('phone'), c_msg)

    # Clear active booking session
    session.pop('booking_info', None)
    session.modified = True

    flash(f"🎉 Payment Successful! Booking #{new_booking_id} registered successfully under 48-Hour Owner Hold. / भुगतान सफल! बुकिंग #{new_booking_id} दर्ज हो गई है।", "success")
    return redirect(url_for('dashboard'))

@app.route('/quick_inquiry', methods=['POST'])
def quick_inquiry():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    event_type = request.form.get('event_type', 'Wedding').strip()
    city = request.form.get('city', 'Itarsi').strip()
    
    if not phone or len(phone) < 10:
        return jsonify({'success': False, 'message': 'कृपया एक सही 10-अंकीय मोबाइल नंबर दर्ज करें!'}), 400
        
    print(f"[CALLBACK REQUEST]: {name} ({phone}) for {event_type} in {city}")
    return jsonify({
        'success': True, 
        'message': f'धन्यवाद {name or "जी"}! हमारी सेलिब्रेटो इवेंट एक्सपर्ट टीम जल्द ही {phone} पर आपसे संपर्क करेगी।'
    })

# Confirm selections and compute price

@app.route('/user/respond_counter_offer/<int:booking_id>', methods=['POST'])
def user_respond_counter_offer(booking_id):
    if 'user' not in session:
        flash("Please log in first / कृपया पहले लॉग इन करें।", "warning")
        return redirect(url_for('login'))

    action = request.form.get('action') # 'accept' or 'decline'
    
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                if action == 'accept':
                    cursor.execute(
                        """UPDATE booking 
                           SET amount=counter_offer_amount, counter_offer_status='Accepted', booking_status='Confirmed' 
                           WHERE id=%s AND email=%s""",
                        (booking_id, session['user'])
                    )
                    flash("Counter offer ACCEPTED! Your booking total has been updated to match the proposal. / काउंटर ऑफर स्वीकार कर लिया गया है! आपकी बुकिंग का कुल मूल्य अद्यतन हो गया है।", "success")
                else:
                    cursor.execute(
                        """UPDATE booking 
                           SET counter_offer_status='Declined' 
                           WHERE id=%s AND email=%s""",
                        (booking_id, session['user'])
                    )
                    flash("Counter offer declined. / काउंटर ऑफर अस्वीकार कर दिया गया।", "info")
                conn.commit()
        except Exception as e:
            flash(f"Error responding to counter offer: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock mode fallback
        mock_bookings = session.get('mock_bookings', [])
        for b in mock_bookings:
            if b.get('id') == booking_id and b.get('email') == session['user']:
                if action == 'accept':
                    if b.get('counter_offer_amount'):
                        b['amount'] = b['counter_offer_amount']
                    b['counter_offer_status'] = 'Accepted'
                    b['booking_status'] = 'Confirmed'
                    flash("Counter offer ACCEPTED (Simulated)! Booking price updated. / काउंटर प्रस्ताव स्वीकार किया गया (सिम्युलेटेड)! बुकिंग मूल्य अपडेट हुआ।", "success")
                else:
                    b['counter_offer_status'] = 'Declined'
                    flash("Counter offer declined (Simulated). / काउंटर प्रस्ताव अस्वीकार किया गया।", "info")
        session['mock_bookings'] = mock_bookings
        session.modified = True

    return redirect(url_for('dashboard'))

@app.route('/vendor/reassign_booking/<int:booking_id>', methods=['POST'])
@app.route('/admin/reassign_booking/<int:booking_id>', methods=['POST'])
@app.route('/vendor/reassign_booking', methods=['POST'], defaults={'booking_id': 1})
def reassign_booking(booking_id=1):
    if 'vendor' not in session and 'admin' not in session:
        flash("Please log in first to perform vendor reassignment. / कृपया पहले वेंडर या एडमिन के रूप में लॉग इन करें।", "warning")
        return redirect(url_for('login'))

    is_vendor = 'vendor' in session
    redirect_target = 'vendor_dashboard' if is_vendor else 'admin_dashboard'
    
    current_service = session.get('vendor_service') if is_vendor else request.form.get('service_type')
    current_vendor = session.get('vendor_name') if is_vendor else request.form.get('current_vendor_name')

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM booking WHERE id=%s", (booking_id,))
                b = cursor.fetchone()
                if not b:
                    flash(f"Booking #{booking_id} not found.", "danger")
                    return redirect(url_for(redirect_target))

                service_cat = current_service
                if not service_cat:
                    categories = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card', 'security_guard', 'makeup', 'mehendi', 'dhol_band', 'choreographer', 'wedding_planner', 'anchor', 'fireworks', 'safa']
                    for cat in categories:
                        if b.get(cat) == current_vendor or (not current_vendor and b.get(cat)):
                            service_cat = cat
                            current_vendor = b.get(cat)
                            break

                if not service_cat:
                    service_cat = 'venue'

                # Check if customer allowed auto-transfer
                if b.get('allow_reassignment') == 'No' and is_vendor:
                    flash("Customer specified STRICT preference for their selected vendor only. Admin has been alerted to assist the customer personally! / ग्राहक ने केवल चुना हुआ वेंडर ही मांगा है। एडमिन को ग्राहक से व्यक्तिगत रूप से सहायता करने हेतु सूचित कर दिया गया है!", "warning")
                    return redirect(url_for(redirect_target))

                tehsil = b.get('tehsil')
                district = b.get('district')
                
                cursor.execute(
                    "SELECT name, phone FROM vendor WHERE service=%s AND (approval_status IS NULL OR approval_status='Approved') AND name != %s AND (tehsil=%s OR district=%s) LIMIT 1",
                    (service_cat, current_vendor or '', tehsil, district)
                )
                alt_vendor = cursor.fetchone()

                if not alt_vendor:
                    cursor.execute(
                        "SELECT name, phone FROM vendor WHERE service=%s AND (approval_status IS NULL OR approval_status='Approved') AND name != %s LIMIT 1",
                        (service_cat, current_vendor or '')
                    )
                    alt_vendor = cursor.fetchone()

                if alt_vendor:
                    new_vendor_name = alt_vendor['name']
                    new_vendor_phone = alt_vendor['phone']

                    cursor.execute(f"UPDATE booking SET {service_cat}=%s WHERE id=%s", (new_vendor_name, booking_id))
                    cursor.execute(
                        "DELETE FROM booking_verification WHERE booking_id=%s AND service_type=%s",
                        (booking_id, service_cat)
                    )
                    cursor.execute(
                        "INSERT INTO booking_verification (booking_id, vendor_name, service_type, status) VALUES (%s, %s, %s, 'Pending')",
                        (booking_id, new_vendor_name, service_cat)
                    )
                    conn.commit()

                    c_msg = f"Dear {b['name']}, your booking #{booking_id} for {service_cat.replace('_', ' ').title()} has been transferred to top-rated vendor ({new_vendor_name}). Your event is 100% guaranteed! - Shubhlo"
                    send_sms_notification('Customer', b['phone'], c_msg)

                    v_msg = f"Dear {new_vendor_name}, booking #{booking_id} for {service_cat.replace('_', ' ').title()} on {b['event_date']} has been reassigned to you! Please check your dashboard. - Shubhlo"
                    send_sms_notification('Vendor', new_vendor_phone, v_msg)

                    flash(f"Booking #{booking_id} successfully reassigned to new vendor ({new_vendor_name})! / बुकिंग सफलतापूर्वक नए वेंडर ({new_vendor_name}) को ट्रांसफर कर दी गई है! 🎉", "success")
                else:
                    flash(f"No alternative vendor found for {service_cat.title()} in this location. Shubhlo Admin has been alerted to contact the customer directly to ensure satisfaction! / इस क्षेत्र में कोई अन्य वेंडर उपलब्ध नहीं है। सेलिब्रेटो एडमिन को सीधे ग्राहक से बात करने हेतु अलर्ट भेज दिया गया है!", "info")
        except Exception as e:
            flash(f"Error reassigning booking: {e}", "danger")
        finally:
            conn.close()
    else:
        # Mock mode fallback
        mock_bookings = session.get('mock_bookings', [])
        found_b = next((mb for mb in mock_bookings if str(mb['id']) == str(booking_id)), None)
        if found_b:
            service_cat = current_service or 'venue'
            old_vendor = current_vendor or found_b.get(service_cat, '')
            
            mock_vendors = session.get('mock_vendors', [])
            alt_v = next((v for v in mock_vendors if v.get('service') == service_cat and v.get('name') != old_vendor and v.get('approval_status', 'Approved') == 'Approved'), None)
            
            if not alt_v:
                m_list = MOCK_VENDORS.get(service_cat, [])
                alt_v = next((v for v in m_list if v['name'] != old_vendor), None)
                
            new_v_name = alt_v['name'] if alt_v else f"Shubhlo Partner ({service_cat.title()})"
            found_b[service_cat] = new_v_name
            
            mock_verifications = session.get('mock_verifications', [])
            session['mock_verifications'] = [mv for mv in mock_verifications if not (mv['booking_id'] == booking_id and mv['service_type'] == service_cat)]
            session['mock_verifications'].append({
                'booking_id': booking_id,
                'vendor_name': new_v_name,
                'service_type': service_cat,
                'status': 'Pending',
                'verified_at': None
            })
            
            mock_sms = session.get('mock_sms', [])
            mock_sms.append({
                'id': len(mock_sms) + 1,
                'recipient': 'Customer',
                'phone': found_b['phone'],
                'message': f"Dear {found_b['name']}, your booking #{booking_id} for {service_cat.replace('_', ' ').title()} has been transferred to top-rated vendor ({new_v_name}). Your event is 100% guaranteed! - Shubhlo"
            })
            session['mock_sms'] = mock_sms
            session['mock_bookings'] = mock_bookings
            session.modified = True
            flash(f"Booking #{booking_id} successfully reassigned to new vendor ({new_v_name}) (Simulated)! / बुकिंग न्यू वेंडर ({new_v_name}) को ट्रांसफर की गई (सिम्युलेटेड)! 🎉", "success")

    return redirect(url_for(redirect_target))

@app.route('/booking/cancel/<int:booking_id>', methods=['GET', 'POST'])
@app.route('/cancel-booking/<int:booking_id>', methods=['GET', 'POST'])
@app.route('/booking/cancel', methods=['GET', 'POST'], defaults={'booking_id': 1})
def cancel_booking(booking_id=1):
    if 'user' not in session:
        flash("Please log in first to cancel a booking.", "warning")
        return redirect(url_for('login'))

    email = session['user']
    
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # First, ensure the booking belongs to the logged-in user and is not already cancelled/rejected
                cursor.execute("SELECT * FROM booking WHERE id=%s AND email=%s", (booking_id, email))
                b = cursor.fetchone()
                
                if not b:
                    flash("Booking not found or unauthorized access.", "danger")
                    return redirect(url_for('dashboard'))
                
                b_status = b.get('booking_status', 'Pending')
                if b_status == 'Cancelled':
                    flash("This booking is already cancelled.", "info")
                    return redirect(url_for('dashboard'))
                
                # Update booking status to Cancelled
                cursor.execute("UPDATE booking SET booking_status='Cancelled' WHERE id=%s", (booking_id,))
                
                # Update associated booking_verification records to 'Cancelled' (if status is not already Verified)
                cursor.execute("UPDATE booking_verification SET status='Cancelled' WHERE booking_id=%s AND status != 'Verified'", (booking_id,))
                
                # Send SMS confirmation to Customer
                c_msg = f"Dear {b['name']}, your booking #{booking_id} has been CANCELLED successfully. We hope to serve you again. - Shubhlo"
                send_sms_notification('Customer', b['phone'], c_msg)
                
                # Notify vendors
                categories = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card']
                for cat in categories:
                    v_name = b.get(cat)
                    if v_name and v_name.strip() != "":
                        # Get vendor phone
                        cursor.execute("SELECT phone FROM vendor WHERE name=%s", (v_name,))
                        v_row = cursor.fetchone()
                        v_phone = v_row['phone'] if v_row else '9988776655'
                        
                        v_msg = f"Notice: Booking #{booking_id} from {b['name']} on {b['event_date']} has been CANCELLED by the customer. Please adjust your calendar. - Shubhlo"
                        send_sms_notification('Vendor', v_phone, v_msg)
                
                conn.commit()
                flash(f"Booking #{booking_id} has been successfully cancelled.", "success")
        except Exception as e:
            flash(f"Error cancelling booking: {e}", "danger")
        finally:
            conn.close()
    else:
        # Fallback simulation
        mock_bookings = session.get('mock_bookings', [])
        mb = next((x for x in mock_bookings if x['id'] == booking_id and x['email'] == email), None)
        if mb:
            mb['booking_status'] = 'Cancelled'
            # Send simulated SMS
            c_msg = f"Dear {mb['name']}, your booking #{booking_id} has been CANCELLED successfully. We hope to serve you again. - Shubhlo"
            send_sms_notification('Customer', mb['phone'], c_msg)
            
            # Vendor simulated notifications
            categories = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card']
            for cat in categories:
                v_name = mb.get(cat)
                if v_name and v_name.strip() != "":
                    v_msg = f"Notice: Booking #{booking_id} from {mb['name']} on {mb['event_date']} has been CANCELLED by the customer. Please adjust your calendar. - Shubhlo"
                    send_sms_notification('Vendor', '9988776655', v_msg)
            
            # Modify mock verifications in session too
            mock_verifications = session.get('mock_verifications', [])
            for mv in mock_verifications:
                if mv['booking_id'] == booking_id and mv['status'] != 'Verified':
                    mv['status'] = 'Cancelled'
            
            session.modified = True
            flash(f"Booking #{booking_id} cancelled successfully (Simulated Fallback Mode).", "success")
        else:
            flash("Booking not found in session fallback.", "danger")
            
    return redirect(url_for('dashboard'))

# Ratings Page

@app.route('/admin/blacklist/delete/<int:blacklist_id>', methods=['POST'])
def admin_blacklist_delete(blacklist_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM blacklist WHERE id=%s", (blacklist_id,))
                conn.commit()
                flash(f"Removed from blacklist successfully.", "success")
        except Exception as e:
            flash(f"Error removing from blacklist: {e}", "danger")
        finally:
            conn.close()
    else:
        mock_blacklist = session.get('mock_blacklist', [])
        mock_blacklist = [entry for entry in mock_blacklist if entry['id'] != blacklist_id]
        session['mock_blacklist'] = mock_blacklist
        session.modified = True
        flash(f"Removed from blacklist successfully (Simulated).", "success")
        
    return redirect(url_for('admin_dashboard'))

@app.route('/oauth/login/<provider>')
def oauth_login(provider):
    if provider not in ['google', 'facebook']:
        flash("Invalid login provider!", "danger")
        return redirect(url_for('login'))
    # In a production environment, you would redirect to the real OAuth provider.
    # Here, we render the beautiful mock consent screen.
    return render_template('mock_oauth.html', provider=provider)

@app.route('/oauth/callback/<provider>', methods=['POST'])
def oauth_callback(provider):
    if provider not in ['google', 'facebook']:
        flash("Invalid login provider!", "danger")
        return redirect(url_for('login'))
        
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name or not email:
        flash("Social authentication failed. Missing user details.", "danger")
        return redirect(url_for('login'))
        
    # Check if the user already exists in database
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
                user = cursor.fetchone()
                
                if user:
                    # User exists, log them in
                    session['user'] = user['email']
                    session['user_name'] = user['name']
                    flash(f"Successfully logged in with {provider.capitalize()}! Welcome back, {user['name']}.", "success")
                else:
                    # User doesn't exist, create a new user account with a mock password
                    # and then log them in.
                    mock_password = f"{provider}_oauth_bypass_{os.urandom(4).hex()}"
                    cursor.execute(
                        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                        (name, email, mock_password)
                    )
                    conn.commit()
                    
                    session['user'] = email
                    session['user_name'] = name
                    flash(f"Successfully registered and logged in with {provider.capitalize()}! Welcome, {name}.", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Error during social login: {e}", "danger")
            return redirect(url_for('login'))
        finally:
            conn.close()
    else:
        # Fallback simulation if DB connection fails
        session['user'] = email
        session['user_name'] = name
        flash(f"Logged in via fallback {provider.capitalize()} mode (Database offline).", "warning")
        return redirect(url_for('home'))

# Signup

def inject_chatbot(response):
    try:
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            html = response.get_data(as_text=True)
            chatbot_html = (
                '<link rel="stylesheet" href="/static/chatbot.css?v=50">\n'
                '<script src="/static/chatbot.js?v=50"></script>\n'
            )
            if '</body>' in html and '/static/chatbot.js' not in html:
                html = html.replace('</body>', f'{chatbot_html}</body>')
                response.set_data(html)
    except Exception as e:
        print(f"Error injecting chatbot assets: {e}")
    return response

@app.route('/customer/accept_counter_offer/<int:booking_id>')
def customer_accept_counter_offer(booking_id):
    if 'user' not in session:
        flash("Please log in to accept offer.", "warning")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE booking SET counter_offer_status='Accepted' WHERE id=%s", (booking_id,))
                conn.commit()
                flash("Counter offer accepted successfully! / वेंडर का बजट ऑफर स्वीकार कर लिया गया है।", "success")
        except Exception as e:
            flash(f"Error accepting counter offer: {e}", "danger")
        finally:
            conn.close()
    else:
        mock_user_bookings = session.get('mock_user_bookings', [])
        for mb in mock_user_bookings:
            if mb.get('id') == booking_id:
                mb['counter_offer_status'] = 'Accepted'
        session['mock_user_bookings'] = mock_user_bookings
        flash("Counter offer accepted successfully (Simulated)! / वेंडर का बजट ऑफर स्वीकार किया गया!", "success")
        
    return redirect(url_for('dashboard'))

# Vendor Send Counter Offer

def dispatch_fast2sms(phone, message):
    api_key = os.environ.get("FAST2SMS_API_KEY", FAST2SMS_API_KEY).strip()
    if not api_key:
        return False

    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]
    if len(digits) != 10:
        print(f"[FAST2SMS ERR]: Invalid 10-digit phone number '{phone}'")
        return False

    import urllib.request
    import urllib.parse
    import json
    import re

    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        otp_match = re.search(r'\b\d{4,8}\b', str(message))
        if "otp" in str(message).lower() and otp_match:
            otp_val = otp_match.group(0)
            payload = {
                "route": "otp",
                "variables_values": otp_val,
                "numbers": digits
            }
        else:
            payload = {
                "route": "q",
                "message": str(message),
                "language": "english",
                "flash": "0",
                "numbers": digits
            }
            
        headers = {
            "authorization": api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            if res_json.get("return"):
                print(f"[FAST2SMS DISPATCH SUCCESS to {digits}]: {res_json}")
                return True
            else:
                print(f"[FAST2SMS DISPATCH FAILURE to {digits}]: {res_json}")
                return False
    except Exception as e:
        print(f"[FAST2SMS DISPATCH EXCEPTION to {phone}]: {e}")
        return False

def dispatch_twilio(phone, message):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_phone = os.environ.get("TWILIO_PHONE_NUMBER", "").strip()
    if not (account_sid and auth_token and from_phone):
        return False

    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) == 10:
        target_phone = "+91" + digits
    elif str(phone).startswith("+"):
        target_phone = str(phone)
    else:
        target_phone = "+" + digits

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_phone,
            to=target_phone
        )
        print(f"[TWILIO DISPATCH SUCCESS to {target_phone}]: SID {msg.sid}")
        return True
    except Exception as e:
        print(f"[TWILIO DISPATCH EXCEPTION to {phone}]: {e}")
        return False

@app.template_filter('urlquote')
def urlquote_filter(value):
    if not value:
        return ""
    import urllib.parse
    return urllib.parse.quote(str(value))

@app.template_filter('clean_phone_indian')

def clean_phone_indian_filter(value):
    if not value:
        return ""
    digits = ''.join(c for c in str(value) if c.isdigit())
    if len(digits) == 10:
        return "91" + digits
    if len(digits) > 10 and digits.startswith("91"):
        return digits
    if len(digits) > 10:
        return digits[-10:]
    return digits

@app.route('/admin/reset_all_data', methods=['GET', 'POST'])
@app.route('/reset_all_data', methods=['GET', 'POST'])
@app.route('/reset_session', methods=['GET', 'POST'])
def admin_reset_all_data():
    if 'admin' not in session:
        flash("Admin access required.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                for tbl in ["booking_verification", "selected_services", "simulated_sms", "vendor_availability", "booking", "rating", "contact_messages", "vendor", "users"]:
                    try:
                        cursor.execute(f"TRUNCATE TABLE {tbl}")
                    except Exception:
                        pass
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                conn.commit()
        except Exception as e:
            print(f"Error truncating DB: {e}")
        finally:
            conn.close()

    global GLOBAL_REGISTERED_VENDORS, GLOBAL_REGISTERED_USERS, GLOBAL_VENDOR_RATINGS
    GLOBAL_REGISTERED_VENDORS = []
    GLOBAL_REGISTERED_USERS = []
    GLOBAL_VENDOR_RATINGS = []

    session.pop('mock_bookings', None)
    session.pop('mock_vendors', None)
    session.pop('mock_users', None)
    session.pop('mock_sms', None)
    session.pop('mock_verifications', None)
    session.pop('mock_tickets', None)
    session.pop('mock_contact_messages', None)
    session.modified = True

    flash("🧹 ALL Test Data, Vendors, Users, and Bookings have been 100% TRUNCATED and RESET! System is fresh.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/rating', methods=['GET', 'POST'])
@app.route('/rate_vendor', methods=['GET', 'POST'])
@app.route('/rate-vendor', methods=['GET', 'POST'])
def rating():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id') or 101
        v_name = request.form.get('vendor_name')
        stars_val = request.form.get('stars') or request.form.get('rating') or 5
        review_text = request.form.get('feedback') or request.form.get('review') or ''
        c_name = request.form.get('customer_name') or session.get('user_name', 'Customer')

        if not v_name:
            flash("Please enter or select a vendor name to rate / कृपया वेंडर का नाम दर्ज करें।", "danger")
            return redirect(url_for('rating'))

        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO rating (vendor_name, stars, feedback, customer_name, booking_id) VALUES (%s, %s, %s, %s, %s)", (v_name, stars_val, review_text, c_name, booking_id))
                    conn.commit()
                    flash(f"Thank you! Your rating for '{v_name}' has been submitted ⭐", "success")
            except Exception as e:
                flash(f"Error submitting rating: {e}", "danger")
            finally:
                conn.close()
        else:
            if 'mock_vendor_ratings' not in session:
                session['mock_vendor_ratings'] = []
            session['mock_vendor_ratings'].append({
                'booking_id': int(booking_id),
                'vendor_name': v_name,
                'stars': int(stars_val),
                'feedback': review_text
            })
            session.modified = True
            flash(f"Thank you! Your rating for '{v_name}' has been recorded ⭐", "success")
        
        return redirect(url_for('dashboard') if 'user' in session else url_for('services'))

    vendor_param = request.args.get('vendor') or request.args.get('vendor_name') or ''
    booking_id_param = request.args.get('booking_id') or ''
    
    user_bookings = []
    if 'user' in session:
        email = session['user']
        conn = get_db_connection()
        if conn is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, venue, catering, dj, decoration, transport, photography FROM booking WHERE email=%s", (email,))
                    user_bookings = cursor.fetchall()
            except Exception as e:
                print(f"Error fetching user bookings for rating page: {e}")
            finally:
                conn.close()
        else:
            user_bookings = session.get('mock_bookings', [])

    return render_template('rating.html', vendor_name=vendor_param, booking_id=booking_id_param, user_bookings=user_bookings)

@app.route('/booking/invoice/<int:booking_id>')
@app.route('/download_invoice/<int:booking_id>', endpoint='download_invoice')
@app.route('/booking/invoice', defaults={'booking_id': 1})
@app.route('/download_invoice', defaults={'booking_id': 1}, endpoint='download_invoice')
def booking_invoice(booking_id=1):
    if 'user' not in session and 'admin' not in session:
        flash("Please log in to view the order invoice.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    booking = None
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM booking WHERE id=%s", (booking_id,))
                booking = cursor.fetchone()
        except Exception as e:
            print(f"Error fetching invoice: {e}")
        finally:
            conn.close()
            
    if not booking:
        # Fallback search in mock session bookings
        mock_bookings = session.get('mock_bookings', [])
        booking = next((b for b in mock_bookings if b.get('id') == booking_id or str(b.get('id')) == str(booking_id)), None)

    if not booking:
        flash("Booking invoice not found.", "danger")
        return redirect(url_for('dashboard'))

    # Compile itemized vendors list for invoice
    categories_cols = ['venue', 'catering', 'dj', 'decoration', 'transport', 'photography', 'shahi_sawari', 'invitation_card', 'security_guard', 'makeup', 'mehendi', 'dhol_band', 'pandit', 'choreographer', 'wedding_planner', 'anchor', 'fireworks', 'mocktail', 'safa']
    selected_items = []
    num_vendors = 0
    for cat in categories_cols:
        v_name = booking.get(cat)
        if v_name and str(v_name).strip() != "":
            num_vendors += 1
            selected_items.append({
                'category': cat.replace('_', ' ').title(),
                'name': v_name,
                'price': 50000.00 if cat == 'venue' else 15000.00
            })

    if num_vendors == 0:
        num_vendors = 1

    advance_paid = float(booking.get('advance_paid') or (num_vendors * 5118.00))
    platform_fee = num_vendors * 100.00
    gst_tax = num_vendors * 18.00
    deposit_credit = num_vendors * 5000.00
    total_est_amount = float(booking.get('amount') or (deposit_credit + 50000.00))
    remaining_balance = total_est_amount - deposit_credit

    return render_template(
        'invoice.html',
        booking=booking,
        selected_items=selected_items,
        num_vendors=num_vendors,
        advance_paid=advance_paid,
        platform_fee=platform_fee,
        gst_tax=gst_tax,
        deposit_credit=deposit_credit,
        total_est_amount=total_est_amount,
        remaining_balance=remaining_balance
    )

# Payment Page

@app.route('/ad-video')
@app.route('/promo-video')
def ad_video():
    return render_template('ad_video.html')

@app.route('/youtube')
def youtube():
    return render_template('youtube.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first to access the dashboard.", "warning")
        return redirect(url_for('login'))

    email = session['user']
    user_name = session.get('user_name', email.split('@')[0].capitalize())

    conn = get_db_connection()
    bookings = []
    
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM booking WHERE email=%s ORDER BY event_date DESC", (email,))
                bookings = cursor.fetchall()
                
                # Fetch verifications for each booking
                for b in bookings:
                    cursor.execute(
                        "SELECT vendor_name, service_type, status FROM booking_verification WHERE booking_id=%s",
                        (b['id'],)
                    )
                    b['verifications'] = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching dashboard bookings: {e}")
        finally:
            conn.close()
    else:
        # Fallback realistic mock data if DB is down
        mock_bookings = session.get('mock_bookings', [])
        import copy
        bookings = copy.deepcopy(mock_bookings)
        
        mock_verifications = session.get('mock_verifications', [])
        for b in bookings:
            b['verifications'] = [
                v for v in mock_verifications if v['booking_id'] == b['id']
            ]
            
        if not bookings:
            bookings = []

    # Calculate statistics
    total_bookings = len(bookings)
    total_spent = sum(float(b['amount']) for b in bookings if b['payment_status'] == 'Paid')

    return render_template(
        'dashboard.html',
        bookings=bookings,
        total_bookings=total_bookings,
        total_spent=total_spent,
        user_name=user_name,
        user_email=email
    )

# Admin Dashboard

@app.route('/coming-soon')
def coming_soon():
    return render_template('coming_soon_promo.html')

# Interactive Commercial Video Player Route

@app.route('/customer/submit_ticket', methods=['POST'])
def submit_customer_ticket():
    if 'user' not in session:
        flash("Please log in to submit inquiries, feedback or complaints.", "warning")
        return redirect(url_for('login'))
        
    ticket_type = request.form.get('ticket_type', 'General Inquiry')
    subject = request.form.get('subject', 'Customer Support Ticket')
    details = request.form.get('details', '')
    booking_id = request.form.get('booking_id', None)
    
    if not subject or not details:
        flash("Please fill in both subject and description fields. / विषय और विवरण दोनों भरना अनिवार्य है।", "danger")
        return redirect(url_for('dashboard'))
        
    email = session['user']
    user_name = session.get('user_name', email.split('@')[0].capitalize())
    
    if 'mock_tickets' not in session:
        session['mock_tickets'] = []
        
    new_ticket = {
        'id': 500 + len(session['mock_tickets']) + 1,
        'user_email': email,
        'user_name': user_name,
        'ticket_type': ticket_type,
        'subject': subject,
        'details': details,
        'booking_id': booking_id or 'General',
        'status': 'Pending Admin Review',
        'admin_response': '',
        'created_at': '2026-08-09'
    }
    
    session['mock_tickets'].append(new_ticket)
    session.modified = True
    
    flash("Your Feedback/Inquiry/Complaint ticket has been submitted to Admin! / आपका फ़ीडबैक, पूछताछ या शिकायत सफलतापूर्वक एडमिन को भेज दी गई है।", "success")
    return redirect(url_for('dashboard'))

@app.route('/admin/resolve_ticket/<int:ticket_id>', methods=['POST'])
def admin_resolve_ticket(ticket_id):
    if 'admin' not in session:
        flash("Admin login required.", "danger")
        return redirect(url_for('login'))
        
    status = request.form.get('status', 'Resolved')
    admin_response = request.form.get('admin_response', '')
    
    mock_tickets = session.get('mock_tickets', [])
    for t in mock_tickets:
        if t.get('id') == ticket_id:
            t['status'] = status
            t['admin_response'] = admin_response
            break
            
    session['mock_tickets'] = mock_tickets
    session.modified = True
    flash(f"Customer Ticket #{ticket_id} updated to {status}!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/owner/login', methods=['GET', 'POST'])
def owner_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == "owner@shubhlo.com" and password == "owner123":
            session['admin'] = email
            session['is_owner'] = True
            flash("Welcome Master Owner! Full system control activated.", "success")
            return redirect(url_for('owner_dashboard'))
        else:
            flash("Invalid owner credentials!", "danger")
    return redirect(url_for('login'))

@app.route('/owner/dashboard')
def owner_dashboard():
    session['admin'] = session.get('admin', 'owner@shubhlo.com')
    session['is_owner'] = True
    
    conn = get_db_connection()
    db_vendors = []
    db_bookings = []
    
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM vendor ORDER BY id DESC")
                db_vendors = cursor.fetchall()
                cursor.execute("SELECT * FROM booking ORDER BY id DESC")
                db_bookings = cursor.fetchall()
        except Exception as e:
            print(f"Error loading owner dashboard DB data: {e}")
        finally:
            conn.close()
            
    if not db_vendors:
        db_vendors = session.get('mock_vendors', MOCK_VENDORS.get('venue', []))
    if not db_bookings:
        db_bookings = session.get('mock_bookings', [])
        
    all_tickets = session.get('mock_tickets', [
        {
            'id': 501,
            'user_name': 'Rahul Sharma',
            'user_email': 'rahul@example.com',
            'ticket_type': 'General Inquiry',
            'subject': 'Booking Date Change Process',
            'details': 'How can I change my event date after booking confirmation?',
            'status': 'Resolved / उत्तर दिया गया',
            'admin_response': 'Contact support or vendor directly.'
        }
    ])

    total_gross_volume = sum(float(b.get('amount', 0)) for b in db_bookings)
    total_deposits_collected = sum(float(b.get('token_deposit', 0)) for b in db_bookings)
    commission_rate = session.get('commission_rate', 10.0)
    platform_net_revenue = (total_gross_volume * commission_rate) / 100.0
    is_maintenance = session.get('is_maintenance', False)

    return render_template(
        'owner_dashboard.html',
        vendors=db_vendors,
        bookings=db_bookings,
        tickets=all_tickets,
        total_vendors=len(db_vendors),
        total_gross_volume=total_gross_volume,
        total_deposits_collected=total_deposits_collected,
        commission_rate=commission_rate,
        platform_net_revenue=platform_net_revenue,
        is_maintenance=is_maintenance
    )

@app.route('/owner/update_platform_commission', methods=['POST'])
def owner_update_commission():
    rate = request.form.get('commission_rate', 10.0)
    try:
        session['commission_rate'] = float(rate)
        session.modified = True
        flash(f"Platform fee commission updated to {float(rate)}%!", "success")
    except Exception as e:
        flash(f"Error updating commission: {e}", "danger")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/toggle_maintenance', methods=['POST'])
def owner_toggle_maintenance():
    current_state = session.get('is_maintenance', False)
    session['is_maintenance'] = not current_state
    session.modified = True
    status_str = "PAUSED (Maintenance)" if not current_state else "ACTIVE"
    flash(f"Platform bookings are now {status_str}!", "warning" if not current_state else "success")
    return redirect(url_for('owner_dashboard'))


if __name__ == '__main__':
    migrate_db_schema()
    app.run(debug=True, host='0.0.0.0', port=8080)

@app.route('/owner/approve_and_unlock/<int:booking_id>', methods=['POST'])
def owner_approve_and_unlock(booking_id):
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE booking SET status='Confirmed', booking_status='Confirmed' WHERE id=%s", (booking_id,))
                conn.commit()
        except Exception as e:
            print(f"DB update error in owner_approve_and_unlock: {e}")
        finally:
            conn.close()

    mock_bookings = session.get('mock_bookings', [])
    for b in mock_bookings:
        if b.get('id') == booking_id:
            b['status'] = 'Confirmed'
            b['booking_status'] = 'Confirmed'
            b['unlocked_by_owner'] = True
    session.modified = True
    flash(f"Booking #{booking_id} approved and customer contact details unlocked to Vendor! / बुकिंग #{booking_id} कन्फर्म कर दी गई है और ग्राहक का संपर्क वेंडर के लिए अनलॉक कर दिया गया है।", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/submit_vendor_rating', methods=['POST'])
@app.route('/submit_rating', methods=['POST'])
@app.route('/submit-rating', methods=['POST'])
def submit_vendor_rating():
    if 'user' not in session:
        flash("Please log in first to submit a rating.", "warning")
        return redirect(url_for('login'))
        
    booking_id = request.form.get('booking_id')
    vendor_name = request.form.get('vendor_name')
    stars = request.form.get('stars')
    feedback = request.form.get('feedback', '')

    if not booking_id or not vendor_name or not stars:
        flash("Invalid rating submission. Missing required fields.", "danger")
        return redirect(url_for('dashboard'))

    try:
        stars_int = int(stars)
        if stars_int < 1 or stars_int > 5:
            raise ValueError()
    except ValueError:
        flash("Rating must be between 1 and 5 stars.", "danger")
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Check if rating already exists for this booking and vendor
                cursor.execute("SELECT id FROM rating WHERE booking_id=%s AND vendor_name=%s", (booking_id, vendor_name))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute(
                        "UPDATE rating SET stars=%s, feedback=%s WHERE booking_id=%s AND vendor_name=%s",
                        (stars_int, feedback, booking_id, vendor_name)
                    )
                    flash(f"Your rating for {vendor_name} has been updated! ⭐", "success")
                else:
                    cursor.execute(
                        "INSERT INTO rating (stars, feedback, vendor_name, booking_id) VALUES (%s, %s, %s, %s)",
                        (stars_int, feedback, vendor_name, booking_id)
                    )
                    flash(f"Thank you for rating {vendor_name}! ⭐", "success")
                conn.commit()
        except Exception as e:
            flash(f"Error saving vendor rating: {e}", "danger")
        finally:
            conn.close()
    else:
        # Fallback simulation
        if 'mock_vendor_ratings' not in session:
            session['mock_vendor_ratings'] = []
            
        mock_ratings = session['mock_vendor_ratings']
        # Check if already exists
        existing = next((r for r in mock_ratings if r.get('booking_id') == int(booking_id) and r.get('vendor_name') == vendor_name), None)
        if existing:
            existing['stars'] = stars_int
            existing['feedback'] = feedback
            flash(f"Your rating for {vendor_name} has been updated (Simulated)! ⭐", "success")
        else:
            mock_ratings.append({
                'booking_id': int(booking_id),
                'vendor_name': vendor_name,
                'stars': stars_int,
                'feedback': feedback
            })
            flash(f"Thank you for rating {vendor_name} (Simulated)! ⭐", "success")
        session['mock_vendor_ratings'] = mock_ratings
        session.modified = True

    return redirect(url_for('dashboard'))

@app.route('/api/ai-assistant', methods=['POST'])
def ai_assistant_api():
    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        q_lower = query.lower()

        # Database lookup for real vendors if requested
        vendor_info = ""
        conn = get_db_connection()
        if conn is not None:
            cur = conn.cursor()
            if 'venue' in q_lower or 'garden' in q_lower or 'lawn' in q_lower or 'place' in q_lower:
                cur.execute("SELECT name, tehsil, price FROM vendors WHERE (LOWER(service) LIKE '%venue%' OR LOWER(service) LIKE '%garden%') AND approved = 1 LIMIT 3")
                rows = cur.fetchall()
                if rows:
                    vendor_info = "<br><br><strong>📍 Available Venues in Database:</strong><br>" + "<br>".join([f"• <strong>{r[0]}</strong> ({r[1]}): ₹{r[2]:,.0f}" for r in rows])
            elif 'catering' in q_lower or 'food' in q_lower or 'khana' in q_lower or 'cater' in q_lower:
                cur.execute("SELECT name, tehsil, price FROM vendors WHERE LOWER(service) LIKE '%cater%' AND approved = 1 LIMIT 3")
                rows = cur.fetchall()
                if rows:
                    vendor_info = "<br><br><strong>🍲 Recommended Caterers:</strong><br>" + "<br>".join([f"• <strong>{r[0]}</strong> ({r[1]}): ₹{r[2]:,.0f}" for r in rows])
            elif 'dj' in q_lower or 'music' in q_lower or 'sound' in q_lower:
                cur.execute("SELECT name, tehsil, price FROM vendors WHERE LOWER(service) LIKE '%dj%' AND approved = 1 LIMIT 3")
                rows = cur.fetchall()
                if rows:
                    vendor_info = "<br><br><strong>🎵 Verified DJs & Sound Systems:</strong><br>" + "<br>".join([f"• <strong>{r[0]}</strong> ({r[1]}): ₹{r[2]:,.0f}" for r in rows])
            conn.close()

        # Contextual Smart AI responses in English
        if any(w in q_lower for w in ["hi", "hello", "hey", "namaste", "help", "how are you", "start"]):
          reply = ("👑 <strong>Hello! I am your Shubhlo AI Assistant!</strong><br>"
                   "I am here to help you plan your perfect event. You can ask me about:<br>"
                   "• 🏰 Marriage Garden & Venue Rates<br>"
                   "• 🍲 Catering & Food Menu Packages<br>"
                   "• 🎵 DJ, Music & Sound Systems<br>"
                   "• 📸 Photography & Video Coverage<br>"
                   "• 📝 Step-by-Step Booking Guide<br><br>"
                   "<em>Click any suggestion chip below or type your question! ✨</em>")
        elif any(w in q_lower for w in ["book", "step", "process", "how"]):
          reply = ("📝 <strong>Event Booking Process:</strong><br>"
                   "1. <strong>Step 1:</strong> Click <a href='/booking1'>Book Now</a> and select your event date & Tehsil location.<br>"
                   "2. <strong>Step 2:</strong> Compare verified Venues, Catering, DJ, Photography & Decoration vendors.<br>"
                   "3. <strong>Step 3:</strong> Review your selected service summary.<br>"
                   "4. <strong>Step 4:</strong> Pay a nominal token deposit of ₹5,100 to lock your booking!")
        elif any(w in q_lower for w in ["price", "rate", "cost", "budget", "package"]):
          reply = ("💰 <strong>Shubhlo Best Price Guarantee:</strong><br>"
                   "• 🏰 Venues & Lawns: ₹1,00,000 - ₹2,50,000<br>"
                   "• 🍲 Catering Packages: ₹50,000 - ₹1,50,000<br>"
                   "• 🎵 DJ & Sound: ₹15,000 - ₹35,000<br>"
                   "• 📸 Photography: ₹25,000 - ₹60,000<br>"
                   "• 🌸 Decoration: ₹20,000 - ₹50,000" + vendor_info)
        elif any(w in q_lower for w in ["contact", "phone", "number", "email", "support", "help"]):
          reply = ("📞 <strong>Shubhlo Direct Support:</strong><br>"
                   "• Helpline Call / WhatsApp: <strong>+91 7067883131</strong><br>"
                   "• Support Email: <strong>info@shubhlo.com</strong><br>"
                   "• Head Office: Saket, Madhya Pradesh<br>"
                   "• Support Hours: 24/7 Available")
        elif any(w in q_lower for w in ["vendor", "register", "join", "partner"]):
          reply = ("🤝 <strong>Become a Shubhlo Vendor Partner:</strong><br>"
                   "Grow your business with zero commission listings on Shubhlo!<br>"
                   "👉 <a href='/vendor/register' style='color:#10b981; font-weight:bold;'>Register as a Vendor Here ➔</a>")
        else:
          reply = (f"✨ <strong>Shubhlo AI Assistant:</strong><br>"
                   f"Thank you for asking about: '<em>{query}</em>'<br><br>"
                   "I am available 24/7 to assist you with verified vendor listings, price comparisons, and event bookings across Madhya Pradesh." + vendor_info)

        return jsonify({'status': 'success', 'reply': reply})
    except Exception as e:
        return jsonify({'status': 'error', 'reply': 'An unexpected error occurred. Please try asking your question again!'}), 500

def get_permitted_locations():
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, state, district, tehsil FROM permitted_locations ORDER BY state, district, tehsil")
                rows = cursor.fetchall()
                if rows:
                    return rows
        except Exception as e:
            print(f"Error fetching permitted locations: {e}")
        finally:
            conn.close()

    return session.get('permitted_locations', DEFAULT_PERMITTED_LOCATIONS)

def is_location_permitted(state, district, tehsil):
    if not state or not district or not tehsil:
        return False

    locations = get_permitted_locations()
    st_clean = str(state).strip().lower()
    dist_clean = str(district).strip().lower()
    teh_clean = str(tehsil).strip().lower()

    for loc in locations:
        loc_st = str(loc.get('state', '')).strip().lower()
        loc_dist = str(loc.get('district', '')).strip().lower()
        loc_teh = str(loc.get('tehsil', '')).strip().lower()

        if loc_st == st_clean and loc_dist == dist_clean and loc_teh == teh_clean:
            return True
    return False

@app.route('/owner/add_location', methods=['POST'])
def owner_add_location():
    if not session.get('is_owner') and session.get('admin') != 'owner@shubhlo.com':
        flash("Access Denied: Owner permission required! / केवल ऑनर्स कंट्रोल पैनल!", "danger")
        return redirect(url_for('login'))

    state = request.form.get('state', '').strip()
    district = request.form.get('district', '').strip()
    tehsil = request.form.get('tehsil', '').strip()

    if not state or not district or not tehsil:
        flash("Please enter State, District, and Tehsil. / कृपया राज्य, ज़िला और तहसील दर्ज करें।", "danger")
        return redirect(url_for('owner_dashboard'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM permitted_locations WHERE LOWER(state)=LOWER(%s) AND LOWER(district)=LOWER(%s) AND LOWER(tehsil)=LOWER(%s)",
                    (state, district, tehsil)
                )
                if cursor.fetchone():
                    flash(f"Location '{tehsil}, {district}, {state}' is already permitted! / यह स्थान पहले से अनुमति प्राप्त है!", "warning")
                else:
                    cursor.execute(
                        "INSERT INTO permitted_locations (state, district, tehsil) VALUES (%s, %s, %s)",
                        (state, district, tehsil)
                    )
                    conn.commit()
                    flash(f"Permitted Location '{tehsil}, {district}, {state}' added successfully! / स्थान अनुमति स्वीकृत की गई!", "success")
        except Exception as e:
            flash(f"Error adding permitted location: {e}", "danger")
        finally:
            conn.close()
    else:
        mock_locs = session.get('permitted_locations', list(DEFAULT_PERMITTED_LOCATIONS))
        if any(str(m['state']).lower() == state.lower() and str(m['district']).lower() == district.lower() and str(m['tehsil']).lower() == tehsil.lower() for m in mock_locs):
            flash(f"Location '{tehsil}, {district}, {state}' is already permitted!", "warning")
        else:
            new_loc = {'id': 900 + len(mock_locs), 'state': state, 'district': district, 'tehsil': tehsil}
            mock_locs.append(new_loc)
            session['permitted_locations'] = mock_locs
            session.modified = True
            flash(f"Permitted Location '{tehsil}, {district}, {state}' added (Simulated)! / स्थान अनुमति स्वीकृत की गई!", "success")

    return redirect(url_for('owner_dashboard'))

@app.route('/owner/delete_location/<int:loc_id>', methods=['POST', 'GET'])
def owner_delete_location(loc_id):
    if not session.get('is_owner') and session.get('admin') != 'owner@shubhlo.com':
        flash("Access Denied: Owner permission required!", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM permitted_locations WHERE id=%s", (loc_id,))
                conn.commit()
                flash("Location permission revoked! / स्थान अनुमति सफलतापूर्वक हटाई गई!", "info")
        except Exception as e:
            flash(f"Error revoking location permission: {e}", "danger")
        finally:
            conn.close()
    else:
        mock_locs = session.get('permitted_locations', list(DEFAULT_PERMITTED_LOCATIONS))
        session['permitted_locations'] = [m for m in mock_locs if str(m.get('id')) != str(loc_id)]
        session.modified = True
        flash("Location permission revoked (Simulated)! / स्थान अनुमति सफलतापूर्वक हटाई गई!", "info")

@app.route('/owner/toggle_setting', methods=['POST'])
def owner_toggle_setting():
    if not session.get('is_owner') or session.get('admin') != 'owner@shubhlo.com':
        flash("Access Denied: Only Platform Owner can toggle system settings!", "danger")
        return redirect(url_for('login'))

    setting_key = request.form.get('setting_key')
    setting_value = request.form.get('setting_value', 'ON')
    
    label = "Customer Booking" if setting_key == "allow_customer_booking" else "Vendor Registration"
    
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO system_settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value=%s",
                    (setting_key, setting_value, setting_value)
                )
                conn.commit()
        except Exception as e:
            print(f"Error updating system_settings DB: {e}")
        finally:
            conn.close()

    mock_settings = session.get('mock_system_settings', {})
    if setting_key not in mock_settings:
        mock_settings[setting_key] = {}
    mock_settings[setting_key]['value'] = setting_value
    session['mock_system_settings'] = mock_settings
    session.modified = True

    status_txt = "ACTIVATED (ON) 🟢" if setting_value == "ON" else "PAUSED (OFF) 🔴"
    flash(f"Owner Authority Update: {label} has been {status_txt}!", "success" if setting_value == "ON" else "warning")
    return redirect(url_for('owner_dashboard'))

@app.route('/admin/vendor/blacklist/<int:vendor_id>', methods=['POST'])
def admin_vendor_blacklist(vendor_id):
    if not session.get('is_owner') and 'admin' not in session:
        flash("Access Denied: Only Owner/Admin can blacklist vendors!", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    v_email = None
    v_phone = None
    v_name = None

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, email, phone FROM vendor WHERE id=%s", (vendor_id,))
                v = cursor.fetchone()
                if v:
                    v_email = v['email']
                    v_phone = v['phone']
                    v_name = v['name']
                    cursor.execute("UPDATE vendor SET approval_status='Blacklisted' WHERE id=%s", (vendor_id,))
                    if v_email:
                        cursor.execute("INSERT IGNORE INTO blacklist (type, value, reason) VALUES ('Email', %s, %s)", (v_email.lower(), f"Blacklisted Vendor: {v_name}"))
                    if v_phone:
                        cursor.execute("INSERT IGNORE INTO blacklist (type, value, reason) VALUES ('Phone', %s, %s)", (v_phone[-10:], f"Blacklisted Vendor: {v_name}"))
                    conn.commit()
        except Exception as e:
            print(f"Error blacklisting vendor DB: {e}")
        finally:
            conn.close()

    mock_vendors = session.get('mock_vendors', [])
    for v in mock_vendors:
        if v.get('id') == vendor_id:
            v['approval_status'] = 'Blacklisted'
            v_email = v.get('email')
            v_phone = v.get('phone')
            v_name = v.get('name')

    mock_bl = session.get('mock_blacklist', [])
    if v_email and not any(b['value'] == v_email.lower() for b in mock_bl):
        mock_bl.append({'id': 300 + len(mock_bl), 'type': 'Email', 'value': v_email.lower(), 'reason': f"Blacklisted Vendor: {v_name}"})
    if v_phone and not any(b['value'] == str(v_phone)[-10:] for b in mock_bl):
        mock_bl.append({'id': 301 + len(mock_bl), 'type': 'Phone', 'value': str(v_phone)[-10:], 'reason': f"Blacklisted Vendor: {v_name}"})
    session['mock_blacklist'] = mock_bl
    session.modified = True

    flash(f"Vendor #{vendor_id} ({v_name or ''}) has been BLACKLISTED and permanently blocked from logging in! / वेंडर को ब्लैकलिस्ट कर दिया गया है और लॉगिन ब्लॉक कर दिया गया है।", "warning")
    return redirect(url_for('owner_dashboard'))

@app.route('/admin/user/blacklist', methods=['POST'])
def admin_user_blacklist():
    if not session.get('is_owner') and 'admin' not in session:
        flash("Access Denied: Only Owner/Admin can blacklist customers!", "danger")
        return redirect(url_for('login'))

    user_val = request.form.get('value', '').strip()
    b_type = request.form.get('type', 'Email')
    reason = request.form.get('reason', 'Blacklisted by Owner due to fake/suspicious activity')

    if not user_val:
        flash("Please enter an email or phone number to blacklist.", "danger")
        return redirect(url_for('owner_dashboard'))

    clean_val = user_val.lower()
    if b_type == 'Phone':
        clean_val = ''.join(filter(str.isdigit, clean_val))[-10:]

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT IGNORE INTO blacklist (type, value, reason) VALUES (%s, %s, %s)", (b_type, clean_val, reason))
                cursor.execute("DELETE FROM users WHERE email=%s OR phone=%s", (clean_val, clean_val))
                conn.commit()
        except Exception as e:
            print(f"Error blacklisting user DB: {e}")
        finally:
            conn.close()

    mock_bl = session.get('mock_blacklist', [])
    if not any(b['value'] == clean_val for b in mock_bl):
        mock_bl.append({'id': 400 + len(mock_bl), 'type': b_type, 'value': clean_val, 'reason': reason})
        session['mock_blacklist'] = mock_bl

    mock_users = session.get('mock_users', [])
    session['mock_users'] = [u for u in mock_users if u.get('email', '').lower() != clean_val and u.get('phone', '') != clean_val]
    session.modified = True

    flash(f"Customer identifier '{user_val}' has been BLACKLISTED and permanently blocked from login! / ग्राहक खाता ब्लैकलिस्ट कर दिया गया है और लॉगिन ब्लॉक कर दिया गया है।", "warning")
    return redirect(url_for('owner_dashboard'))

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
def admin_user_delete(user_id):
    if not session.get('is_owner') and 'admin' not in session:
        flash("Access Denied: Only Owner/Admin can delete customer accounts!", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
                conn.commit()
        except Exception as e:
            print(f"Error deleting user DB: {e}")
        finally:
            conn.close()

    mock_users = session.get('mock_users', [])
    session['mock_users'] = [u for u in mock_users if u.get('id') != user_id]
    session.modified = True

    flash(f"Customer user account #{user_id} permanently deleted.", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/admin/blacklist/remove', methods=['POST'])
def admin_blacklist_remove():
    if not session.get('is_owner') and 'admin' not in session:
        flash("Access Denied!", "danger")
        return redirect(url_for('login'))

    val = request.form.get('value', '').strip().lower()
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM blacklist WHERE value=%s OR value LIKE %s", (val, f"%{val}"))
                conn.commit()
        except Exception as e:
            print(f"Error removing from blacklist DB: {e}")
        finally:
            conn.close()

    mock_bl = session.get('mock_blacklist', [])
    session['mock_blacklist'] = [b for b in mock_bl if str(b.get('value', '')).lower() != val]
    session.modified = True

    flash(f"Identifier '{val}' removed from blacklist. Login access restored!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/contact/reply/<int:msg_id>', methods=['POST'])
def respond_contact_message(msg_id):
    if not (session.get('admin') or session.get('is_owner')):
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    reply_text = request.form.get('owner_reply', '').strip()
    status_text = request.form.get('status', 'Responded')

    # Update in GLOBAL_CONTACT_MESSAGES
    for m in GLOBAL_CONTACT_MESSAGES:
        if str(m.get('id')) == str(msg_id):
            m['owner_reply'] = reply_text
            m['status'] = status_text

    # Update in session
    session_msgs = session.get('mock_contact_messages', [])
    for m in session_msgs:
        if str(m.get('id')) == str(msg_id):
            m['owner_reply'] = reply_text
            m['status'] = status_text
    session.modified = True

    # Update in DB
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE contact_messages SET owner_reply=%s, status=%s WHERE id=%s",
                    (reply_text, status_text, msg_id)
                )
                conn.commit()
        except Exception as e:
            print(f"Error updating contact message in DB: {e}")
        finally:
            conn.close()

    flash(f"Response saved for message #{msg_id}!", "success")
    return redirect(request.referrer or url_for('owner_dashboard'))

@app.route('/booking/receipt/<int:booking_id>')
def booking_receipt(booking_id):
    if 'user' not in session and 'admin' not in session:
        flash("Please log in to view booking receipt. / रसीद देखने के लिए कृपया लॉगिन करें।", "warning")
        return redirect(url_for('login'))

    booking_item = None
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM booking WHERE id=%s", (booking_id,))
                booking_item = cursor.fetchone()
        except Exception as e:
            print(f"Error fetching receipt booking: {e}")
        finally:
            conn.close()

    if not booking_item:
        mock_bookings = session.get('mock_bookings', [])
        booking_item = next((b for b in mock_bookings if b.get('id') == booking_id), None)

    if not booking_item:
        flash("Booking record not found! / बुकिंग रिकॉर्ड नहीं मिला।", "danger")
        return redirect(url_for('dashboard'))

    # STRICT OWNER APPROVAL CHECK: Pass only generated if status is Confirmed/Approved!
    status_val = str(booking_item.get('status') or booking_item.get('booking_status') or '').strip().lower()
    if status_val not in ('confirmed', 'approved'):
        flash("⚠️ Booking Pass & Invoice Receipt can ONLY be generated AFTER Shubhlo Owner approves/confirms the booking! / ऑनर द्वारा बुकिंग की पुष्टि (Approved) करने के बाद ही बुकिंग पास जनरेट होगा।", "warning")
        return redirect(url_for('dashboard'))

    return render_template('booking_receipt.html', booking=booking_item)

def get_vendor_rating_stats(vendor_name):
    if not vendor_name:
        return {'avg_rating': 4.9, 'review_count': 15, 'stars_display': '⭐ 4.9'}

    clean_name = str(vendor_name).strip().lower()

    # Retrieve session ratings safely if inside request context
    sess_ratings = []
    try:
        if has_request_context():
            sess_ratings = list(session.get('mock_vendor_ratings', []))
    except Exception:
        sess_ratings = []

    all_mock_ratings = sess_ratings + GLOBAL_VENDOR_RATINGS
    matched_mock = [
        r for r in all_mock_ratings
        if str(r.get('vendor_name', '')).strip().lower() == clean_name
    ]

    if matched_mock:
        stars_list = [int(r.get('stars', 5)) for r in matched_mock if r.get('stars')]
        if stars_list:
            avg_val = round(sum(stars_list) / len(stars_list), 1)
            return {'avg_rating': avg_val, 'review_count': len(stars_list), 'stars_display': f"⭐ {avg_val}"}

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT stars FROM rating WHERE LOWER(TRIM(vendor_name))=%s", (clean_name,))
                rows = cursor.fetchall()
                if rows:
                    stars_list = [int(r['stars']) for r in rows if r.get('stars')]
                    if stars_list:
                        avg_val = round(sum(stars_list) / len(stars_list), 1)
                        return {'avg_rating': avg_val, 'review_count': len(stars_list), 'stars_display': f"⭐ {avg_val}"}
        except Exception as e:
            print(f"Error fetching DB rating stats for {vendor_name}: {e}")
        finally:
            conn.close()

    return {'avg_rating': 4.9, 'review_count': 15, 'stars_display': '⭐ 4.9'}

@app.route('/vendor/remove_service', methods=['POST', 'GET'])
@app.route('/vendor/remove_service/<service_name>', methods=['POST', 'GET'])
def vendor_remove_service(service_name=None):
    if 'vendor' not in session:
        flash("Please log in as a vendor first. / कृपया पहले वेंडर लॉग इन करें।", "warning")
        return redirect(url_for('vendor_login'))

    if not service_name:
        service_name = request.args.get('service_name') or request.form.get('service_name')

    if not service_name:
        flash("No service category specified for removal. / हटाने के लिए कोई सेवा श्रेणी निर्दिष्ट नहीं की गई।", "danger")
        return redirect(url_for('vendor_dashboard'))

    email = session['vendor']
    global GLOBAL_REGISTERED_VENDORS

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                # Count total services for this vendor
                cursor.execute("SELECT COUNT(*) as cnt FROM vendor WHERE email=%s", (email,))
                cnt_row = cursor.fetchone()
                total_cnt = cnt_row['cnt'] if cnt_row else 1
                if total_cnt <= 1:
                    flash("You must keep at least one registered service category. Cannot remove your only remaining service profile. / आप कम से कम एक सेवा श्रेणी नहीं हटा सकते।", "warning")
                    return redirect(url_for('vendor_dashboard'))

                # Delete specified service category
                cursor.execute("DELETE FROM vendor WHERE email=%s AND service=%s", (email, service_name))
                conn.commit()

                # Remove from GLOBAL_REGISTERED_VENDORS
                GLOBAL_REGISTERED_VENDORS = [v for v in GLOBAL_REGISTERED_VENDORS if not (v.get('email') == email and v.get('service') == service_name)]

                # Switch session service if active service was deleted
                cursor.execute("SELECT service, id, name FROM vendor WHERE email=%s LIMIT 1", (email,))
                remaining = cursor.fetchone()
                if remaining:
                    session['vendor_service'] = remaining['service']
                    session['vendor_id'] = remaining['id']
                    session['vendor_name'] = remaining['name']

                flash(f"Service category '{service_name.upper()}' removed successfully! It will no longer appear in customer bookings. / सेवा श्रेणी '{service_name.upper()}' सफलतापूर्वक हटा दी गई है!", "success")
        except Exception as e:
            flash(f"Error removing service: {e}", "danger")
        finally:
            conn.close()
    else:
        # Simulation mode fallback
        session_vendors = list(session.get('mock_vendors', []))
        all_user_vendors = [v for v in (session_vendors + GLOBAL_REGISTERED_VENDORS) if v.get('email') == email]
        
        if len(all_user_vendors) <= 1:
            flash("You must keep at least one registered service category. Cannot remove your only remaining service profile. / आप कम से कम एक सेवा श्रेणी नहीं हटा सकते।", "warning")
            return redirect(url_for('vendor_dashboard'))

        # Remove from session mock vendors and GLOBAL_REGISTERED_VENDORS
        session_vendors = [v for v in session_vendors if not (v.get('email') == email and v.get('service') == service_name)]
        GLOBAL_REGISTERED_VENDORS = [v for v in GLOBAL_REGISTERED_VENDORS if not (v.get('email') == email and v.get('service') == service_name)]

        session['mock_vendors'] = session_vendors
        session.modified = True

        remaining_v = next((v for v in (session_vendors + GLOBAL_REGISTERED_VENDORS) if v.get('email') == email), None)
        if remaining_v:
            session['vendor_service'] = remaining_v.get('service')
            session['vendor_id'] = remaining_v.get('id')
            session['vendor_name'] = remaining_v.get('name')

        flash(f"Service category '{service_name.upper()}' removed successfully! It will no longer appear in customer bookings. / सेवा श्रेणी '{service_name.upper()}' सफलतापूर्वक हटा दी गई है!", "success")

    return redirect(url_for('vendor_dashboard'))

def is_email_or_phone_registered(email, phone, conn=None):
    if not email and not phone:
        return False

    clean_email = (email or '').strip().lower()
    clean_phone = (phone or '').strip()

    # 1. Check DB if connection provided or available
    close_db = False
    if conn is None:
        conn = get_db_connection()
        close_db = True

    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE LOWER(email)=%s OR phone=%s LIMIT 1", (clean_email, clean_phone))
                if cursor.fetchone():
                    if close_db: conn.close()
                    return True
                cursor.execute("SELECT id FROM vendor WHERE LOWER(email)=%s OR phone=%s LIMIT 1", (clean_email, clean_phone))
                if cursor.fetchone():
                    if close_db: conn.close()
                    return True
        except Exception as e:
            print(f"Error checking DB duplicate registration: {e}")
        finally:
            if close_db:
                conn.close()

    # 2. Check GLOBAL_REGISTERED_VENDORS
    for v in GLOBAL_REGISTERED_VENDORS:
        v_email = (v.get('email') or '').strip().lower()
        v_phone = (v.get('phone') or '').strip()
        if (clean_email and v_email == clean_email) or (clean_phone and v_phone == clean_phone):
            return True

    # 3. Check session mock_vendors and mock_users
    try:
        mock_v = session.get('mock_vendors', [])
        for v in mock_v:
            v_email = (v.get('email') or '').strip().lower()
            v_phone = (v.get('phone') or '').strip()
            if (clean_email and v_email == clean_email) or (clean_phone and v_phone == clean_phone):
                return True

        mock_u = session.get('mock_users', [])
        for u in mock_u:
            u_email = (u.get('email') or '').strip().lower()
            u_phone = (u.get('phone') or '').strip()
            if (clean_email and u_email == clean_email) or (clean_phone and u_phone == clean_phone):
                return True
    except Exception:
        pass

    # 4. Check known hardcoded seed accounts
    seed_emails = {'user@shubhlo.com', 'owner@shubhlo.com', 'royal@shubhlo.com', 'meadow@shubhlo.com', 'shahi@shubhlo.com', 'djrock@shubhlo.com', 'n9599@gmail.com'}
    seed_phones = {'9876543210', '9876543211', '9876543212', '9876543213', '9876543214', '9599000000'}
    if clean_email in seed_emails or clean_phone in seed_phones:
        return True

    return False

@app.route('/admin/customer/delete/<int:user_id>', methods=['POST'])
@app.route('/owner/customer/delete/<int:user_id>', methods=['POST'])
@app.route('/admin/customer/delete', methods=['POST'], defaults={'user_id': 1})
def admin_delete_customer(user_id=1):
    if not (session.get('admin') or session.get('is_owner')):
        flash("Unauthorized access. Owner permission required. / केवल ऑनर्स को अधिकार प्राप्त है।", "danger")
        return redirect(url_for('login'))

    target_email = None
    target_phone = None

    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT email, phone FROM users WHERE id=%s", (user_id,))
                u_row = cursor.fetchone()
                if u_row:
                    target_email = u_row.get('email')
                    target_phone = u_row.get('phone')
                cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
                conn.commit()
                flash(f"Customer Account #{user_id} PERMANENTLY DELETED from database by Owner! / ग्राहक खाता #{user_id} पूरी तरह डिलीट कर दिया गया है!", "success")
        except Exception as e:
            flash(f"Error deleting customer: {e}", "danger")
        finally:
            conn.close()

    # Fallback target lookup from memory pools if DB is offline
    if not target_email:
        all_u_pool = GLOBAL_REGISTERED_USERS + session.get('mock_users', [])
        target_u = next((u for u in all_u_pool if str(u.get('id')) == str(user_id)), None)
        if target_u:
            target_email = target_u.get('email')
            target_phone = target_u.get('phone')

    GLOBAL_REGISTERED_USERS[:] = [
        u for u in GLOBAL_REGISTERED_USERS
        if not (str(u.get('id')) == str(user_id) or (target_email and u.get('email') == target_email) or (target_phone and u.get('phone') == target_phone))
    ]

    mock_users = session.get('mock_users', [])
    if mock_users:
        session['mock_users'] = [
            u for u in mock_users
            if not (str(u.get('id')) == str(user_id) or (target_email and u.get('email') == target_email) or (target_phone and u.get('phone') == target_phone))
        ]
        session.modified = True

    flash(f"Customer Account #{user_id} PERMANENTLY DELETED by Owner! / ग्राहक खाता पूरी तरह डिलीट किया गया!", "success")
    return redirect(request.referrer or url_for('owner_dashboard'))

# -------------------------------------------------------------
# AUTOMATIC .HTML ROUTE REDIRECT & BRANDED 404 HANDLER
# -------------------------------------------------------------
@app.route('/<page_name>.html', methods=['GET', 'POST'])
def handle_html_extension_redirect(page_name):
    page_map = {
        'index': 'home',
        'home': 'home',
        'about': 'about',
        'contact': 'contact',
        'cantact': 'contact',
        'services': 'services',
        'servies': 'services',
        'booking': 'booking1',
        'booking1': 'booking1',
        'boking1': 'booking1',
        'booking2': 'booking2',
        'boking2': 'booking2',
        'confirm_booking': 'confirm_booking',
        'confirm-booking': 'confirm_booking',
        'pay': 'pay',
        'login': 'login',
        'signup': 'signup',
        'register': 'signup',
        'dashboard': 'dashboard',
        'vendor_dashboard': 'vendor_dashboard',
        'vendor-dashboard': 'vendor_dashboard',
        'vendor_login': 'vendor_login',
        'vendor-login': 'vendor_login',
        'vendor_register': 'vendor_register',
        'vendor-register': 'vendor_register',
        'admin_dashboard': 'admin_dashboard',
        'owner_dashboard': 'owner_dashboard',
        'terms': 'terms',
        'privacy': 'privacy',
        'rating': 'rating',
        'forgot_password': 'forget_password',
        'forgot-password': 'forget_password',
        'forgetpws': 'forget_password',
        'reset_password': 'reset_password',
        'youtube': 'youtube',
        'ad_video': 'ad_video',
        'advertisement': 'advertisement',
    }
    target_endpoint = page_map.get(str(page_name).lower())
    if target_endpoint and target_endpoint in app.view_functions:
        return redirect(url_for(target_endpoint), code=301)
    return redirect(url_for('home'), code=302)

def handle_url_build_error(error, endpoint, values):
    if endpoint in ['booking1', 'booking']:
        return '/booking1'
    if endpoint in ['vendor_login', 'vendor_login_alias', 'vendor-login']:
        return '/vendor_login'
    if endpoint in ['vendor_register', 'vendor_register_alias', 'vendor-registration']:
        return '/vendor_register'
    if endpoint in ['vendor_dashboard', 'vendor_dashboard_alias']:
        return '/vendor_dashboard'
    if endpoint in ['forget_password', 'forgot_password', 'forget_password_alias']:
        return '/forget-password'
    if endpoint in ['signup', 'register', 'signup_alias']:
        return '/signup'
    if endpoint in ['login']:
        return '/login'
    if endpoint in ['home']:
        return '/home'
    if endpoint in ['services', 'servies']:
        return '/services'
    if endpoint in ['about']:
        return '/about'
    if endpoint in ['contact', 'cantact']:
        return '/contact'
    if endpoint in ['terms']:
        return '/terms'
    if endpoint in ['privacy']:
        return '/privacy'
    if endpoint in ['admin_dashboard']:
        return '/admin/dashboard'
    if endpoint in ['dashboard']:
        return '/dashboard'
    if endpoint in ['logout']:
        return '/logout'
    if endpoint in ['download_invoice', 'booking_invoice']:
        b_id = values.get('booking_id', 1) if values else 1
        return f"/booking/invoice/{b_id}"
    if endpoint == 'vendor_remove_service':
        svc = values.get('service_name', '') if values else ''
        return f"/vendor/remove_service/{svc}" if svc else "/vendor/remove_service"
    return None

app.url_build_error_handlers.append(handle_url_build_error)

@app.errorhandler(404)
def page_not_found(e):
    path = request.path.lower().rstrip('/')
    if path.endswith('.html'):
        clean_page = path.rsplit('/', 1)[-1].replace('.html', '')
        return handle_html_extension_redirect(clean_page)

    flash("The requested page was not found. Redirected to Shubhlo Home! / मांगी गई URL नहीं मिली, होमपेज पर रिडायरेक्ट किया गया।", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    migrate_db_schema()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)
