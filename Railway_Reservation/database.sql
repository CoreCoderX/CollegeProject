-- Create the database
CREATE DATABASE IF NOT EXISTS railway_system;
USE railway_system;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    is_admin BOOLEAN DEFAULT FALSE,
    profile_pic VARCHAR(255),
    theme VARCHAR(10) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trains table
CREATE TABLE IF NOT EXISTS trains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(20) UNIQUE NOT NULL,
    train_name VARCHAR(100) NOT NULL,
    total_seats_sleeper INT NOT NULL,
    total_seats_ac INT NOT NULL,
    total_seats_general INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schedules table
CREATE TABLE IF NOT EXISTS schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    train_id INT NOT NULL,
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_time TIME NOT NULL,
    fare_sleeper DECIMAL(10, 2) NOT NULL,
    fare_ac DECIMAL(10, 2) NOT NULL,
    fare_general DECIMAL(10, 2) NOT NULL,
    status ENUM('on-time', 'delayed', 'cancelled') DEFAULT 'on-time',
    delay_minutes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    schedule_id INT NOT NULL,
    pnr VARCHAR(10) UNIQUE NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_fare DECIMAL(10, 2) NOT NULL,
    status ENUM('confirmed', 'cancelled') DEFAULT 'confirmed',
    payment_method ENUM('credit_card', 'debit_card', 'net_banking', 'upi') NOT NULL,
    payment_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
);

-- Passengers table
CREATE TABLE IF NOT EXISTS passengers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('male', 'female', 'other') NOT NULL,
    seat_class ENUM('sleeper', 'ac', 'general') NOT NULL,
    seat_number VARCHAR(10),
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

