-- Shubhlo (शुभलो) Master Database Schema
-- Database Name: shubhlo_db
-- Import this SQL script into phpMyAdmin or MySQL Server

CREATE DATABASE IF NOT EXISTS `shubhlo_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `shubhlo_db`;

-- 1. Users Table (Customer Accounts)
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `phone` VARCHAR(15) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Vendor Table (Service Providers & Anti-Fraud Verification Data)
CREATE TABLE IF NOT EXISTS `vendor` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) NOT NULL,
  `service` VARCHAR(50) NOT NULL,
  `description` TEXT,
  `photo` VARCHAR(255),
  `password` VARCHAR(255) NOT NULL,
  `price` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  `min_order_value` DECIMAL(10, 2) DEFAULT 0.00,
  `address` TEXT,
  `state` VARCHAR(100) DEFAULT 'Madhya Pradesh',
  `district` VARCHAR(100) DEFAULT 'Hoshangabad',
  `tehsil` VARCHAR(100) DEFAULT 'Itarsi',
  `govt_id_number` VARCHAR(50) DEFAULT NULL,
  `govt_id_proof` VARCHAR(255) DEFAULT NULL,
  `approval_status` VARCHAR(20) DEFAULT 'Pending',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Booking Table (Customer Event Bookings)
CREATE TABLE IF NOT EXISTS `booking` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) NOT NULL,
  `address` TEXT,
  `state` VARCHAR(100) DEFAULT 'Madhya Pradesh',
  `district` VARCHAR(100) DEFAULT 'Hoshangabad',
  `tehsil` VARCHAR(100) DEFAULT 'Itarsi',
  `event_date` DATE NOT NULL,
  `venue` VARCHAR(100) DEFAULT NULL,
  `catering` VARCHAR(100) DEFAULT NULL,
  `dj` VARCHAR(100) DEFAULT NULL,
  `photography` VARCHAR(100) DEFAULT NULL,
  `makeup` VARCHAR(100) DEFAULT NULL,
  `transport` VARCHAR(100) DEFAULT NULL,
  `decoration` VARCHAR(100) DEFAULT NULL,
  `birthday` VARCHAR(100) DEFAULT NULL,
  `security_guard` VARCHAR(100) DEFAULT NULL,
  `shahi_savari` VARCHAR(100) DEFAULT NULL,
  `invitation_card` VARCHAR(100) DEFAULT NULL,
  `amount` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  `advance_paid` DECIMAL(10, 2) DEFAULT 0.00,
  `target_budget` DECIMAL(10, 2) DEFAULT NULL,
  `budget_flexible` VARCHAR(20) DEFAULT 'Negotiable',
  `counter_offer_amount` DECIMAL(10, 2) DEFAULT NULL,
  `counter_offer_vendor` VARCHAR(100) DEFAULT NULL,
  `counter_offer_status` VARCHAR(20) DEFAULT NULL,
  `payment_status` VARCHAR(20) DEFAULT 'Pending',
  `payment_method` VARCHAR(50) DEFAULT 'Online UPI/Card',
  `dispute_status` VARCHAR(50) DEFAULT NULL,
  `dispute_reason` TEXT DEFAULT NULL,
  `refund_amount` DECIMAL(10, 2) DEFAULT 0.00,
  `refund_status` VARCHAR(50) DEFAULT NULL,
  `refund_method` VARCHAR(50) DEFAULT 'Original Payment Method / UPI',
  `refund_notes` TEXT DEFAULT NULL,
  `refunded_at` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Booking Verification Table (Vendor Contact Locking/Unlocking)
CREATE TABLE IF NOT EXISTS `booking_verification` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `booking_id` INT NOT NULL,
  `vendor_name` VARCHAR(100) NOT NULL,
  `service_type` VARCHAR(50) NOT NULL,
  `status` VARCHAR(20) DEFAULT 'Pending',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`booking_id`) REFERENCES `booking`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Vendor Date Availability Table
CREATE TABLE IF NOT EXISTS `vendor_availability` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `vendor_name` VARCHAR(100) NOT NULL,
  `event_date` DATE NOT NULL,
  `status` VARCHAR(20) DEFAULT 'Booked',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Vendor Rating & Reviews Table
CREATE TABLE IF NOT EXISTS `rating` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `vendor_name` VARCHAR(100) NOT NULL,
  `stars` INT NOT NULL DEFAULT 5,
  `review_text` TEXT,
  `customer_name` VARCHAR(100) DEFAULT 'Anonymous Host',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Permitted Locations Table (Master Location Control)
CREATE TABLE IF NOT EXISTS `permitted_locations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `state` VARCHAR(100) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `tehsil` VARCHAR(100) NOT NULL,
  `is_active` TINYINT(1) DEFAULT 1,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_loc` (`state`, `district`, `tehsil`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `allowed_locations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `state` VARCHAR(100) NOT NULL,
  `district` VARCHAR(100) NOT NULL,
  `tehsil` VARCHAR(100) NOT NULL,
  `is_active` TINYINT(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert Default Permitted Locations
INSERT IGNORE INTO `permitted_locations` (`state`, `district`, `tehsil`, `is_active`) VALUES
('Madhya Pradesh', 'Hoshangabad', 'Itarsi', 1),
('Madhya Pradesh', 'Hoshangabad', 'Sohagpur', 1),
('Madhya Pradesh', 'Hoshangabad', 'Pipariya', 1),
('Madhya Pradesh', 'Hoshangabad', 'Hoshangabad', 1),
('Madhya Pradesh', 'Bhopal', 'Berasia', 1),
('Madhya Pradesh', 'Bhopal', 'Kolar', 1),
('Madhya Pradesh', 'Indore', 'Indore', 1);

-- 8. System Settings Table (Master Controls)
CREATE TABLE IF NOT EXISTS `system_settings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `setting_key` VARCHAR(100) NOT NULL UNIQUE,
  `setting_value` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `system_settings` (`setting_key`, `setting_value`) VALUES
('customer_bookings_enabled', 'true'),
('vendor_registrations_enabled', 'true')
ON DUPLICATE KEY UPDATE `setting_value` = VALUES(`setting_value`);

-- 9. Contact Messages Table
CREATE TABLE IF NOT EXISTS `contact_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `message_type` VARCHAR(50) DEFAULT 'Enquiry',
  `message` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Sent SMS Log Table
CREATE TABLE IF NOT EXISTS `sent_sms` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `phone` VARCHAR(15) NOT NULL,
  `recipient_type` VARCHAR(50) NOT NULL,
  `message` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Blacklisted Users Table
CREATE TABLE IF NOT EXISTS `blacklisted_users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(100) DEFAULT NULL,
  `phone` VARCHAR(15) DEFAULT NULL,
  `reason` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
