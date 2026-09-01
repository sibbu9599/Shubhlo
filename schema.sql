-- ============================================================
-- SHUBHLO EVENT PLATFORM (शुभलो) - PRODUCTION MYSQL DATABASE SCHEMA
-- Database Name: shubhlo_db
-- Encoding: UTF8MB4
-- ============================================================

CREATE DATABASE IF NOT EXISTS shubhlo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shubhlo_db;

-- ------------------------------------------------------------
-- 1. USERS TABLE (ग्राहक खाता तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 2. VENDOR TABLE (वेंडर खाता व सेवा तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vendor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    service VARCHAR(100) NOT NULL,
    description TEXT,
    photo VARCHAR(255),
    id_proof VARCHAR(255),
    govt_id_number VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) DEFAULT 0.00,
    min_order_value DECIMAL(10, 2) DEFAULT 0.00,
    state VARCHAR(100) DEFAULT 'Madhya Pradesh',
    district VARCHAR(100) DEFAULT 'Hoshangabad',
    tehsil VARCHAR(100) DEFAULT 'Itarsi',
    approval_status VARCHAR(20) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_vendor_service (service),
    INDEX idx_vendor_tehsil (tehsil),
    INDEX idx_vendor_approval (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 3. BOOKING TABLE (ग्राहक बुकिंग व टोकन हिसाब तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    state VARCHAR(100) DEFAULT 'Madhya Pradesh',
    district VARCHAR(100) DEFAULT 'Hoshangabad',
    tehsil VARCHAR(100) DEFAULT 'Itarsi',
    event_date DATE NOT NULL,
    amount DECIMAL(10, 2) DEFAULT 0.00,
    token_deposit DECIMAL(10, 2) DEFAULT 5000.00,
    advance_paid DECIMAL(10, 2) DEFAULT 5118.00,
    customer_platform_fee DECIMAL(10, 2) DEFAULT 100.00,
    gst_amount DECIMAL(10, 2) DEFAULT 18.00,
    vendor_fee DECIMAL(10, 2) DEFAULT 500.00,
    vendor_payout DECIMAL(10, 2) DEFAULT 4500.00,
    payment_status VARCHAR(20) DEFAULT 'Paid',
    payment_method VARCHAR(50) DEFAULT 'UPI',
    transaction_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending Owner Approval',
    booking_status VARCHAR(50) DEFAULT 'Pending',
    otp VARCHAR(10) DEFAULT '784920',
    target_budget DECIMAL(10, 2) DEFAULT NULL,
    budget_flexible VARCHAR(20) DEFAULT 'Negotiable',
    counter_offer_amount DECIMAL(10, 2) DEFAULT NULL,
    counter_note TEXT DEFAULT NULL,
    counter_offer_status VARCHAR(20) DEFAULT 'Pending',
    venue VARCHAR(150),
    catering VARCHAR(150),
    dj VARCHAR(150),
    decoration VARCHAR(150),
    transport VARCHAR(150),
    photography VARCHAR(150),
    shahi_sawari VARCHAR(150),
    invitation_card VARCHAR(150),
    security_guard VARCHAR(150),
    makeup VARCHAR(150),
    mehendi VARCHAR(150),
    dhol_band VARCHAR(150),
    choreographer VARCHAR(150),
    anchor VARCHAR(150),
    fireworks VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_booking_email (email),
    INDEX idx_booking_event_date (event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 4. PERMITTED LOCATIONS TABLE (ऑनर्स अनुमति स्थान तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permitted_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    tehsil VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 5. VENDOR AVAILABILITY TABLE (वेंडर ब्लॉक तारीख तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vendor_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT NOT NULL,
    event_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Blocked',
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor(id) ON DELETE CASCADE,
    INDEX idx_availability_date (event_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 6. BOOKING VERIFICATION TABLE (सर्विस वेरिफिकेशन तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS booking_verification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    vendor_name VARCHAR(150) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES booking(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 7. VENDOR RATINGS TABLE (वेंडर रेटिंग तालिका)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vendor_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendor(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- 8. SYSTEM SETTINGS TABLE (सिस्टम कंट्रोल सेटिंग्स)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(50) DEFAULT 'ON',
    custom_message TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Initial System Settings Seed
INSERT IGNORE INTO system_settings (setting_key, setting_value, custom_message) VALUES
('allow_customer_booking', 'ON', 'Customer bookings are temporarily paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा ग्राहक बुकिंग फ़िलहाल बंद है।'),
('allow_vendor_registration', 'ON', 'New vendor registrations are currently paused by Shubhlo Admin. Please check back soon! / एडमिन द्वारा नया वेंडर रजिस्ट्रेशन फ़िलहाल बंद है।');

-- Initial Permitted Locations Seed
INSERT IGNORE INTO permitted_locations (id, state, district, tehsil) VALUES
(1, 'Madhya Pradesh', 'Hoshangabad', 'Itarsi'),
(2, 'Madhya Pradesh', 'Hoshangabad', 'Sohagpur'),
(3, 'Madhya Pradesh', 'Hoshangabad', 'Pipariya'),
(4, 'Madhya Pradesh', 'Hoshangabad', 'Narmadapuram'),
(5, 'Madhya Pradesh', 'Indore', 'Indore'),
(6, 'Madhya Pradesh', 'Bhopal', 'Bhopal');

-- ============================================================
-- SCHEMA SETUP COMPLETED SUCCESSFULLY
-- ============================================================
