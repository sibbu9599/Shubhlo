# 👑 Shubhlo (शुभलो) - Event Management & Vendor Booking Platform
### 🏢 A Flagship Product of Apna Infotech Pvt. Ltd.

**Shubhlo** is a comprehensive, full-stack event management and vendor booking platform owned, managed, and operated by **Apna Infotech Pvt. Ltd.** Built using **Python (Flask)**, **Jinja2**, **HTML5/CSS3**, and **MySQL**, it enables customers to discover verified vendors across **18 complete event service categories**, customize packages according to target budgets, manage event date availability, send custom counter-offers, rate completed bookings, and download official tax receipts.

---

## 📍 File Location
The project's README file is located at:
`c:\Users\Shailendra Singh\OneDrive\Desktop\celebrato project\README.md`

---

## ✨ Complete Feature Matrix

- **18 Complete Event Service Categories**:
  1. 🏢 **VENUE / मैरिज गार्डन** (`venue`)
  2. 🍽️ **CATERING / कैटरिंग** (`catering`)
  3. 🎵 **DJ & MUSICS / डीजे साउंड** (`dj`)
  4. 📸 **PHOTOGRAPHY / फोटो व वीडियो** (`photography`)
  5. 💄 **MAKEUP & BEAUTY / ब्यूटी मेकअप** (`makeup`)
  6. 🚗 **TRANSPORT / लग्जरी गाड़ियां** (`transport`)
  7. 🎈 **DECORATION / फ्लावर सजावट** (`decoration`)
  8. 🎂 **BIRTHDAY PARTY / बर्थडे सेलिब्रेशन** (`birthday`)
  9. 🛡️ **SECURITY GUARDS / सुरक्षा बाउंसर्स** (`security_guard`)
  10. 👑 **SHAHI SAVARI / शाही बग्घी** (`shahi_savari`)
  11. 💌 **INVITATION CARDS / निमंत्रण कार्ड** (`invitation_card`)
  12. ⛺ **TENT & LIGHTING / टेंट व लाइटिंग** (`tent_lighting`)
  13. 🎺 **BAND & DHOL / बैंड बाजा व ढोल** (`band_dhol`)
  14. 🎆 **FIREWORKS & PYRO / आतिशबाजी व पायरो** (`fireworks`)
  15. 🎤 **ANCHOR & CHOREOGRAPHER / एंकर व डांस** (`anchor_choreographer`)
  16. 🌿 **MEHENDI ARTIST / मेहंदी आर्टिस्ट** (`mehendi`)
  17. 👳 **SAFA & TURBAN / साफा व दूल्हा पगड़ी** (`safa_turban`)
  18. 🌼 **HALDI SETUP / हल्दी व मेहंदी डेकोर** (`haldi_setup`)

- **Multi-Step Event Booking Flow**:
  - **Step 1 (`/booking1`)**: Capture event details, type, date, location (State, District, Tehsil), and target budget.
  - **Step 2 (`/booking2`)**: Interactive vendor catalog with location-based filtering, real-time date availability badges, minimum order limit validation, and dynamic budget calculations.
  - **Confirmation (`/confirm_booking`)**: Summary of selected services, token deposit breakdown, and booking confirmation.
- **Vendor Anti-Fake Verification & Registration (`/vendor_register`)**:
  - Strict verification checks (GSTIN Number, PAN/Aadhar Upload, Business License, Photo Upload) to filter out fake vendors.
  - Service selection pills for all 18 categories.
- **Customer Dashboard (`/dashboard`)**:
  - View active bookings, payment statuses, and counter-offers sent by vendors.
  - Rate completed vendor services (`/rating`).
  - Cancel bookings with auto-refund policy.
  - View & download GST Tax Invoices (`/booking/invoice/<id>`).
- **Vendor Dashboard (`/vendor/dashboard`)**:
  - Manage service categories and starting prices.
  - Update Minimum Order values.
  - Toggle Date Availability (block/unblock specific dates).
  - Review incoming customer bookings and send custom **Counter Offers**.
- **Master Admin Dashboard (`/admin/dashboard`)**:
  - Master System Controls (pause customer bookings for maintenance).
  - Verify and approve vendor accounts and customer bookings.
  - Location management (add/remove allowed states, districts, and tehsils).
  - Blacklist management and SMS notification log tracking.

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.9+
- **Dependencies**: `pip install flask pymysql werkzeug`

### Running the Application

1. **Launch Server**:
   ```bash
   python app.py
   ```
2. **Access in Browser**:
   - **Main Web Application**: [http://127.0.0.1:8080](http://127.0.0.1:8080)
   - **Vendor Registration**: [http://127.0.0.1:8080/vendor_register](http://127.0.0.1:8080/vendor_register)
   - **Book Event Services**: [http://127.0.0.1:8080/booking1](http://127.0.0.1:8080/booking1)
   - **Services Catalog**: [http://127.0.0.1:8080/services](http://127.0.0.1:8080/services)

---

## 🧪 Running Integration Tests

Run the complete 11-test automated suite to verify all routes, booking flows, counter-offers, date availability, and admin controls:

```bash
python test_suite.py
```

---

## 📁 Directory Structure

```text
celebrato project/
├── app.py                  # Main Flask Server & Route Controllers
├── test_suite.py           # Automated Test Suite (11 Integration Tests)
├── verify_and_fix_routes.py# Route Decorator Integrity Verifier
├── README.md               # Project Documentation
├── static/                 # Stylesheets, Scripts, and Brand Assets
│   ├── master.css
│   ├── services.css
│   ├── dashboard.css
│   └── booking2.css
└── templates/              # HTML Templates (Jinja2)
    ├── home.html
    ├── booking1.html
    ├── booking2.html
    ├── confirm_booking.html
    ├── dashboard.html
    ├── vendor_dashboard.html
    ├── vendor_register.html
    ├── admin_dashboard.html
    ├── services.html
    └── ...
```

---

## 🔒 Corporate Branding & License

- **Parent Company**: Apna Infotech Pvt. Ltd. (Flagship Venture: Shubhlo)
- **Brand Name**: Shubhlo (शुभलो) - Event Management & Vendor Booking Platform
- **Copyright**: © 2026 Shubhlo - A Venture of Apna Infotech Pvt. Ltd. All rights reserved.
