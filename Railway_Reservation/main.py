import math
import os
import re
import bcrypt
import mysql.connector
from dotenv import load_dotenv
import customtkinter as ctk
from customtkinter import CTkEntry
from datetime import datetime, timedelta
import random
import string
import tkinter as tk
from tkinter import ttk, messagebox, StringVar, IntVar
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import platform
from CTkMessagebox import CTkMessagebox

# Load environment variables
load_dotenv()

# Theme and style settings
THEME_COLORS = {
    "dark": {
        "primary": "#1e88e5",
        "secondary": "#303f9f",
        "accent": "#ff6f00",
        "success": "#43a047",
        "danger": "#e53935",
        "warning": "#ffb300",
        "text": "#ffffff",
        "bg_primary": "#121212",
        "bg_secondary": "#1e1e1e",
        "card": "#2d2d2d"
    },
    "light": {
        "primary": "#1976d2",
        "secondary": "#303f9f",
        "accent": "#ff6f00",
        "success": "#43a047",
        "danger": "#e53935",
        "warning": "#ffb300",
        "text": "#212121",
        "bg_primary": "#f5f5f5",
        "bg_secondary": "#e0e0e0",
        "card": "#ffffff"
    }
}

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", "3306"))
        )
        return connection
    except mysql.connector.Error as err:
        CTkMessagebox(title="Database Connection Error", 
                     message=f"Failed to connect to database: {err}",
                     icon="cancel")
        return None

# Initialize database and tables
def initialize_database():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trains (
                id INT AUTO_INCREMENT PRIMARY KEY,
                train_number VARCHAR(20) UNIQUE NOT NULL,
                train_name VARCHAR(100) NOT NULL,
                total_seats_sleeper INT NOT NULL,
                total_seats_ac INT NOT NULL,
                total_seats_general INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passengers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                gender ENUM('male', 'female', 'other') NOT NULL,
                seat_class ENUM('sleeper', 'ac', 'general') NOT NULL,
                seat_number VARCHAR(10),
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Insert sample admin and users if they don't exist
        sample_users = [
            ("Admin User", "sivaprakash7223@gmail.com", "siva@2006", True),
            ("Rohith", "rohith7223@gmail.com", "rohith@2006", False),
            ("Kamal", "kamal7223@gmail.com", "kamal@2006", False),
            ("Nithish", "nithish7223@gmail.com", "nithish@2006", False),
            ("Rajasekar", "rajasekar7223@gmail.com", "rjk@2006", False)
        ]
        
        for name, email, password, is_admin in sample_users:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if not cursor.fetchone():
                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "INSERT INTO users (name, email, password, is_admin) VALUES (%s, %s, %s, %s)",
                    (name, email, hashed_password, is_admin)
                )
        
        # Insert sample trains if they don't exist
        sample_trains = [
            ("12345", "Rajdhani Express", 500, 300, 700),
            ("12346", "Shatabdi Express", 450, 350, 600),
            ("12347", "Duronto Express", 550, 250, 800)
        ]
        
        for train_number, train_name, sleeper, ac, general in sample_trains:
            cursor.execute("SELECT id FROM trains WHERE train_number = %s", (train_number,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO trains (train_number, train_name, total_seats_sleeper, total_seats_ac, total_seats_general) VALUES (%s, %s, %s, %s, %s)",
                    (train_number, train_name, sleeper, ac, general)
                )
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    return False

# Helper functions
def generate_pnr():
    """Generate a random 10-character PNR number"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def format_currency(amount):
    """Format amount as currency"""
    return f"₹{amount:,.2f}"

def get_user_theme(user_id):
    """Get the theme preference for a user"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT theme FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            return result['theme'] if result else 'light'
        except Exception as e:
            print(f"Error getting user theme: {e}")
            return 'light'
        finally:
            cursor.close()
            connection.close()
    return 'light'

def set_user_theme(user_id, theme):
    """Set the theme preference for a user"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE users SET theme = %s WHERE id = %s", (theme, user_id))
            connection.commit()
        except Exception as e:
            print(f"Error setting user theme: {e}")
        finally:
            cursor.close()
            connection.close()

def load_image(path, size=(20, 20)):
    """Load an image and resize it"""
    try:
        return ctk.CTkImage(light_image=Image.open(path),
                           dark_image=Image.open(path),
                           size=size)
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        return None

# Create assets directory if it doesn't exist
os.makedirs("assets", exist_ok=True)

# Main Application
class RailwayReservationSystem:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Railways | Modern Railway Reservation System")
        self.app.geometry("1200x700")
        self.app.minsize(900, 600)
        self.app.resizable(True, True)
        
        # Try to set icon if file exists
        try:
            if platform.system() == "Windows":
                self.app.iconbitmap("assets/train_icon.ico")
            else:
                logo_img = Image.open("assets/train_icon.png")
                logo_photo = ImageTk.PhotoImage(logo_img)
                self.app.wm_iconphoto(True, logo_photo)
        except:
            pass
        
        # Set appearance mode and color theme
        self.current_theme = "light"
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Current user data
        self.current_user = None
        
        # Initialize database
        if not initialize_database():
            self.app.destroy()
            return
        
        # Show splashscreen
        self.show_splash_screen()
        
    def show_splash_screen(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        splash_frame = ctk.CTkFrame(self.app, corner_radius=0)
        splash_frame.pack(fill="both", expand=True)
        
        # Center frame
        center_frame = ctk.CTkFrame(splash_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((200, 200), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(center_frame, image=logo_photo, text="")
            logo_label.image = logo_photo
            logo_label.pack(pady=20)
        except:
            # If logo image is not available
            logo_label = ctk.CTkLabel(center_frame, text="🚄", font=ctk.CTkFont(size=80))
            logo_label.pack(pady=20)
        
        # App name
        title_label = ctk.CTkLabel(
            center_frame, 
            text="Railways", 
            font=ctk.CTkFont(size=40, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Tagline
        tagline_label = ctk.CTkLabel(
            center_frame, 
            text="Modern Railway Reservation System", 
            font=ctk.CTkFont(size=16)
        )
        tagline_label.pack(pady=(0, 40))
        
        # Progress bar
        progress = ctk.CTkProgressBar(center_frame, width=300)
        progress.pack(pady=10)
        progress.set(0)
        
        # Status label
        status_label = ctk.CTkLabel(center_frame, text="Loading...")
        status_label.pack(pady=10)
        
        # Schedule tasks
        self.schedule_progress_tasks(progress, status_label)
    
    def schedule_progress_tasks(self, progress_bar, status_label, step=0):
        steps = [
            ("Connecting to database...", 0.2),
            ("Loading resources...", 0.4),
            ("Initializing application...", 0.6),
            ("Preparing user interface...", 0.8),
            ("Ready!", 1.0)
        ]
        
        if step < len(steps):
            status, value = steps[step]
            status_label.configure(text=status)
            progress_bar.set(value)
            self.app.after(800, lambda: self.schedule_progress_tasks(progress_bar, status_label, step+1))
        else:
            # Once loading is complete, show the login screen
            self.app.after(500, self.show_login_screen)
    
    def show_login_screen(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create login container
        main_container = ctk.CTkFrame(self.app, corner_radius=0)
        main_container.pack(fill="both", expand=True)
        
        # Split into two parts: Left (image) and Right (login form)
        left_panel = ctk.CTkFrame(main_container, corner_radius=0)
        left_panel.pack(side="left", fill="both", expand=True)
        
        right_panel = ctk.CTkFrame(main_container, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Left panel - Image and quotes
        try:
            bg_img = Image.open("assets/train_background.jpg")
            bg_photo = ImageTk.PhotoImage(bg_img)
            
            bg_label = ctk.CTkLabel(left_panel, image=bg_photo, text="")
            bg_label.image = bg_photo  # Keep a reference
            bg_label.pack(fill="both", expand=True)
            
            # Overlay text
            overlay = ctk.CTkFrame(left_panel, fg_color=("rgba(0, 0, 0, 0.6)", "rgba(0, 0, 0, 0.6)"))
            overlay.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.3)
            
            quote = ctk.CTkLabel(
                overlay,
                text="The journey of a thousand miles begins with a single step.",
                font=ctk.CTkFont(size=18, weight="bold"),
                wraplength=400,
                text_color="white"
            )
            quote.pack(pady=(20, 10), padx=20)
            
            author = ctk.CTkLabel(
                overlay,
                text="— Lao Tzu",
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            author.pack(pady=(0, 20), padx=20)
        except:
            # Fallback if image is not available
            title_label = ctk.CTkLabel(
                left_panel, 
                text="Railway Reservation System", 
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(100, 20))
            
            subtitle_label = ctk.CTkLabel(
                left_panel, 
                text="Book your journey with ease and comfort",
                font=ctk.CTkFont(size=16)
            )
            subtitle_label.pack()
        
        # Right panel - Login form
        login_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        login_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8)
        
        # Title
        welcome_label = ctk.CTkLabel(
            login_container, 
            text="Welcome Back!", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        welcome_label.pack(pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            login_container, 
            text="Sign in to continue", 
            font=ctk.CTkFont(size=16)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Email
        email_frame = ctk.CTkFrame(login_container, fg_color="transparent")
        email_frame.pack(fill="x", pady=10)
        
        email_label = ctk.CTkLabel(email_frame, text="Email")
        email_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        email_entry = ctk.CTkEntry(
            email_frame, 
            width=300, 
            placeholder_text="Enter your email",
            height=40
        )
        email_entry.pack(fill="x")
        
        # Password
        password_frame = ctk.CTkFrame(login_container, fg_color="transparent")
        password_frame.pack(fill="x", pady=10)
        
        password_label = ctk.CTkLabel(password_frame, text="Password")
        password_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        password_entry = ctk.CTkEntry(
            password_frame, 
            width=300, 
            placeholder_text="Enter your password", 
            show="•",
            height=40
        )
        password_entry.pack(fill="x")
        
        # Remember me and forgot password
        options_frame = ctk.CTkFrame(login_container, fg_color="transparent")
        options_frame.pack(fill="x", pady=10)
        
        remember_var = IntVar(value=0)
        remember_checkbox = ctk.CTkCheckBox(
            options_frame, 
            text="Remember me", 
            variable=remember_var,
            checkbox_width=20,
            checkbox_height=20
        )
        remember_checkbox.pack(side="left")
        
        forgot_button = ctk.CTkButton(
            options_frame, 
            text="Forgot password?", 
            fg_color="transparent", 
            text_color=("blue", "#ADD8E6"),
            hover=False,
            command=self.show_forgot_password
        )
        forgot_button.pack(side="right")
        
        # Login button
        login_button = ctk.CTkButton(
            login_container, 
            text="Login", 
            command=lambda: self.login(email_entry.get(), password_entry.get()),
            height=40,
            corner_radius=8
        )
        login_button.pack(pady=20, fill="x")
        
        # Register link
        register_frame = ctk.CTkFrame(login_container, fg_color="transparent")
        register_frame.pack(pady=10)
        
        register_label = ctk.CTkLabel(register_frame, text="Don't have an account?")
        register_label.pack(side="left", padx=(0, 5))
        
        register_button = ctk.CTkButton(
            register_frame, 
            text="Register", 
            command=self.show_register_screen, 
            fg_color="transparent", 
            text_color=("blue", "#ADD8E6"),
            hover=False
        )
        register_button.pack(side="left")
        
        # Version info
        version_label = ctk.CTkLabel(
            login_container, 
            text="Version 2.0.0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(pady=(30, 0))
    
    def show_forgot_password(self):
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Forgot Password")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog on screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Content
        header_label = ctk.CTkLabel(
            dialog, 
            text="Reset Your Password", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack(pady=(20, 5))
        
        info_label = ctk.CTkLabel(
            dialog, 
            text="Enter your email address below to receive a password reset link.",
            wraplength=350
        )
        info_label.pack(pady=(0, 20))
        
        # Email
        email_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        email_frame.pack(fill="x", padx=30)
        
        email_label = ctk.CTkLabel(email_frame, text="Email")
        email_label.pack(anchor="w", pady=(0, 5))
        
        email_entry = ctk.CTkEntry(
            email_frame, 
            width=340, 
            placeholder_text="Enter your email",
            height=40
        )
        email_entry.pack(fill="x")
        
        # Reset button
        reset_button = ctk.CTkButton(
            dialog, 
            text="Send Reset Link", 
            command=lambda: self.send_password_reset(email_entry.get(), dialog),
            height=40,
            corner_radius=8
        )
        reset_button.pack(pady=20, padx=30, fill="x")
    
    def send_password_reset(self, email, dialog):
        if not email:
            CTkMessagebox(
                title="Error", 
                message="Please enter your email address.",
                icon="cancel"
            )
            return
        
        if not validate_email(email):
            CTkMessagebox(
                title="Error", 
                message="Please enter a valid email address.",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Check if email exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    # In a real application, send an email with a password reset link
                    # For this demo, just show a success message
                    dialog.destroy()
                    CTkMessagebox(
                        title="Success", 
                        message=f"A password reset link has been sent to {email}. Please check your inbox.",
                        icon="check"
                    )
                else:
                    CTkMessagebox(
                        title="Error", 
                        message="No account found with this email address.",
                        icon="cancel"
                    )
            except Exception as e:
                CTkMessagebox(
                    title="Error", 
                    message=f"An error occurred: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_register_screen(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ctk.CTkFrame(self.app, corner_radius=0)
        main_container.pack(fill="both", expand=True)
        
        # Split into two parts: Left (image) and Right (registration form)
        left_panel = ctk.CTkFrame(main_container, corner_radius=0)
        left_panel.pack(side="left", fill="both", expand=True)
        
        right_panel = ctk.CTkFrame(main_container, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Left panel - Image
        try:
            bg_img = Image.open("assets/train_register.jpg")
            bg_photo = ImageTk.PhotoImage(bg_img)
            
            bg_label = ctk.CTkLabel(left_panel, image=bg_photo, text="")
            bg_label.image = bg_photo  # Keep a reference
            bg_label.pack(fill="both", expand=True)
            
            # Overlay text
            overlay = ctk.CTkFrame(left_panel, fg_color=("rgba(0, 0, 0, 0.6)", "rgba(0, 0, 0, 0.6)"))
            overlay.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.3)
            
            quote = ctk.CTkLabel(
                overlay,
                text="Embark on a new journey with us!",
                font=ctk.CTkFont(size=18, weight="bold"),
                wraplength=400,
                text_color="white"
            )
            quote.pack(pady=20, padx=20)
        except:
            # Fallback if image is not available
            title_label = ctk.CTkLabel(
                left_panel, 
                text="Join Our Community", 
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(100, 20))
            
            subtitle_label = ctk.CTkLabel(
                left_panel, 
                text="Create an account to access all features",
                font=ctk.CTkFont(size=16)
            )
            subtitle_label.pack()
        
        # Right panel - Registration form
        # Create a scrollable frame to hold the registration form
        scrollable_frame = ctk.CTkScrollableFrame(right_panel)
        scrollable_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Title
        title_label = ctk.CTkLabel(
            scrollable_frame, 
            text="Create Account", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            scrollable_frame, 
            text="Fill in the details to register", 
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Form fields
        # Full Name
        name_label = ctk.CTkLabel(scrollable_frame, text="Full Name")
        name_label.pack(anchor="w", pady=(10, 5))
        
        name_entry = ctk.CTkEntry(
            scrollable_frame, 
            placeholder_text="Enter your full name",
            height=40
        )
        name_entry.pack(fill="x", pady=(0, 10))
        
        # Email
        email_label = ctk.CTkLabel(scrollable_frame, text="Email")
        email_label.pack(anchor="w", pady=(10, 5))
        
        email_entry = ctk.CTkEntry(
            scrollable_frame, 
            placeholder_text="Enter your email",
            height=40
        )
        email_entry.pack(fill="x", pady=(0, 10))
        
        # Phone
        phone_label = ctk.CTkLabel(scrollable_frame, text="Phone Number (Optional)")
        phone_label.pack(anchor="w", pady=(10, 5))
        
        phone_entry = ctk.CTkEntry(
            scrollable_frame, 
            placeholder_text="Enter your phone number",
            height=40
        )
        phone_entry.pack(fill="x", pady=(0, 10))
        
        # Password
        password_label = ctk.CTkLabel(scrollable_frame, text="Password")
        password_label.pack(anchor="w", pady=(10, 5))
        
        password_entry = ctk.CTkEntry(
            scrollable_frame, 
            placeholder_text="Enter your password", 
            show="•",
            height=40
        )
        password_entry.pack(fill="x", pady=(0, 10))
        
        # Password requirements
        password_req = ctk.CTkLabel(
            scrollable_frame, 
            text="Password must be at least 6 characters long",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        password_req.pack(anchor="w")
        
        # Confirm Password
        confirm_password_label = ctk.CTkLabel(scrollable_frame, text="Confirm Password")
        confirm_password_label.pack(anchor="w", pady=(10, 5))
        
        confirm_password_entry = ctk.CTkEntry(
            scrollable_frame, 
            placeholder_text="Confirm your password", 
            show="•",
            height=40
        )
        confirm_password_entry.pack(fill="x", pady=(0, 10))
        
        # Terms and conditions
        terms_var = IntVar(value=0)
        terms_checkbox = ctk.CTkCheckBox(
            scrollable_frame, 
            text="I agree to the Terms and Conditions", 
            variable=terms_var,
            checkbox_width=20,
            checkbox_height=20
        )
        terms_checkbox.pack(anchor="w", pady=(10, 20))
        
        # Register button
        register_button = ctk.CTkButton(
            scrollable_frame, 
            text="Register", 
            command=lambda: self.register(
                name_entry.get(), 
                email_entry.get(), 
                password_entry.get(), 
                confirm_password_entry.get(),
                phone_entry.get(),
                terms_var.get()
            ),
            height=40,
            corner_radius=8
        )
        register_button.pack(pady=(0, 20), fill="x")
        
        # Back to login link
        back_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        back_frame.pack()
        
        back_label = ctk.CTkLabel(back_frame, text="Already have an account?")
        back_label.pack(side="left", padx=(0, 5))
        
        back_button = ctk.CTkButton(
            back_frame, 
            text="Login", 
            command=self.show_login_screen, 
            fg_color="transparent", 
            text_color=("blue", "#ADD8E6"),
            hover=False
        )
        back_button.pack(side="left")
    
    def login(self, email, password):
        if not email or not password:
            CTkMessagebox(
                title="Login Error", 
                message="Please enter both email and password",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get user by email
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    self.current_user = user
                    
                    # Set theme based on user preference
                    self.current_theme = user.get('theme', 'light')
                    ctk.set_appearance_mode(self.current_theme)
                    
                    if user['is_admin']:
                        self.show_admin_dashboard()
                    else:
                        self.show_user_dashboard()
                else:
                    CTkMessagebox(
                        title="Login Error", 
                        message="Invalid email or password",
                        icon="cancel"
                    )
            except Exception as e:
                CTkMessagebox(
                    title="Login Error", 
                    message=f"An error occurred: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def register(self, name, email, password, confirm_password, phone=None, terms_accepted=0):
        if not name or not email or not password or not confirm_password:
            CTkMessagebox(
                title="Registration Error", 
                message="Please fill in all required fields",
                icon="cancel"
            )
            return
        
        if not validate_email(email):
            CTkMessagebox(
                title="Registration Error", 
                message="Please enter a valid email address",
                icon="cancel"
            )
            return
        
        if phone and not validate_phone(phone):
            CTkMessagebox(
                title="Registration Error", 
                message="Please enter a valid phone number",
                icon="cancel"
            )
            return
        
        if password != confirm_password:
            CTkMessagebox(
                title="Registration Error", 
                message="Passwords do not match",
                icon="cancel"
            )
            return
        
        if len(password) < 6:
            CTkMessagebox(
                title="Registration Error", 
                message="Password must be at least 6 characters long",
                icon="cancel"
            )
            return
        
        if not terms_accepted:
            CTkMessagebox(
                title="Registration Error", 
                message="You must accept the Terms and Conditions",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    CTkMessagebox(
                        title="Registration Error", 
                        message="Email already registered",
                        icon="cancel"
                    )
                    return
                
                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # Insert new user
                if phone:
                    cursor.execute(
                        "INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)",
                        (name, email, hashed_password, phone)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                        (name, email, hashed_password)
                    )
                
                connection.commit()
                
                # Show success message
                CTkMessagebox(
                    title="Registration Successful", 
                    message="Your account has been created successfully. You can now login.",
                    icon="check"
                )
                
                # Safely navigate to login screen (FIX ADDED HERE)
                self.app.after(1000, self.show_login_screen)
                
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Registration Error", 
                    message=f"An error occurred: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def logout(self):
        self.current_user = None
        self.show_login_screen()
    
    # Admin Dashboard
    def show_admin_dashboard(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Dashboard" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Dashboard" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Admin Dashboard", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Current date and time
        current_datetime = "2025-05-04 13:51:07"  # Use the provided UTC time
        date_label = ctk.CTkLabel(
            header_frame, 
            text=current_datetime,
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        date_label.pack(side="right", padx=20)
        
        # Dashboard content
        dashboard_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Dashboard grid
        dashboard_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="column")
        dashboard_frame.rowconfigure(0, weight=0)  # For stats cards
        dashboard_frame.rowconfigure(1, weight=2)  # For booking chart (now expanded)
        dashboard_frame.rowconfigure(2, weight=1)  # For activities and schedules
        
        # Stats cards
        self.create_stats_card(dashboard_frame, "Total Trains", self.get_total_trains(), "assets/train_icon.png", 0, 0)
        self.create_stats_card(dashboard_frame, "Total Schedules", self.get_total_schedules(), "assets/schedule_icon.png", 0, 1)
        self.create_stats_card(dashboard_frame, "Total Bookings", self.get_total_bookings(), "assets/booking_icon.png", 0, 2)
        self.create_stats_card(dashboard_frame, "Total Revenue", format_currency(self.get_total_revenue()), "assets/revenue_icon.png", 0, 3)
        
        # Charts - Expanded booking chart to fill the entire row
        booking_chart_frame = ctk.CTkFrame(dashboard_frame)
        booking_chart_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        
        booking_chart_label = ctk.CTkLabel(
            booking_chart_frame, 
            text="Bookings - Last 7 Days", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        booking_chart_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        booking_chart = self.create_booking_chart(booking_chart_frame)
        booking_chart.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        # Recent activities and schedules
        recent_activities_frame = ctk.CTkFrame(dashboard_frame)
        recent_activities_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        activities_label = ctk.CTkLabel(
            recent_activities_frame, 
            text="Recent Bookings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        activities_label.pack(anchor="w", padx=15, pady=15)
        
        self.show_recent_bookings(recent_activities_frame)
        
        upcoming_schedules_frame = ctk.CTkFrame(dashboard_frame)
        upcoming_schedules_frame.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        schedules_label = ctk.CTkLabel(
            upcoming_schedules_frame, 
            text="Upcoming Departures", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        schedules_label.pack(anchor="w", padx=15, pady=15)
        
        self.show_upcoming_schedules(upcoming_schedules_frame)
    
    def show_admin_tab(self, tab_name):
        # This method handles navigation between admin tabs
        if tab_name == "trains":
            self.show_admin_trains_tab()
        elif tab_name == "schedules":
            self.show_admin_schedules_tab()
        elif tab_name == "bookings":
            self.show_admin_bookings_tab()
        elif tab_name == "revenue":
            self.show_admin_revenue_tab()
        elif tab_name == "passengers":
            self.show_admin_passengers_tab()
        elif tab_name == "settings":
            self.show_admin_settings_tab()
    
    def create_stats_card(self, parent, title, value, icon_path, row, column):
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        
        card_content = ctk.CTkFrame(card, fg_color="transparent")
        card_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        try:
            icon_img = load_image(icon_path, (32, 32))
            icon_label = ctk.CTkLabel(card_content, image=icon_img, text="")
            icon_label.image = icon_img
            icon_label.pack(anchor="w")
        except:
            pass
        
        title_label = ctk.CTkLabel(
            card_content, 
            text=title,
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray70")
        )
        title_label.pack(anchor="w", pady=(5, 0))
        
        value_label = ctk.CTkLabel(
            card_content, 
            text=str(value),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(anchor="w", pady=(5, 0))
    
    def get_total_trains(self):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM trains")
                return cursor.fetchone()[0]
            except Exception as e:
                print(f"Error getting total trains: {e}")
                return 0
            finally:
                cursor.close()
                connection.close()
        return 0
    
    def get_total_schedules(self):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM schedules")
                return cursor.fetchone()[0]
            except Exception as e:
                print(f"Error getting total schedules: {e}")
                return 0
            finally:
                cursor.close()
                connection.close()
        return 0
    
    def get_total_bookings(self):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM bookings")
                return cursor.fetchone()[0]
            except Exception as e:
                print(f"Error getting total bookings: {e}")
                return 0
            finally:
                cursor.close()
                connection.close()
        return 0
    
    def get_total_revenue(self):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT COALESCE(SUM(total_fare), 0) FROM bookings WHERE status = 'confirmed'")
                return cursor.fetchone()[0]
            except Exception as e:
                print(f"Error getting total revenue: {e}")
                return 0
            finally:
                cursor.close()
                connection.close()
        return 0
    
    def create_booking_chart(self, parent):
        # Get booking data for last 7 days
        connection = get_db_connection()
        dates = []
        bookings = []
        
        if connection:
            cursor = connection.cursor()
            try:
                # Generate last 7 days
                for i in range(6, -1, -1):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    dates.append((datetime.now() - timedelta(days=i)).strftime('%b %d'))
                    
                    cursor.execute(
                        "SELECT COUNT(*) FROM bookings WHERE DATE(booking_date) = %s",
                        (date,)
                    )
                    bookings.append(cursor.fetchone()[0])
            except Exception as e:
                print(f"Error getting booking data: {e}")
                # Add dummy data if there's an error
                dates = [(datetime.now() - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
                bookings = [random.randint(5, 20) for _ in range(7)]
            finally:
                cursor.close()
                connection.close()
        else:
            # Add dummy data if no connection
            dates = [(datetime.now() - timedelta(days=i)).strftime('%b %d') for i in range(6, -1, -1)]
            bookings = [random.randint(5, 20) for _ in range(7)]
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        
        # Set background color to match CTk theme
        bg_color = "white" if self.current_theme == "light" else "#2d2d2d"
        text_color = "black" if self.current_theme == "light" else "white"
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Create bar chart
        bars = ax.bar(dates, bookings, color=THEME_COLORS[self.current_theme]["primary"], width=0.6)
        
        # Add data labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 0.1,
                str(int(height)),
                ha='center', 
                va='bottom',
                color=text_color,
                fontsize=8
            )
        
        # Customize chart
        ax.set_xlabel('Date', color=text_color)
        ax.set_ylabel('Number of Bookings', color=text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('gray')
        ax.spines['left'].set_color('gray')
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        ax.yaxis.grid(True, linestyle='--', alpha=0.7, color='gray')
        
        plt.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas_widget = canvas.get_tk_widget()
        
        return canvas_widget
    
    def create_revenue_chart(self, parent):
        # Get revenue data by class
        connection = get_db_connection()
        labels = ['Sleeper', 'AC', 'General']
        values = [0, 0, 0]
        
        if connection:
            cursor = connection.cursor()
            try:
                # Query for each class
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN p.seat_class = 'sleeper' THEN b.total_fare ELSE 0 END) AS sleeper_revenue,
                        SUM(CASE WHEN p.seat_class = 'ac' THEN b.total_fare ELSE 0 END) AS ac_revenue,
                        SUM(CASE WHEN p.seat_class = 'general' THEN b.total_fare ELSE 0 END) AS general_revenue
                    FROM 
                        passengers p
                    JOIN 
                        bookings b ON p.booking_id = b.id
                    WHERE 
                        b.status = 'confirmed'
                """)
                result = cursor.fetchone()
                
                if result:
                    values = [
                        result[0] if result[0] else 0,
                        result[1] if result[1] else 0,
                        result[2] if result[2] else 0
                    ]
            except Exception as e:
                print(f"Error getting revenue data: {e}")
                # Add dummy data if there's an error
                values = [random.randint(15000, 25000) for _ in range(3)]
            finally:
                cursor.close()
                connection.close()
        else:
            # Add dummy data if no connection
            values = [random.randint(15000, 25000) for _ in range(3)]
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        
        # Set background color to match CTk theme
        bg_color = "white" if self.current_theme == "light" else "#2d2d2d"
        text_color = "black" if self.current_theme == "light" else "white"
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Create pie chart
        colors = [
            THEME_COLORS[self.current_theme]["primary"],
            THEME_COLORS[self.current_theme]["secondary"],
            THEME_COLORS[self.current_theme]["accent"]
        ]
        
        # Add percentage to labels
        total = sum(values)
        percentages = [100 * val / total if total > 0 else 0 for val in values]
        pie_labels = [f"{label}\n({val:,.0f}₹, {p:.1f}%)" for label, val, p in zip(labels, values, percentages)]
        
        wedges, texts = ax.pie(
            values, 
            labels=None, 
            autopct=None,
            startangle=90,
            colors=colors,
            wedgeprops={'width': 0.5} # Make it a donut chart
        )
        
        # Add legend
        ax.legend(
            wedges, 
            pie_labels,
            loc="center",
            fontsize=8,
            frameon=False,
            labelcolor=text_color
        )
        
        # Add total in center
        ax.text(
            0, 0,
            f"Total\n{format_currency(total)}",
            ha='center',
            va='center',
            fontsize=9,
            fontweight='bold',
            color=text_color
        )
        
        ax.set_title('Revenue Distribution by Class', color=text_color, fontsize=10)
        
        plt.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas_widget = canvas.get_tk_widget()
        
        return canvas_widget
    
    def show_recent_bookings(self, parent):
        # Create scrollable frame
        bookings_scroll = ctk.CTkScrollableFrame(parent)
        bookings_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Get recent bookings
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT 
                        b.id, b.pnr, u.name as user_name, b.booking_date, b.total_fare, b.status,
                        t.train_name, s.source, s.destination, s.departure_date, s.departure_time
                    FROM 
                        bookings b
                    JOIN 
                        users u ON b.user_id = u.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    ORDER BY 
                        b.booking_date DESC
                    LIMIT 5
                """)
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_data_label = ctk.CTkLabel(
                        bookings_scroll, 
                        text="No recent bookings found",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_data_label.pack(pady=20)
                    return
                
                # Create bookings list
                for booking in bookings:
                    booking_frame = ctk.CTkFrame(bookings_scroll)
                    booking_frame.pack(fill="x", pady=5)
                    
                    # PNR and status
                    header_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    header_frame.pack(fill="x", padx=10, pady=(10, 5))
                    
                    pnr_label = ctk.CTkLabel(
                        header_frame,
                        text=f"PNR: {booking['pnr']}",
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
                    pnr_label.pack(side="left")
                    
                    status_color = "#43a047" if booking['status'] == 'confirmed' else "#e53935"
                    status_text = "Confirmed" if booking['status'] == 'confirmed' else "Cancelled"
                    
                    status_label = ctk.CTkLabel(
                        header_frame,
                        text=status_text,
                        font=ctk.CTkFont(size=12),
                        text_color=status_color
                    )
                    status_label.pack(side="right")
                    
                    # Train details
                    train_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    train_frame.pack(fill="x", padx=10, pady=(0, 5))
                    
                    train_label = ctk.CTkLabel(
                        train_frame,
                        text=f"{booking['train_name']}",
                        font=ctk.CTkFont(size=13)
                    )
                    train_label.pack(side="left")
                    
                    route_label = ctk.CTkLabel(
                        train_frame,
                        text=f"{booking['source']} → {booking['destination']}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    route_label.pack(side="right")
                    
                    # Bottom details
                    bottom_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", padx=10, pady=(0, 10))
                    
                    date_str = f"{booking['departure_date']} {booking['departure_time']}"
                    date_label = ctk.CTkLabel(
                        bottom_frame,
                        text=f"Departure: {date_str}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    date_label.pack(side="left")
                    
                    fare_label = ctk.CTkLabel(
                        bottom_frame,
                        text=format_currency(booking['total_fare']),
                        font=ctk.CTkFont(size=12, weight="bold")
                    )
                    fare_label.pack(side="right")
            except Exception as e:
                print(f"Error loading recent bookings: {e}")
                no_data_label = ctk.CTkLabel(
                    bookings_scroll, 
                    text="Error loading recent bookings",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_data_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            no_data_label = ctk.CTkLabel(
                bookings_scroll, 
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            no_data_label.pack(pady=20)
    
    def show_upcoming_schedules(self, parent):
        # Create scrollable frame
        schedules_scroll = ctk.CTkScrollableFrame(parent)
        schedules_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Get upcoming schedules
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get schedules departing today or in the future
                current_date = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT 
                        s.id, t.train_number, t.train_name, s.source, s.destination, 
                        s.departure_date, s.departure_time, s.status, s.delay_minutes
                    FROM 
                        schedules s
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        (s.departure_date > %s) OR 
                        (s.departure_date = %s AND s.departure_time >= %s)
                    ORDER BY 
                        s.departure_date, s.departure_time
                    LIMIT 5
                """, (current_date, current_date, datetime.now().strftime('%H:%M')))
                schedules = cursor.fetchall()
                
                if not schedules:
                    no_data_label = ctk.CTkLabel(
                        schedules_scroll, 
                        text="No upcoming schedules found",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_data_label.pack(pady=20)
                    return
                
                # Create schedules list
                for schedule in schedules:
                    schedule_frame = ctk.CTkFrame(schedules_scroll)
                    schedule_frame.pack(fill="x", pady=5)
                    
                    # Train details
                    header_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
                    header_frame.pack(fill="x", padx=10, pady=(10, 5))
                    
                    train_label = ctk.CTkLabel(
                        header_frame,
                        text=f"{schedule['train_number']} - {schedule['train_name']}",
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
                    train_label.pack(side="left")
                    
                    # Status indicator
                    status_color = "#43a047"  # Default green for on-time
                    status_text = "On Time"
                    
                    if schedule['status'] == 'delayed':
                        status_color = "#ffb300"  # Orange for delayed
                        status_text = f"Delayed {schedule['delay_minutes']} min"
                    elif schedule['status'] == 'cancelled':
                        status_color = "#e53935"  # Red for cancelled
                        status_text = "Cancelled"
                    
                    status_label = ctk.CTkLabel(
                        header_frame,
                        text=status_text,
                        font=ctk.CTkFont(size=12),
                        text_color=status_color
                    )
                    status_label.pack(side="right")
                    
                    # Route
                    route_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
                    route_frame.pack(fill="x", padx=10, pady=(0, 5))
                    
                    route_label = ctk.CTkLabel(
                        route_frame,
                        text=f"{schedule['source']} → {schedule['destination']}",
                        font=ctk.CTkFont(size=13)
                    )
                    route_label.pack(side="left")
                    
                    # Departure details
                    bottom_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", padx=10, pady=(0, 10))
                    
                    date_label = ctk.CTkLabel(
                        bottom_frame,
                        text=f"Departure: {schedule['departure_date']} {schedule['departure_time']}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    date_label.pack(side="left")
            except Exception as e:
                print(f"Error loading upcoming schedules: {e}")
                no_data_label = ctk.CTkLabel(
                    schedules_scroll, 
                    text="Error loading upcoming schedules",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_data_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            no_data_label = ctk.CTkLabel(
                schedules_scroll, 
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            no_data_label.pack(pady=20)
    
    def change_appearance_mode(self, appearance_mode):
        # Convert first letter to lowercase for customtkinter
        mode = appearance_mode.lower()
        ctk.set_appearance_mode(mode)
        self.current_theme = mode
        
        # Save theme preference for the user
        if self.current_user:
            set_user_theme(self.current_user['id'], mode)
    


    def show_admin_trains_tab(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Manage Trains" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Manage Trains" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Manage Trains", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Trains content
        trains_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        trains_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Split into two parts
        left_frame = ctk.CTkFrame(trains_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)
        
        right_frame = ctk.CTkFrame(trains_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
        
        # Left frame - Add new train
        add_train_label = ctk.CTkLabel(
            left_frame, 
            text="Add New Train", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        add_train_label.pack(pady=(15, 15), padx=15)
        
        # Create a scrollable frame for the form
        form_scroll = ctk.CTkScrollableFrame(left_frame)
        form_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Train Number
        train_number_label = ctk.CTkLabel(form_scroll, text="Train Number")
        train_number_label.pack(anchor="w", pady=(10, 5))
        
        train_number_entry = ctk.CTkEntry(form_scroll, placeholder_text="Enter train number", height=35)
        train_number_entry.pack(fill="x", pady=(0, 10))
        
        # Train Name
        train_name_label = ctk.CTkLabel(form_scroll, text="Train Name")
        train_name_label.pack(anchor="w", pady=(10, 5))
        
        train_name_entry = ctk.CTkEntry(form_scroll, placeholder_text="Enter train name", height=35)
        train_name_entry.pack(fill="x", pady=(0, 10))
        
        # Seats - Sleeper
        seats_sleeper_label = ctk.CTkLabel(form_scroll, text="Total Seats (Sleeper)")
        seats_sleeper_label.pack(anchor="w", pady=(10, 5))
        
        seats_sleeper_entry = ctk.CTkEntry(form_scroll, placeholder_text="Enter number of sleeper seats", height=35)
        seats_sleeper_entry.pack(fill="x", pady=(0, 10))
        
        # Seats - AC
        seats_ac_label = ctk.CTkLabel(form_scroll, text="Total Seats (AC)")
        seats_ac_label.pack(anchor="w", pady=(10, 5))
        
        seats_ac_entry = ctk.CTkEntry(form_scroll, placeholder_text="Enter number of AC seats", height=35)
        seats_ac_entry.pack(fill="x", pady=(0, 10))
        
        # Seats - General
        seats_general_label = ctk.CTkLabel(form_scroll, text="Total Seats (General)")
        seats_general_label.pack(anchor="w", pady=(10, 5))
        
        seats_general_entry = ctk.CTkEntry(form_scroll, placeholder_text="Enter number of general seats", height=35)
        seats_general_entry.pack(fill="x", pady=(0, 10))
        
        # Add Train Button
        add_train_button = ctk.CTkButton(
            form_scroll, 
            text="Add Train", 
            command=lambda: self.add_train(
                train_number_entry.get(),
                train_name_entry.get(),
                seats_sleeper_entry.get(),
                seats_ac_entry.get(),
                seats_general_entry.get(),
                train_number_entry, train_name_entry, seats_sleeper_entry, seats_ac_entry, seats_general_entry
            ),
            height=40
        )
        add_train_button.pack(fill="x", pady=(20, 10))
        
        # Clear form button
        clear_form_button = ctk.CTkButton(
            form_scroll, 
            text="Clear Form", 
            command=lambda: [entry.delete(0, 'end') for entry in [
                train_number_entry, train_name_entry, seats_sleeper_entry, seats_ac_entry, seats_general_entry
            ]],
            height=40,
            fg_color="gray",
            hover_color="gray30"
        )
        clear_form_button.pack(fill="x", pady=(0, 10))
        
        # Right frame - Train list
        trains_label = ctk.CTkLabel(
            right_frame, 
            text="Existing Trains", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        trains_label.pack(pady=(15, 10), padx=15, anchor="w")
        
        # Search frame
        search_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search trains...", 
            height=35
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        search_button = ctk.CTkButton(
            search_frame, 
            text="Search", 
            width=100,
            command=lambda: self.search_trains(trains_scroll, search_entry.get())
        )
        search_button.pack(side="right")
        
        # Create a scrollable frame for the train list
        trains_scroll = ctk.CTkScrollableFrame(right_frame)
        trains_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            right_frame, 
            text="Refresh Train List", 
            command=lambda: self.load_trains(trains_scroll),
            height=35
        )
        refresh_button.pack(pady=10, padx=15, fill="x")
        
        # Load trains
        self.load_trains(trains_scroll)



    
    def add_train(self, train_number, train_name, seats_sleeper, seats_ac, seats_general, *entries):
        if not train_number or not train_name or not seats_sleeper or not seats_ac or not seats_general:
            CTkMessagebox(
                title="Error", 
                message="Please fill in all fields",
                icon="cancel"
            )
            return
        
        try:
            seats_sleeper = int(seats_sleeper)
            seats_ac = int(seats_ac)
            seats_general = int(seats_general)
            
            if seats_sleeper <= 0 or seats_ac <= 0 or seats_general <= 0:
                CTkMessagebox(
                    title="Error", 
                    message="Seat numbers must be positive integers",
                    icon="cancel"
                )
                return
        except ValueError:
            CTkMessagebox(
                title="Error", 
                message="Seat numbers must be integers",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Check if train number already exists
                cursor.execute("SELECT id FROM trains WHERE train_number = %s", (train_number,))
                if cursor.fetchone():
                    CTkMessagebox(
                        title="Error", 
                        message="Train number already exists",
                        icon="cancel"
                    )
                    return
                
                # Insert new train
                cursor.execute(
                    "INSERT INTO trains (train_number, train_name, total_seats_sleeper, total_seats_ac, total_seats_general) VALUES (%s, %s, %s, %s, %s)",
                    (train_number, train_name, seats_sleeper, seats_ac, seats_general)
                )
                
                connection.commit()
                CTkMessagebox(
                    title="Success", 
                    message="Train added successfully",
                    icon="check"
                )
                
                # Clear the form fields if entries are provided
                if entries:
                    for entry in entries:
                        entry.delete(0, 'end')
                
                # Refresh the train list
                for widget in self.app.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkScrollableFrame):
                                        self.load_trains(grandchild)
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Error", 
                    message=f"Failed to add train: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def search_trains(self, container, search_term):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        # Create a single frame for the entire content
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Search by train number or name
                search_pattern = f"%{search_term}%"
                cursor.execute(
                    "SELECT * FROM trains WHERE train_number LIKE %s OR train_name LIKE %s ORDER BY train_name",
                    (search_pattern, search_pattern)
                )
                
                trains = cursor.fetchall()
                
                if not trains:
                    no_results_label = ctk.CTkLabel(
                        content_frame, 
                        text=f"No trains found matching '{search_term}'",
                        text_color=("gray50", "gray70")
                    )
                    no_results_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        content_frame, 
                        text="Show All Trains", 
                        command=lambda: self.load_trains(container),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Create a table-like structure
                table_frame = ctk.CTkFrame(content_frame)
                table_frame.pack(fill="both", expand=True, padx=0, pady=0)
                
                # Header row (dark gray)
                header_frame = ctk.CTkFrame(table_frame, fg_color=("gray80", "gray25"), height=40)
                header_frame.pack(fill="x", pady=0)
                header_frame.pack_propagate(False)  # Maintain fixed height
                
                # Configure header columns
                header_frame.columnconfigure(0, weight=1, minsize=100)  # Train Number
                header_frame.columnconfigure(1, weight=2, minsize=150)  # Train Name
                header_frame.columnconfigure(2, weight=1, minsize=80)   # Sleeper
                header_frame.columnconfigure(3, weight=1, minsize=80)   # AC
                header_frame.columnconfigure(4, weight=1, minsize=80)   # General
                header_frame.columnconfigure(5, weight=1, minsize=150)  # Actions
                
                # Create header labels
                ctk.CTkLabel(header_frame, text="Train Number", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="Train Name", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="Sleeper", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="AC", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="General", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="Actions", font=ctk.CTkFont(weight="bold")).grid(row=0, column=5, padx=10, pady=10, sticky="w")
                
                # Fix for customtkinter: Use a frame that doesn't expand vertically
                scroll_container = ctk.CTkFrame(table_frame, fg_color="transparent")
                scroll_container.pack(fill="x", anchor="n")
                
                # Calculate the height needed based on number of trains
                # Each row is about 50 pixels high, add some padding
                row_height = 50
                max_visible_rows = 10  # Maximum number of rows to show before scrolling
                total_rows = len(trains)
                scroll_height = min(total_rows * row_height, max_visible_rows * row_height)
                
                # Data rows in scrollable frame with fixed height
                rows_frame = ctk.CTkScrollableFrame(scroll_container, orientation="vertical", height=scroll_height)
                rows_frame.pack(fill="x")
                
                # Use grid for the scrollable frame to make all rows have consistent width
                rows_frame.grid_columnconfigure(0, weight=1)
                
                # Now create each data row with the same grid layout as the header
                for i, train in enumerate(trains):
                    # Alternate row colors for better readability
                    bg_color = "transparent" if i % 2 == 0 else ("gray90", "gray20")
                    
                    row_frame = ctk.CTkFrame(rows_frame, fg_color=bg_color)
                    row_frame.grid(row=i, column=0, sticky="ew", pady=1)
                    
                    # Match column configuration with header
                    row_frame.columnconfigure(0, weight=1, minsize=100)
                    row_frame.columnconfigure(1, weight=2, minsize=150)
                    row_frame.columnconfigure(2, weight=1, minsize=80)
                    row_frame.columnconfigure(3, weight=1, minsize=80)
                    row_frame.columnconfigure(4, weight=1, minsize=80)
                    row_frame.columnconfigure(5, weight=1, minsize=150)
                    
                    # Train data
                    ctk.CTkLabel(row_frame, text=train['train_number']).grid(row=0, column=0, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=train['train_name']).grid(row=0, column=1, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=str(train['total_seats_sleeper'])).grid(row=0, column=2, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=str(train['total_seats_ac'])).grid(row=0, column=3, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=str(train['total_seats_general'])).grid(row=0, column=4, padx=10, pady=8, sticky="w")
                    
                    # Action buttons
                    action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                    action_frame.grid(row=0, column=5, padx=5, pady=5, sticky="w")
                    
                    edit_button = ctk.CTkButton(
                        action_frame, 
                        text="Edit",
                        width=60,
                        height=30,
                        command=lambda t=train: self.show_edit_train_dialog(t)
                    )
                    edit_button.pack(side="left", padx=(0, 5))
                    
                    delete_button = ctk.CTkButton(
                        action_frame, 
                        text="Delete",
                        width=60,
                        height=30,
                        fg_color="#e53935",
                        hover_color="#c62828",
                        command=lambda t=train: self.delete_train(t['id'], container)
                    )
                    delete_button.pack(side="left")
                
                # Add a spacer at the bottom to push everything up
                # This prevents the large gap at the bottom
                spacer = ctk.CTkFrame(content_frame, fg_color="transparent", height=1)
                spacer.pack(side="bottom", fill="x")
                
            except Exception as e:
                print(f"Error searching trains: {e}")
                error_label = ctk.CTkLabel(
                    content_frame,
                    text=f"Error searching trains: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
            
    
    def load_trains(self, container):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        # Create a single frame for the entire content
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("SELECT * FROM trains ORDER BY train_name")
                trains = cursor.fetchall()
                
                if not trains:
                    no_trains_label = ctk.CTkLabel(
                        content_frame, 
                        text="No trains found",
                        text_color=("gray50", "gray70")
                    )
                    no_trains_label.pack(pady=20)
                    return
                
                # Create a table-like structure
                table_frame = ctk.CTkFrame(content_frame)
                table_frame.pack(fill="both", expand=True, padx=0, pady=0)
                
                # Header row (dark gray)
                header_frame = ctk.CTkFrame(table_frame, fg_color=("gray80", "gray25"), height=40)
                header_frame.pack(fill="x", pady=0)
                header_frame.pack_propagate(False)  # Maintain fixed height
                
                # Configure header columns
                header_frame.columnconfigure(0, weight=1, minsize=100)  # Train Number
                header_frame.columnconfigure(1, weight=2, minsize=150)  # Train Name
                header_frame.columnconfigure(2, weight=1, minsize=80)   # Sleeper
                header_frame.columnconfigure(3, weight=1, minsize=80)   # AC
                header_frame.columnconfigure(4, weight=1, minsize=80)   # General
                header_frame.columnconfigure(5, weight=1, minsize=150)  # Actions
                
                # Create header labels
                ctk.CTkLabel(header_frame, text="Train Number", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="Train Name", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="Sleeper", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="AC", font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="General", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=10, pady=10, sticky="w")
                ctk.CTkLabel(header_frame, text="Actions", font=ctk.CTkFont(weight="bold")).grid(row=0, column=5, padx=10, pady=10, sticky="w")
                
                # Fix for customtkinter: Use a frame that doesn't expand vertically
                scroll_container = ctk.CTkFrame(table_frame, fg_color="transparent")
                scroll_container.pack(fill="x", anchor="n")
                
                # Calculate the height needed based on number of trains
                # Each row is about 50 pixels high, add some padding
                row_height = 50
                max_visible_rows = 10  # Maximum number of rows to show before scrolling
                total_rows = len(trains)
                scroll_height = min(total_rows * row_height, max_visible_rows * row_height)
                
                # Data rows in scrollable frame with fixed height
                rows_frame = ctk.CTkScrollableFrame(scroll_container, orientation="vertical", height=scroll_height)
                rows_frame.pack(fill="x")
                
                # Use grid for the scrollable frame to make all rows have consistent width
                rows_frame.grid_columnconfigure(0, weight=1)
                
                # Now create each data row with the same grid layout as the header
                for i, train in enumerate(trains):
                    # Alternate row colors for better readability
                    bg_color = "transparent" if i % 2 == 0 else ("gray90", "gray20")
                    
                    row_frame = ctk.CTkFrame(rows_frame, fg_color=bg_color)
                    row_frame.grid(row=i, column=0, sticky="ew", pady=1)
                    
                    # Match column configuration with header
                    row_frame.columnconfigure(0, weight=1, minsize=100)
                    row_frame.columnconfigure(1, weight=2, minsize=150)
                    row_frame.columnconfigure(2, weight=1, minsize=80)
                    row_frame.columnconfigure(3, weight=1, minsize=80)
                    row_frame.columnconfigure(4, weight=1, minsize=80)
                    row_frame.columnconfigure(5, weight=1, minsize=150)
                    
                    # Train data
                    ctk.CTkLabel(row_frame, text=train['train_number']).grid(row=0, column=0, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=train['train_name']).grid(row=0, column=1, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=str(train['total_seats_sleeper'])).grid(row=0, column=2, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=str(train['total_seats_ac'])).grid(row=0, column=3, padx=10, pady=8, sticky="w")
                    ctk.CTkLabel(row_frame, text=str(train['total_seats_general'])).grid(row=0, column=4, padx=10, pady=8, sticky="w")
                    
                    # Action buttons
                    action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                    action_frame.grid(row=0, column=5, padx=5, pady=5, sticky="w")
                    
                    edit_button = ctk.CTkButton(
                        action_frame, 
                        text="Edit",
                        width=60,
                        height=30,
                        command=lambda t=train: self.show_edit_train_dialog(t)
                    )
                    edit_button.pack(side="left", padx=(0, 5))
                    
                    delete_button = ctk.CTkButton(
                        action_frame, 
                        text="Delete",
                        width=60,
                        height=30,
                        fg_color="#e53935",
                        hover_color="#c62828",
                        command=lambda t=train: self.delete_train(t['id'], container)
                    )
                    delete_button.pack(side="left")
                
                # Add a spacer at the bottom to push everything up
                # This prevents the large gap at the bottom
                spacer = ctk.CTkFrame(content_frame, fg_color="transparent", height=1)
                spacer.pack(side="bottom", fill="x")
                
            except Exception as e:
                print(f"Error loading trains: {e}")
                error_label = ctk.CTkLabel(
                    content_frame, 
                    text=f"Error loading trains: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def display_trains(self, container, trains):
        # Headers
        header_frame = ctk.CTkFrame(container, fg_color=("gray80", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=5)
        
        header_columns = [
            ("Train Number", 120),
            ("Train Name", 180),
            ("Sleeper", 80),
            ("AC", 80),
            ("General", 80),
            ("Actions", 120)
        ]
        
        for i, (text, width) in enumerate(header_columns):
            header_label = ctk.CTkLabel(
                header_frame, 
                text=text, 
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Train rows
        for i, train in enumerate(trains):
            row_frame = ctk.CTkFrame(container)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(row_frame, text=train['train_number'], width=header_columns[0][1]).grid(row=0, column=0, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=train['train_name'], width=header_columns[1][1]).grid(row=0, column=1, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=str(train['total_seats_sleeper']), width=header_columns[2][1]).grid(row=0, column=2, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=str(train['total_seats_ac']), width=header_columns[3][1]).grid(row=0, column=3, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=str(train['total_seats_general']), width=header_columns[4][1]).grid(row=0, column=4, padx=5, pady=8, sticky="w")
            
            # Action buttons
            action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            action_frame.grid(row=0, column=5, padx=5, pady=5, sticky="w")
            
            # Edit button with icon
            try:
                edit_icon = load_image("assets/edit_icon.png", (16, 16))
                edit_button = ctk.CTkButton(
                    action_frame, 
                    text="",
                    image=edit_icon,
                    width=30,
                    height=30,
                    command=lambda t=train: self.show_edit_train_dialog(t)
                )
                edit_button.image = edit_icon
            except:
                edit_button = ctk.CTkButton(
                    action_frame, 
                    text="Edit",
                    width=60,
                    height=30,
                    command=lambda t=train: self.show_edit_train_dialog(t)
                )
            edit_button.grid(row=0, column=0, padx=2)
            
            # Delete button with icon
            try:
                delete_icon = load_image("assets/delete_icon.png", (16, 16))
                delete_button = ctk.CTkButton(
                    action_frame, 
                    text="",
                    image=delete_icon,
                    width=30,
                    height=30,
                    fg_color="#e53935",
                    hover_color="#c62828",
                    command=lambda t=train: self.delete_train(t['id'], container)
                )
                delete_button.image = delete_icon
            except:
                delete_button = ctk.CTkButton(
                    action_frame, 
                    text="Delete",
                    width=60,
                    height=30,
                    fg_color="#e53935",
                    hover_color="#c62828",
                    command=lambda t=train: self.delete_train(t['id'], container)
                )
            delete_button.grid(row=0, column=1, padx=2)
    
    def show_edit_train_dialog(self, train):
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Edit Train: {train['train_name']}")
        dialog.geometry("565x700")
        dialog.resizable(True, True)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        header_label = ctk.CTkLabel(
            dialog, 
            text=f"Edit Train: {train['train_name']}", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack(pady=(20, 20), padx=20)
        
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Train Number
        train_number_label = ctk.CTkLabel(form_frame, text="Train Number:")
        train_number_label.pack(anchor="w", pady=(10, 5))
        
        train_number_entry = ctk.CTkEntry(form_frame, height=35)
        train_number_entry.insert(0, train['train_number'])
        train_number_entry.pack(fill="x", pady=(0, 10))
        
        # Train Name
        train_name_label = ctk.CTkLabel(form_frame, text="Train Name:")
        train_name_label.pack(anchor="w", pady=(10, 5))
        
        train_name_entry = ctk.CTkEntry(form_frame, height=35)
        train_name_entry.insert(0, train['train_name'])
        train_name_entry.pack(fill="x", pady=(0, 10))
        
        # Seats - Sleeper
        seats_sleeper_label = ctk.CTkLabel(form_frame, text="Total Seats (Sleeper):")
        seats_sleeper_label.pack(anchor="w", pady=(10, 5))
        
        seats_sleeper_entry = ctk.CTkEntry(form_frame, height=35)
        seats_sleeper_entry.insert(0, str(train['total_seats_sleeper']))
        seats_sleeper_entry.pack(fill="x", pady=(0, 10))
        
        # Seats - AC
        seats_ac_label = ctk.CTkLabel(form_frame, text="Total Seats (AC):")
        seats_ac_label.pack(anchor="w", pady=(10, 5))
        
        seats_ac_entry = ctk.CTkEntry(form_frame, height=35)
        seats_ac_entry.insert(0, str(train['total_seats_ac']))
        seats_ac_entry.pack(fill="x", pady=(0, 10))
        
        # Seats - General
        seats_general_label = ctk.CTkLabel(form_frame, text="Total Seats (General):")
        seats_general_label.pack(anchor="w", pady=(10, 5))
        
        seats_general_entry = ctk.CTkEntry(form_frame, height=35)
        seats_general_entry.insert(0, str(train['total_seats_general']))
        seats_general_entry.pack(fill="x", pady=(0, 10))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Update Button
        update_button = ctk.CTkButton(
            buttons_frame, 
            text="Update Train", 
            command=lambda: self.update_train(
                train['id'],
                train_number_entry.get(),
                train_name_entry.get(),
                seats_sleeper_entry.get(),
                seats_ac_entry.get(),
                seats_general_entry.get(),
                dialog
            ),
            height=40
        )
        update_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            command=dialog.destroy,
            fg_color="gray",
            hover_color="gray30",
            height=40
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def update_train(self, train_id, train_number, train_name, seats_sleeper, seats_ac, seats_general, dialog):
        if not train_number or not train_name or not seats_sleeper or not seats_ac or not seats_general:
            CTkMessagebox(
                title="Error", 
                message="Please fill in all fields",
                icon="cancel"
            )
            return
        
        try:
            seats_sleeper = int(seats_sleeper)
            seats_ac = int(seats_ac)
            seats_general = int(seats_general)
            
            if seats_sleeper <= 0 or seats_ac <= 0 or seats_general <= 0:
                CTkMessagebox(
                    title="Error", 
                    message="Seat numbers must be positive integers",
                    icon="cancel"
                )
                return
        except ValueError:
            CTkMessagebox(
                title="Error", 
                message="Seat numbers must be integers",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Check if train number already exists for another train
                cursor.execute("SELECT id FROM trains WHERE train_number = %s AND id != %s", (train_number, train_id))
                if cursor.fetchone():
                    CTkMessagebox(
                        title="Error", 
                        message="Train number already exists for another train",
                        icon="cancel"
                    )
                    return
                
                # Update train
                cursor.execute(
                    "UPDATE trains SET train_number = %s, train_name = %s, total_seats_sleeper = %s, total_seats_ac = %s, total_seats_general = %s WHERE id = %s",
                    (train_number, train_name, seats_sleeper, seats_ac, seats_general, train_id)
                )
                
                connection.commit()
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success", 
                    message="Train updated successfully",
                    icon="check"
                )
                
                # Refresh the train list
                for widget in self.app.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkScrollableFrame):
                                        self.load_trains(grandchild)
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Error", 
                    message=f"Failed to update train: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def delete_train(self, train_id, container=None):
        # Create a confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.app)
        confirm_dialog.title("Confirm Delete")
        confirm_dialog.geometry("400x200")
        confirm_dialog.resizable(False, False)
        confirm_dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Warning icon
        try:
            warning_img = load_image("assets/warning_icon.png", (64, 64))
            warning_label = ctk.CTkLabel(confirm_dialog, image=warning_img, text="")
            warning_label.image = warning_img
            warning_label.pack(pady=(20, 0))
        except:
            pass
        
        message_label = ctk.CTkLabel(
            confirm_dialog,
            text="Are you sure you want to delete this train?\nThis will also delete all associated schedules and bookings.",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=20)
        
        buttons_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Delete Button
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            fg_color="#e53935",
            hover_color="#c62828",
            command=lambda: self.perform_delete_train(train_id, container, confirm_dialog),
            height=35
        )
        delete_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            fg_color="gray",
            hover_color="gray30",
            command=confirm_dialog.destroy,
            height=35
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def perform_delete_train(self, train_id, container, dialog):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Delete train (cascading will handle related records)
                cursor.execute("DELETE FROM trains WHERE id = %s", (train_id,))
                connection.commit()
                
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success", 
                    message="Train deleted successfully",
                    icon="check"
                )
                
                # Refresh the train list
                if container:
                    self.load_trains(container)
                else:
                    for widget in self.app.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkFrame):
                                    for grandchild in child.winfo_children():
                                        if isinstance(grandchild, ctk.CTkScrollableFrame):
                                            self.load_trains(grandchild)
            except Exception as e:
                connection.rollback()
                dialog.destroy()
                CTkMessagebox(
                    title="Error", 
                    message=f"Failed to delete train: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_admin_schedules_tab(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame with sidebar like in show_admin_trains_tab
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Add sidebar (same as in trains tab)
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Manage Schedules" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Manage Schedules" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar (same as in trains tab)
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Manage Schedules", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Schedules content
        schedules_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        schedules_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create a notebook-style interface
        tabview = ctk.CTkTabview(schedules_frame)
        tabview.pack(fill="both", expand=True)
        
        # Add tabs
        tab_add = tabview.add("Add Schedule")
        tab_view = tabview.add("View Schedules")
        
        # Configure tabs
        self.setup_add_schedule_tab(tab_add)
        self.setup_view_schedules_tab(tab_view)
    
    def setup_add_schedule_tab(self, parent):
        # Create a scrollable frame
        add_schedule_scroll = ctk.CTkScrollableFrame(parent)
        add_schedule_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        add_schedule_label = ctk.CTkLabel(
            add_schedule_scroll, 
            text="Add New Schedule", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        add_schedule_label.pack(pady=(0, 20))
        
        # Form layout
        form_frame = ctk.CTkFrame(add_schedule_scroll)
        form_frame.pack(fill="x", expand=True, padx=20, pady=10)
        
        # Train selection
        train_label = ctk.CTkLabel(form_frame, text="Select Train")
        train_label.pack(anchor="w", pady=(10, 5))
        
        train_var = StringVar()
        train_combo = ctk.CTkComboBox(form_frame, variable=train_var, height=35, width=400)
        train_combo.pack(fill="x", pady=(0, 10))
        
        self.load_trains_into_combobox(train_combo)
        
        # Source and destination - side by side
        route_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        route_frame.pack(fill="x", pady=10)
        route_frame.grid_columnconfigure(0, weight=1)
        route_frame.grid_columnconfigure(1, weight=1)
        
        source_label = ctk.CTkLabel(route_frame, text="Source Station")
        source_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        destination_label = ctk.CTkLabel(route_frame, text="Destination Station")
        destination_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        source_entry = ctk.CTkEntry(route_frame, height=35)
        source_entry.grid(row=1, column=0, sticky="ew")
        
        destination_entry = ctk.CTkEntry(route_frame, height=35)
        destination_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Departure date and time - side by side
        departure_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        departure_frame.pack(fill="x", pady=10)
        departure_frame.grid_columnconfigure(0, weight=1)
        departure_frame.grid_columnconfigure(1, weight=1)
        
        departure_date_label = ctk.CTkLabel(departure_frame, text="Departure Date")
        departure_date_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        departure_time_label = ctk.CTkLabel(departure_frame, text="Departure Time (HH:MM)")
        departure_time_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        departure_date_frame = ctk.CTkFrame(departure_frame)
        departure_date_frame.grid(row=1, column=0, sticky="ew")
        
        departure_date_entry = DateEntry(
            departure_date_frame, 
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        departure_date_entry.pack(fill="both", expand=True)
        
        departure_time_entry = ctk.CTkEntry(departure_frame, height=35, placeholder_text="e.g., 14:30")
        departure_time_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Arrival date and time - side by side
        arrival_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        arrival_frame.pack(fill="x", pady=10)
        arrival_frame.grid_columnconfigure(0, weight=1)
        arrival_frame.grid_columnconfigure(1, weight=1)
        
        arrival_date_label = ctk.CTkLabel(arrival_frame, text="Arrival Date")
        arrival_date_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        arrival_time_label = ctk.CTkLabel(arrival_frame, text="Arrival Time (HH:MM)")
        arrival_time_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        arrival_date_frame = ctk.CTkFrame(arrival_frame)
        arrival_date_frame.grid(row=1, column=0, sticky="ew")
        
        arrival_date_entry = DateEntry(
            arrival_date_frame, 
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        arrival_date_entry.pack(fill="both", expand=True)
        
        arrival_time_entry = ctk.CTkEntry(arrival_frame, height=35, placeholder_text="e.g., 18:45")
        arrival_time_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Fares section
        fares_label = ctk.CTkLabel(form_frame, text="Ticket Fares", font=ctk.CTkFont(size=16, weight="bold"))
        fares_label.pack(anchor="w", pady=(20, 10))
        
        # Fares - side by side
        fares_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        fares_frame.pack(fill="x")
        fares_frame.grid_columnconfigure(0, weight=1)
        fares_frame.grid_columnconfigure(1, weight=1)
        fares_frame.grid_columnconfigure(2, weight=1)
        
        fare_sleeper_label = ctk.CTkLabel(fares_frame, text="Sleeper Class (₹)")
        fare_sleeper_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        fare_ac_label = ctk.CTkLabel(fares_frame, text="AC Class (₹)")
        fare_ac_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        fare_general_label = ctk.CTkLabel(fares_frame, text="General Class (₹)")
        fare_general_label.grid(row=0, column=2, sticky="w", pady=(0, 5), padx=(10, 0))
        
        fare_sleeper_entry = ctk.CTkEntry(fares_frame, height=35)
        fare_sleeper_entry.grid(row=1, column=0, sticky="ew")
        
        fare_ac_entry = ctk.CTkEntry(fares_frame, height=35)
        fare_ac_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        fare_general_entry = ctk.CTkEntry(fares_frame, height=35)
        fare_general_entry.grid(row=1, column=2, sticky="ew", padx=(10, 0))
        
        # Button frame
        button_frame = ctk.CTkFrame(add_schedule_scroll, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        # Add Schedule Button
        add_schedule_button = ctk.CTkButton(
            button_frame, 
            text="Add Schedule", 
            command=lambda: self.add_schedule(
                train_var.get(),
                source_entry.get(),
                destination_entry.get(),
                departure_date_entry.get_date(),
                departure_time_entry.get(),
                arrival_date_entry.get_date(),
                arrival_time_entry.get(),
                fare_sleeper_entry.get(),
                fare_ac_entry.get(),
                fare_general_entry.get()
            ),
            height=40
        )
        add_schedule_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Clear form button
        clear_form_button = ctk.CTkButton(
            button_frame, 
            text="Clear Form", 
            command=lambda: [entry.delete(0, 'end') for entry in [
                source_entry, destination_entry, departure_time_entry,
                arrival_time_entry, fare_sleeper_entry, fare_ac_entry, fare_general_entry
            ]],
            height=40,
            fg_color="gray",
            hover_color="gray30"
        )
        clear_form_button.pack(side="right", fill="x", expand=True, padx=(5, 0))
    
    def setup_view_schedules_tab(self, parent):
        # Create a frame for search controls
        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=(10, 5))
        
        search_entry = ctk.CTkEntry(search_frame, height=35, width=200, placeholder_text="Train number, name, or station...")
        search_entry.pack(side="left", padx=5)
        
        search_button = ctk.CTkButton(
            search_frame, 
            text="Search", 
            width=100,
            command=lambda: self.search_schedules(schedules_scroll, search_entry.get())
        )
        search_button.pack(side="left", padx=5)
        
        # Filter options
        filter_label = ctk.CTkLabel(search_frame, text="Filter by date:")
        filter_label.pack(side="left", padx=(20, 5))
        
        filter_date_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        filter_date_frame.pack(side="left")
        
        filter_date_entry = DateEntry(
            filter_date_frame, 
            width=10,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        filter_date_entry.pack(fill="both", expand=True)
        
        filter_button = ctk.CTkButton(
            search_frame, 
            text="Filter", 
            width=80,
            command=lambda: self.filter_schedules_by_date(schedules_scroll, filter_date_entry.get_date())
        )
        filter_button.pack(side="left", padx=5)
        
        reset_button = ctk.CTkButton(
            search_frame, 
            text="Reset", 
            width=80,
            fg_color="gray",
            hover_color="gray30",
            command=lambda: [self.load_schedules(schedules_scroll), search_entry.delete(0, 'end')]
        )
        reset_button.pack(side="left", padx=5)
        
        # Create a scrollable frame for the schedule list
        schedules_scroll = ctk.CTkScrollableFrame(parent)
        schedules_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load schedules
        self.load_schedules(schedules_scroll)
    
    def load_trains_into_combobox(self, combobox):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("SELECT id, train_number, train_name FROM trains ORDER BY train_name")
                trains = cursor.fetchall()
                
                # Format: "Train Number - Train Name"
                train_options = [f"{train['train_number']} - {train['train_name']}" for train in trains]
                
                # Store the train data for later use
                self.train_data = {f"{train['train_number']} - {train['train_name']}": train['id'] for train in trains}
                
                combobox.configure(values=train_options)
                if train_options:
                    combobox.set(train_options[0])
                else:
                    combobox.set("")
            except Exception as e:
                print(f"Error loading trains: {e}")
            finally:
                cursor.close()
                connection.close()
    
    def add_schedule(self, train_option, source, destination, departure_date, departure_time, arrival_date, arrival_time, fare_sleeper, fare_ac, fare_general):
        if not train_option or not source or not destination or not departure_time or not arrival_time or not fare_sleeper or not fare_ac or not fare_general:
            CTkMessagebox(
                title="Error", 
                message="Please fill in all fields",
                icon="cancel"
            )
            return
        
        try:
            # Get train ID from the selected option
            train_id = self.train_data.get(train_option)
            if not train_id:
                CTkMessagebox(
                    title="Error", 
                    message="Invalid train selection",
                    icon="cancel"
                )
                return
            
            # Validate time format (HH:MM)
            time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
            if not time_pattern.match(departure_time) or not time_pattern.match(arrival_time):
                CTkMessagebox(
                    title="Error", 
                    message="Time must be in HH:MM format",
                    icon="cancel"
                )
                return
            
            # Validate fares
            fare_sleeper = float(fare_sleeper)
            fare_ac = float(fare_ac)
            fare_general = float(fare_general)
            
            if fare_sleeper <= 0 or fare_ac <= 0 or fare_general <= 0:
                CTkMessagebox(
                    title="Error", 
                    message="Fares must be positive numbers",
                    icon="cancel"
                )
                return
            
            # Format dates for MySQL
            departure_date_str = departure_date.strftime('%Y-%m-%d')
            arrival_date_str = arrival_date.strftime('%Y-%m-%d')
            
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                
                try:
                    # Insert new schedule
                    cursor.execute(
                        """INSERT INTO schedules 
                           (train_id, source, destination, departure_date, departure_time, 
                            arrival_date, arrival_time, fare_sleeper, fare_ac, fare_general) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (train_id, source, destination, departure_date_str, departure_time, 
                         arrival_date_str, arrival_time, fare_sleeper, fare_ac, fare_general)
                    )
                    
                    connection.commit()
                    CTkMessagebox(
                        title="Success", 
                        message="Schedule added successfully",
                        icon="check"
                    )
                    
                    # Refresh the schedule list in the View Schedules tab
                    for widget in self.app.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkFrame):
                                    for grandchild in child.winfo_children():
                                        if isinstance(grandchild, ctk.CTkTabview):
                                            for tab in grandchild.winfo_children():
                                                for content in tab.winfo_children():
                                                    if isinstance(content, ctk.CTkScrollableFrame):
                                                        self.load_schedules(content)
                                                        return
                except Exception as e:
                    connection.rollback()
                    CTkMessagebox(
                        title="Error", 
                        message=f"Failed to add schedule: {str(e)}",
                        icon="cancel"
                    )
                finally:
                    cursor.close()
                    connection.close()
        except ValueError as e:
            CTkMessagebox(
                title="Error", 
                message=f"Invalid input: {str(e)}",
                icon="cancel"
            )
    
    def search_schedules(self, container, search_term):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        if not search_term:
            self.load_schedules(container)
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Search in train number, train name, source, and destination
                search_pattern = f"%{search_term}%"
                cursor.execute("""
                    SELECT s.*, t.train_number, t.train_name
                    FROM schedules s
                    JOIN trains t ON s.train_id = t.id
                    WHERE t.train_number LIKE %s OR t.train_name LIKE %s OR 
                          s.source LIKE %s OR s.destination LIKE %s
                    ORDER BY s.departure_date, s.departure_time
                """, (search_pattern, search_pattern, search_pattern, search_pattern))
                
                schedules = cursor.fetchall()
                
                if not schedules:
                    no_schedules_label = ctk.CTkLabel(
                        container, 
                        text=f"No schedules found matching '{search_term}'",
                        text_color=("gray50", "gray70")
                    )
                    no_schedules_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Schedules", 
                        command=lambda: self.load_schedules(container),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the schedules
                self.display_schedules(container, schedules)
                
            except Exception as e:
                print(f"Error searching schedules: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error searching schedules: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def filter_schedules_by_date(self, container, filter_date):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        date_str = filter_date.strftime('%Y-%m-%d')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT s.*, t.train_number, t.train_name
                    FROM schedules s
                    JOIN trains t ON s.train_id = t.id
                    WHERE s.departure_date = %s
                    ORDER BY s.departure_time
                """, (date_str,))
                
                schedules = cursor.fetchall()
                
                if not schedules:
                    no_schedules_label = ctk.CTkLabel(
                        container, 
                        text=f"No schedules found for {date_str}",
                        text_color=("gray50", "gray70")
                    )
                    no_schedules_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Schedules", 
                        command=lambda: self.load_schedules(container),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the schedules
                self.display_schedules(container, schedules)
                
            except Exception as e:
                print(f"Error filtering schedules: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error filtering schedules: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def load_schedules(self, container):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT s.*, t.train_number, t.train_name
                    FROM schedules s
                    JOIN trains t ON s.train_id = t.id
                    ORDER BY s.departure_date, s.departure_time
                """)
                schedules = cursor.fetchall()
                
                if not schedules:
                    no_schedules_label = ctk.CTkLabel(
                        container, 
                        text="No schedules found",
                        text_color=("gray50", "gray70")
                    )
                    no_schedules_label.pack(pady=20)
                    return
                
                # Display the schedules
                self.display_schedules(container, schedules)
                
            except Exception as e:
                print(f"Error loading schedules: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error loading schedules: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def display_schedules(self, container, schedules):
        # Headers
        header_frame = ctk.CTkFrame(container, fg_color=("gray80", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=5)
        
        header_columns = [
            ("Train", 150),
            ("Route", 200),
            ("Departure", 120),
            ("Arrival", 120),
            ("Sleeper", 70),
            ("AC", 70),
            ("General", 70),
            ("Status", 80),
            ("Actions", 120)
        ]
        
        for i, (text, width) in enumerate(header_columns):
            header_label = ctk.CTkLabel(
                header_frame, 
                text=text, 
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Schedule rows
        for i, schedule in enumerate(schedules):
            row_frame = ctk.CTkFrame(container)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            train_info = f"{schedule['train_number']}\n{schedule['train_name']}"
            route_info = f"{schedule['source']}\n→ {schedule['destination']}"
            departure_info = f"{schedule['departure_date']}\n{schedule['departure_time']}"
            arrival_info = f"{schedule['arrival_date']}\n{schedule['arrival_time']}"
            
            ctk.CTkLabel(row_frame, text=train_info, width=header_columns[0][1]).grid(row=0, column=0, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=route_info, width=header_columns[1][1]).grid(row=0, column=1, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=departure_info, width=header_columns[2][1]).grid(row=0, column=2, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=arrival_info, width=header_columns[3][1]).grid(row=0, column=3, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"₹{schedule['fare_sleeper']}", width=header_columns[4][1]).grid(row=0, column=4, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"₹{schedule['fare_ac']}", width=header_columns[5][1]).grid(row=0, column=5, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"₹{schedule['fare_general']}", width=header_columns[6][1]).grid(row=0, column=6, padx=5, pady=8, sticky="w")
            
            # Status with color-coding
            status_text = "On Time"
            status_color = "#43a047"  # Green
            
            if 'status' in schedule:
                if schedule['status'] == 'delayed':
                    status_text = f"Delayed ({schedule.get('delay_minutes', 0)}m)"
                    status_color = "#ffb300"  # Amber
                elif schedule['status'] == 'cancelled':
                    status_text = "Cancelled"
                    status_color = "#e53935"  # Red
            
            status_label = ctk.CTkLabel(
                row_frame, 
                text=status_text, 
                text_color=status_color,
                width=header_columns[7][1]
            )
            status_label.grid(row=0, column=7, padx=5, pady=8, sticky="w")
            
            # Action buttons
            action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            action_frame.grid(row=0, column=8, padx=5, pady=5, sticky="w")
            
            # Edit button with icon
            try:
                edit_icon = load_image("assets/edit_icon.png", (16, 16))
                edit_button = ctk.CTkButton(
                    action_frame, 
                    text="",
                    image=edit_icon,
                    width=30,
                    height=30,
                    command=lambda s=schedule: self.show_edit_schedule_dialog(s)
                )
                edit_button.image = edit_icon
            except:
                edit_button = ctk.CTkButton(
                    action_frame, 
                    text="Edit",
                    width=60,
                    height=30,
                    command=lambda s=schedule: self.show_edit_schedule_dialog(s)
                )
            edit_button.grid(row=0, column=0, padx=2)
            
            # Delete button with icon
            try:
                delete_icon = load_image("assets/delete_icon.png", (16, 16))
                delete_button = ctk.CTkButton(
                    action_frame, 
                    text="",
                    image=delete_icon,
                    width=30,
                    height=30,
                    fg_color="#e53935",
                    hover_color="#c62828",
                    command=lambda s=schedule: self.delete_schedule(s['id'], container)
                )
                delete_button.image = delete_icon
            except:
                delete_button = ctk.CTkButton(
                    action_frame, 
                    text="Delete",
                    width=60,
                    height=30,
                    fg_color="#e53935",
                    hover_color="#c62828",
                    command=lambda s=schedule: self.delete_schedule(s['id'], container)
                )
            delete_button.grid(row=0, column=1, padx=2)
    
    def show_edit_schedule_dialog(self, schedule):
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Edit Schedule")
        dialog.geometry("600x650")
        dialog.resizable(True, True)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Create scrollable frame for content
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        header_label = ctk.CTkLabel(
            scroll_frame, 
            text=f"Edit Schedule", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack(pady=(0, 20))
        
        # Train info (non-editable)
        train_frame = ctk.CTkFrame(scroll_frame)
        train_frame.pack(fill="x", pady=10)
        
        train_label = ctk.CTkLabel(train_frame, text="Train:")
        train_label.pack(side="left", padx=(10, 5))
        
        train_value = ctk.CTkLabel(
            train_frame, 
            text=f"{schedule['train_number']} - {schedule['train_name']}",
            font=ctk.CTkFont(weight="bold")
        )
        train_value.pack(side="left")
        
        # Source and destination - side by side
        route_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        route_frame.pack(fill="x", pady=10)
        route_frame.grid_columnconfigure(0, weight=1)
        route_frame.grid_columnconfigure(1, weight=1)
        
        source_label = ctk.CTkLabel(route_frame, text="Source Station")
        source_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        destination_label = ctk.CTkLabel(route_frame, text="Destination Station")
        destination_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        source_entry = ctk.CTkEntry(route_frame, height=35)
        source_entry.insert(0, schedule['source'])
        source_entry.grid(row=1, column=0, sticky="ew")
        
        destination_entry = ctk.CTkEntry(route_frame, height=35)
        destination_entry.insert(0, schedule['destination'])
        destination_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Departure date and time - side by side
        departure_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        departure_frame.pack(fill="x", pady=10)
        departure_frame.grid_columnconfigure(0, weight=1)
        departure_frame.grid_columnconfigure(1, weight=1)
        
        departure_date_label = ctk.CTkLabel(departure_frame, text="Departure Date")
        departure_date_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        departure_time_label = ctk.CTkLabel(departure_frame, text="Departure Time (HH:MM)")
        departure_time_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        departure_date_frame = ctk.CTkFrame(departure_frame)
        departure_date_frame.grid(row=1, column=0, sticky="ew")
        
        departure_date = datetime.strptime(str(schedule['departure_date']), '%Y-%m-%d').date()
        departure_date_entry = DateEntry(
            departure_date_frame, 
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            year=departure_date.year,
            month=departure_date.month,
            day=departure_date.day
        )
        departure_date_entry.pack(fill="both", expand=True)
        
        departure_time_entry = ctk.CTkEntry(departure_frame, height=35)
        departure_time_entry.insert(0, str(schedule['departure_time']))
        departure_time_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Arrival date and time - side by side
        arrival_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        arrival_frame.pack(fill="x", pady=10)
        arrival_frame.grid_columnconfigure(0, weight=1)
        arrival_frame.grid_columnconfigure(1, weight=1)
        
        arrival_date_label = ctk.CTkLabel(arrival_frame, text="Arrival Date")
        arrival_date_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        arrival_time_label = ctk.CTkLabel(arrival_frame, text="Arrival Time (HH:MM)")
        arrival_time_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        arrival_date_frame = ctk.CTkFrame(arrival_frame)
        arrival_date_frame.grid(row=1, column=0, sticky="ew")
        
        arrival_date = datetime.strptime(str(schedule['arrival_date']), '%Y-%m-%d').date()
        arrival_date_entry = DateEntry(
            arrival_date_frame, 
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            year=arrival_date.year,
            month=arrival_date.month,
            day=arrival_date.day
        )
        arrival_date_entry.pack(fill="both", expand=True)
        
        arrival_time_entry = ctk.CTkEntry(arrival_frame, height=35)
        arrival_time_entry.insert(0, str(schedule['arrival_time']))
        arrival_time_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Status section
        status_frame = ctk.CTkFrame(scroll_frame)
        status_frame.pack(fill="x", pady=10)
        
        status_label = ctk.CTkLabel(status_frame, text="Schedule Status")
        status_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        status_options = ["on-time", "delayed", "cancelled"]
        status_var = StringVar(value=schedule.get('status', 'on-time'))
        
        status_option_menu = ctk.CTkOptionMenu(
            status_frame, 
            values=status_options,
            variable=status_var,
            width=200,
            height=35
        )
        status_option_menu.pack(anchor="w", padx=10, pady=(0, 5))
        
        # Delay minutes (only shown when status is delayed)
        delay_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        delay_frame.pack(fill="x", pady=(0, 10), padx=10)
        
        delay_label = ctk.CTkLabel(delay_frame, text="Delay (minutes):")
        delay_label.pack(side="left", padx=(0, 10))
        
        delay_entry = ctk.CTkEntry(delay_frame, width=100, height=35)
        delay_entry.insert(0, str(schedule.get('delay_minutes', 0)))
        delay_entry.pack(side="left")
        
        # Show/hide delay entry based on status selection
        def toggle_delay_visibility(*args):
            if status_var.get() == "delayed":
                delay_frame.pack(fill="x", pady=(0, 10), padx=10)
            else:
                delay_frame.pack_forget()
        
        status_var.trace_add("write", toggle_delay_visibility)
        toggle_delay_visibility()  # Initial visibility
        
        # Fares section
        fares_label = ctk.CTkLabel(scroll_frame, text="Ticket Fares", font=ctk.CTkFont(size=16, weight="bold"))
        fares_label.pack(anchor="w", pady=(20, 10))
        
        # Fares - side by side
        fares_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        fares_frame.pack(fill="x")
        fares_frame.grid_columnconfigure(0, weight=1)
        fares_frame.grid_columnconfigure(1, weight=1)
        fares_frame.grid_columnconfigure(2, weight=1)
        
        fare_sleeper_label = ctk.CTkLabel(fares_frame, text="Sleeper Class (₹)")
        fare_sleeper_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        fare_ac_label = ctk.CTkLabel(fares_frame, text="AC Class (₹)")
        fare_ac_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(10, 0))
        
        fare_general_label = ctk.CTkLabel(fares_frame, text="General Class (₹)")
        fare_general_label.grid(row=0, column=2, sticky="w", pady=(0, 5), padx=(10, 0))
        
        fare_sleeper_entry = ctk.CTkEntry(fares_frame, height=35)
        fare_sleeper_entry.insert(0, str(schedule['fare_sleeper']))
        fare_sleeper_entry.grid(row=1, column=0, sticky="ew")
        
        fare_ac_entry = ctk.CTkEntry(fares_frame, height=35)
        fare_ac_entry.insert(0, str(schedule['fare_ac']))
        fare_ac_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        fare_general_entry = ctk.CTkEntry(fares_frame, height=35)
        fare_general_entry.insert(0, str(schedule['fare_general']))
        fare_general_entry.grid(row=1, column=2, sticky="ew", padx=(10, 0))
        
        # Button frame
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Update Button
        update_button = ctk.CTkButton(
            buttons_frame, 
            text="Update Schedule", 
            command=lambda: self.update_schedule(
                schedule['id'],
                source_entry.get(),
                destination_entry.get(),
                departure_date_entry.get_date(),
                departure_time_entry.get(),
                arrival_date_entry.get_date(),
                arrival_time_entry.get(),
                fare_sleeper_entry.get(),
                fare_ac_entry.get(),
                fare_general_entry.get(),
                status_var.get(),
                delay_entry.get() if status_var.get() == "delayed" else "0",
                dialog
            ),
            height=40
        )
        update_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            command=dialog.destroy,
            fg_color="gray",
            hover_color="gray30",
            height=40
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def update_schedule(self, schedule_id, source, destination, departure_date, departure_time, 
                      arrival_date, arrival_time, fare_sleeper, fare_ac, fare_general, 
                      status, delay_minutes, dialog):
        if not source or not destination or not departure_time or not arrival_time or not fare_sleeper or not fare_ac or not fare_general:
            CTkMessagebox(
                title="Error", 
                message="Please fill in all required fields",
                icon="cancel"
            )
            return
        
        try:
            # Validate time format (HH:MM)
            time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
            if not time_pattern.match(departure_time) or not time_pattern.match(arrival_time):
                CTkMessagebox(
                    title="Error", 
                    message="Time must be in HH:MM format",
                    icon="cancel"
                )
                return
            
            # Validate fares
            fare_sleeper = float(fare_sleeper)
            fare_ac = float(fare_ac)
            fare_general = float(fare_general)
            
            if fare_sleeper <= 0 or fare_ac <= 0 or fare_general <= 0:
                CTkMessagebox(
                    title="Error", 
                    message="Fares must be positive numbers",
                    icon="cancel"
                )
                return
            
            # Validate delay minutes
            delay_minutes = int(delay_minutes) if delay_minutes else 0
            if delay_minutes < 0:
                CTkMessagebox(
                    title="Error", 
                    message="Delay minutes cannot be negative",
                    icon="cancel"
                )
                return
            
            # Format dates for MySQL
            departure_date_str = departure_date.strftime('%Y-%m-%d')
            arrival_date_str = arrival_date.strftime('%Y-%m-%d')
            
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                
                try:
                    # Update schedule
                    cursor.execute(
                        """UPDATE schedules 
                           SET source = %s, destination = %s, departure_date = %s, departure_time = %s, 
                               arrival_date = %s, arrival_time = %s, fare_sleeper = %s, fare_ac = %s, 
                               fare_general = %s, status = %s, delay_minutes = %s
                           WHERE id = %s""",
                        (source, destination, departure_date_str, departure_time, 
                         arrival_date_str, arrival_time, fare_sleeper, fare_ac, fare_general,
                         status, delay_minutes, schedule_id)
                    )
                    
                    connection.commit()
                    dialog.destroy()
                    
                    CTkMessagebox(
                        title="Success", 
                        message="Schedule updated successfully",
                        icon="check"
                    )
                    
                    # Refresh the schedule list
                    for widget in self.app.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkFrame):
                                    for grandchild in child.winfo_children():
                                        if isinstance(grandchild, ctk.CTkTabview):
                                            for tab in grandchild.winfo_children():
                                                for content in tab.winfo_children():
                                                    if isinstance(content, ctk.CTkScrollableFrame):
                                                        self.load_schedules(content)
                except Exception as e:
                    connection.rollback()
                    CTkMessagebox(
                        title="Error", 
                        message=f"Failed to update schedule: {str(e)}",
                        icon="cancel"
                    )
                finally:
                    cursor.close()
                    connection.close()
        except ValueError as e:
            CTkMessagebox(
                title="Error", 
                message=f"Invalid input: {str(e)}",
                icon="cancel"
            )
    
    def delete_schedule(self, schedule_id, container=None):
        # Create a confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.app)
        confirm_dialog.title("Confirm Delete")
        confirm_dialog.geometry("400x200")
        confirm_dialog.resizable(False, False)
        confirm_dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Warning icon
        try:
            warning_img = load_image("assets/warning_icon.png", (64, 64))
            warning_label = ctk.CTkLabel(confirm_dialog, image=warning_img, text="")
            warning_label.image = warning_img
            warning_label.pack(pady=(20, 0))
        except:
            pass
        
        message_label = ctk.CTkLabel(
            confirm_dialog,
            text="Are you sure you want to delete this schedule?\nThis will also delete all associated bookings.",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=20)
        
        buttons_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Delete Button
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            fg_color="#e53935",
            hover_color="#c62828",
            command=lambda: self.perform_delete_schedule(schedule_id, container, confirm_dialog),
            height=35
        )
        delete_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            fg_color="gray",
            hover_color="gray30",
            command=confirm_dialog.destroy,
            height=35
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def perform_delete_schedule(self, schedule_id, container, dialog):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Delete schedule (cascading will handle related bookings)
                cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
                connection.commit()
                
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success", 
                    message="Schedule deleted successfully",
                    icon="check"
                )
                
                # Refresh the schedule list
                if container:
                    self.load_schedules(container)
            except Exception as e:
                connection.rollback()
                dialog.destroy()
                CTkMessagebox(
                    title="Error", 
                    message=f"Failed to delete schedule: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_admin_bookings_tab(self):
        # Similar pattern to other admin tabs
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame with sidebar
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Add sidebar (same as in other tabs)
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Bookings" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Bookings" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Manage Bookings", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Bookings content
        bookings_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        bookings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create a tabview for bookings
        tabview = ctk.CTkTabview(bookings_frame)
        tabview.pack(fill="both", expand=True)
        
        # Add tabs
        tab_all = tabview.add("All Bookings")
        tab_today = tabview.add("Today's Bookings")
        tab_cancelled = tabview.add("Cancelled Bookings")
        
        # Setup each tab
        self.setup_bookings_tab(tab_all, "all")
        self.setup_bookings_tab(tab_today, "today")
        self.setup_bookings_tab(tab_cancelled, "cancelled")
    
    def setup_bookings_tab(self, parent, mode="all"):
        # Search and filter frame
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(controls_frame, text="Search by PNR or Name:")
        search_label.pack(side="left", padx=10)
        
        search_entry = ctk.CTkEntry(controls_frame, width=200, height=35)
        search_entry.pack(side="left", padx=5)
        
        search_button = ctk.CTkButton(
            controls_frame, 
            text="Search",
            command=lambda: self.search_bookings(bookings_scroll, search_entry.get(), mode),
            width=80,
            height=35
        )
        search_button.pack(side="left", padx=5)
        
        if mode == "all":
            date_label = ctk.CTkLabel(controls_frame, text="Filter by date:")
            date_label.pack(side="left", padx=(20, 5))
            
            date_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
            date_frame.pack(side="left")
            
            date_entry = DateEntry(
                date_frame, 
                width=10,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                date_pattern='yyyy-mm-dd'
            )
            date_entry.pack(fill="both", expand=True)
            
            filter_button = ctk.CTkButton(
                controls_frame, 
                text="Filter",
                command=lambda: self.filter_bookings_by_date(bookings_scroll, date_entry.get_date()),
                width=80,
                height=35
            )
            filter_button.pack(side="left", padx=5)
        
        reset_button = ctk.CTkButton(
            controls_frame, 
            text="Reset",
            command=lambda: self.load_bookings(bookings_scroll, mode),
            width=80,
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        reset_button.pack(side="left", padx=5)
        
        # Export button (on the right)
        export_button = ctk.CTkButton(
            controls_frame,
            text="Export to CSV",
            command=lambda: self.export_bookings_to_csv(mode),
            width=120,
            height=35,
            fg_color=("green", "dark green"),
            hover_color=("darkgreen", "green4")
        )
        export_button.pack(side="right", padx=10)
        
        # Create a scrollable frame for the bookings list
        bookings_scroll = ctk.CTkScrollableFrame(parent)
        bookings_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load bookings
        self.load_bookings(bookings_scroll, mode)
    
    def load_bookings(self, container, mode="all"):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                query = """
                    SELECT 
                        b.id, b.pnr, u.name as user_name, u.email as user_email, b.booking_date, 
                        b.total_fare, b.status, b.payment_method, t.train_number, t.train_name, 
                        s.source, s.destination, s.departure_date, s.departure_time
                    FROM 
                        bookings b
                    JOIN 
                        users u ON b.user_id = u.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                """
                
                if mode == "today":
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    query += " WHERE DATE(b.booking_date) = %s"
                    params = (current_date,)
                elif mode == "cancelled":
                    query += " WHERE b.status = 'cancelled'"
                    params = ()
                else:
                    params = ()
                
                query += " ORDER BY b.booking_date DESC"
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_bookings_label = ctk.CTkLabel(
                        container, 
                        text=f"No bookings found",
                        text_color=("gray50", "gray70")
                    )
                    no_bookings_label.pack(pady=20)
                    return
                
                # Display the bookings
                self.display_bookings(container, bookings)
                
            except Exception as e:
                print(f"Error loading bookings: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error loading bookings: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def search_bookings(self, container, search_term, mode="all"):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        if not search_term:
            self.load_bookings(container, mode)
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Search by PNR or user name
                search_pattern = f"%{search_term}%"
                
                query = """
                    SELECT 
                        b.id, b.pnr, u.name as user_name, u.email as user_email, b.booking_date, 
                        b.total_fare, b.status, b.payment_method, t.train_number, t.train_name, 
                        s.source, s.destination, s.departure_date, s.departure_time
                    FROM 
                        bookings b
                    JOIN 
                        users u ON b.user_id = u.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        b.pnr LIKE %s OR u.name LIKE %s
                """
                
                params = [search_pattern, search_pattern]
                
                if mode == "today":
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    query += " AND DATE(b.booking_date) = %s"
                    params.append(current_date)
                elif mode == "cancelled":
                    query += " AND b.status = 'cancelled'"
                
                query += " ORDER BY b.booking_date DESC"
                
                cursor.execute(query, params)
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_bookings_label = ctk.CTkLabel(
                        container, 
                        text=f"No bookings found matching '{search_term}'",
                        text_color=("gray50", "gray70")
                    )
                    no_bookings_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Bookings", 
                        command=lambda: self.load_bookings(container, mode),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the bookings
                self.display_bookings(container, bookings)
                
            except Exception as e:
                print(f"Error searching bookings: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error searching bookings: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def filter_bookings_by_date(self, container, filter_date):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        date_str = filter_date.strftime('%Y-%m-%d')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT 
                        b.id, b.pnr, u.name as user_name, u.email as user_email, b.booking_date, 
                        b.total_fare, b.status, b.payment_method, t.train_number, t.train_name, 
                        s.source, s.destination, s.departure_date, s.departure_time
                    FROM 
                        bookings b
                    JOIN 
                        users u ON b.user_id = u.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        DATE(b.booking_date) = %s
                    ORDER BY 
                        b.booking_date DESC
                """, (date_str,))
                
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_bookings_label = ctk.CTkLabel(
                        container, 
                        text=f"No bookings found for {date_str}",
                        text_color=("gray50", "gray70")
                    )
                    no_bookings_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Bookings", 
                        command=lambda: self.load_bookings(container, "all"),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the bookings
                self.display_bookings(container, bookings)
                
            except Exception as e:
                print(f"Error filtering bookings: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error filtering bookings: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def display_bookings(self, container, bookings):
        for i, booking in enumerate(bookings):
            # Create a card for each booking
            booking_card = ctk.CTkFrame(container)
            booking_card.pack(fill="x", pady=5, padx=5)
            
            # Main info
            info_frame = ctk.CTkFrame(booking_card, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=(10, 5))
            
            # Left column: PNR, user info, date
            left_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            left_frame.pack(side="left", fill="y", anchor="w")
            
            # PNR with status badge
            pnr_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
            pnr_frame.pack(anchor="w", fill="x")
            
            pnr_label = ctk.CTkLabel(
                pnr_frame, 
                text=f"PNR: {booking['pnr']}", 
                font=ctk.CTkFont(size=14, weight="bold")
            )
            pnr_label.pack(side="left")
            
            status_color = "#43a047" if booking['status'] == "confirmed" else "#e53935"
            status_text = "Confirmed" if booking['status'] == "confirmed" else "Cancelled"
            
            status_badge = ctk.CTkLabel(
                pnr_frame,
                text=status_text,
                text_color="white",
                fg_color=status_color,
                corner_radius=5,
                width=80,
                height=20
            )
            status_badge.pack(side="left", padx=10)
            
            # User info
            user_label = ctk.CTkLabel(
                left_frame, 
                text=f"Booked by: {booking['user_name']} ({booking['user_email']})"
            )
            user_label.pack(anchor="w", pady=(5, 0))
            
            date_label = ctk.CTkLabel(
                left_frame, 
                text=f"Booking Date: {booking['booking_date']}"
            )
            date_label.pack(anchor="w", pady=(5, 0))
            
            # Payment method
            payment_method_text = booking.get('payment_method', 'Not specified').replace('_', ' ').title()
            payment_label = ctk.CTkLabel(
                left_frame, 
                text=f"Payment: {payment_method_text}"
            )
            payment_label.pack(anchor="w", pady=(5, 0))
            
            # Right column: Total fare
            right_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            right_frame.pack(side="right", fill="y", anchor="e")
            
            fare_label = ctk.CTkLabel(
                right_frame, 
                text=f"Total Fare:", 
                font=ctk.CTkFont(size=12)
            )
            fare_label.pack(anchor="e")
            
            fare_value = ctk.CTkLabel(
                right_frame, 
                text=format_currency(booking['total_fare']), 
                font=ctk.CTkFont(size=16, weight="bold")
            )
            fare_value.pack(anchor="e")
            
            # Train and journey details
            train_frame = ctk.CTkFrame(booking_card, fg_color="transparent")
            train_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            train_label = ctk.CTkLabel(
                train_frame,
                text=f"Train: {booking['train_number']} - {booking['train_name']}",
                font=ctk.CTkFont(size=13)
            )
            train_label.pack(anchor="w", pady=(5, 0))
            
            journey_label = ctk.CTkLabel(
                train_frame,
                text=f"Journey: {booking['source']} → {booking['destination']} | Departure: {booking['departure_date']} {booking['departure_time']}"
            )
            journey_label.pack(anchor="w", pady=(5, 0))
            
            # Actions
            actions_frame = ctk.CTkFrame(booking_card, fg_color="transparent")
            actions_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # View details button
            view_details_button = ctk.CTkButton(
                actions_frame,
                text="View Details",
                command=lambda b=booking: self.show_booking_details(b),
                width=120,
                height=30
            )
            view_details_button.pack(side="left", padx=(0, 10))
            
            # Change status button (disabled if already cancelled)
            if booking['status'] == 'confirmed':
                cancel_button = ctk.CTkButton(
                    actions_frame,
                    text="Cancel Booking",
                    command=lambda b=booking: self.cancel_booking(b, container),
                    width=120,
                    height=30,
                    fg_color="#e53935",
                    hover_color="#c62828"
                )
                cancel_button.pack(side="left", padx=(0, 10))
    
    def show_booking_details(self, booking):
        # Fetch detailed information including passengers
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get passengers for this booking
                cursor.execute("""
                    SELECT * FROM passengers WHERE booking_id = %s
                """, (booking['id'],))
                
                passengers = cursor.fetchall()
                
                # Create a dialog window
                dialog = ctk.CTkToplevel(self.app)
                dialog.title(f"Booking Details - PNR: {booking['pnr']}")
                dialog.geometry("600x500")
                dialog.resizable(False, False)
                dialog.grab_set()  # Make the dialog modal
                
                # Center the dialog
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() // 2) - (width // 2)
                y = (dialog.winfo_screenheight() // 2) - (height // 2)
                dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                
                # Create a scrollable frame
                scroll_frame = ctk.CTkScrollableFrame(dialog)
                scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                # PNR and status
                header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                header_frame.pack(fill="x", pady=(0, 10))
                
                pnr_label = ctk.CTkLabel(
                    header_frame, 
                    text=f"PNR: {booking['pnr']}", 
                    font=ctk.CTkFont(size=20, weight="bold")
                )
                pnr_label.pack(side="left")
                
                status_color = "#43a047" if booking['status'] == "confirmed" else "#e53935"
                status_text = "Confirmed" if booking['status'] == "confirmed" else "Cancelled"
                
                status_badge = ctk.CTkLabel(
                    header_frame,
                    text=status_text,
                    text_color="white",
                    fg_color=status_color,
                    corner_radius=5,
                    width=100,
                    height=25
                )
                status_badge.pack(side="right")
                
                # Booking information
                info_frame = ctk.CTkFrame(scroll_frame)
                info_frame.pack(fill="x", pady=10)
                
                # Grid layout for booking details
                info_frame.grid_columnconfigure(0, weight=1)
                info_frame.grid_columnconfigure(1, weight=1)
                
                info_labels = [
                    ("Booking Date:", booking['booking_date']),
                    ("Booked By:", f"{booking['user_name']} ({booking['user_email']})"),
                    ("Train:", f"{booking['train_number']} - {booking['train_name']}"),
                    ("From:", booking['source']),
                    ("To:", booking['destination']),
                    ("Departure:", f"{booking['departure_date']} {booking['departure_time']}"),
                    ("Total Fare:", format_currency(booking['total_fare'])),
                    ("Payment Method:", booking.get('payment_method', 'Not specified').replace('_', ' ').title())
                ]
                
                for i, (label, value) in enumerate(info_labels):
                    row = i // 2
                    col = i % 2
                    
                    label_widget = ctk.CTkLabel(
                        info_frame, 
                        text=label,
                        font=ctk.CTkFont(weight="bold")
                    )
                    label_widget.grid(row=row, column=col*2, padx=(10, 5), pady=5, sticky="w")
                    
                    value_widget = ctk.CTkLabel(info_frame, text=str(value))
                    value_widget.grid(row=row, column=col*2+1, padx=(0, 10), pady=5, sticky="w")
                
                # Passengers list
                passengers_label = ctk.CTkLabel(
                    scroll_frame, 
                    text="Passenger Details", 
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                passengers_label.pack(anchor="w", pady=(20, 10))
                
                if not passengers:
                    no_passengers_label = ctk.CTkLabel(
                        scroll_frame, 
                        text="No passenger details available",
                        text_color=("gray50", "gray70")
                    )
                    no_passengers_label.pack(pady=10)
                else:
                    # Create frame for passenger headers
                    passenger_header = ctk.CTkFrame(scroll_frame, fg_color=("gray80", "gray25"))
                    passenger_header.pack(fill="x", pady=(0, 5))
                    
                    # Create header labels
                    ctk.CTkLabel(passenger_header, text="Name", width=150, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Age", width=50, font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Gender", width=70, font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Class", width=80, font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Seat", width=80, font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=5, pady=5, sticky="w")
                    
                    # Add each passenger to the list
                    for j, passenger in enumerate(passengers):
                        passenger_frame = ctk.CTkFrame(scroll_frame)
                        passenger_frame.pack(fill="x", pady=1)
                        
                        # Format class and gender values to be more readable
                        seat_class = passenger['seat_class'].capitalize()
                        gender = passenger['gender'].capitalize()
                        
                        ctk.CTkLabel(passenger_frame, text=passenger['name'], width=150).grid(row=0, column=0, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=str(passenger['age']), width=50).grid(row=0, column=1, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=gender, width=70).grid(row=0, column=2, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=seat_class, width=80).grid(row=0, column=3, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=passenger['seat_number'] or "Not assigned", width=80).grid(row=0, column=4, padx=5, pady=5, sticky="w")
                
                # Button to close dialog
                close_button = ctk.CTkButton(
                    dialog,
                    text="Close",
                    command=dialog.destroy,
                    height=35
                )
                close_button.pack(pady=(0, 20), padx=20, fill="x")
                
            except Exception as e:
                print(f"Error fetching booking details: {e}")
                CTkMessagebox(
                    title="Error",
                    message=f"Error fetching booking details: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def cancel_booking(self, booking, container):
        # Create a confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.app)
        confirm_dialog.title("Confirm Cancellation")
        confirm_dialog.geometry("400x200")
        confirm_dialog.resizable(False, False)
        confirm_dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Warning icon
        try:
            warning_img = load_image("assets/warning_icon.png", (64, 64))
            warning_label = ctk.CTkLabel(confirm_dialog, image=warning_img, text="")
            warning_label.image = warning_img
            warning_label.pack(pady=(20, 0))
        except:
            pass
        
        message_label = ctk.CTkLabel(
            confirm_dialog,
            text=f"Are you sure you want to cancel this booking?\nPNR: {booking['pnr']}\nThis action cannot be undone.",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=20)
        
        buttons_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel Booking",
            fg_color="#e53935",
            hover_color="#c62828",
            command=lambda: self.perform_cancel_booking(booking['id'], container, confirm_dialog),
            height=35
        )
        cancel_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Keep Button
        keep_button = ctk.CTkButton(
            buttons_frame,
            text="Keep Booking",
            command=confirm_dialog.destroy,
            height=35
        )
        keep_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def perform_cancel_booking(self, booking_id, container, dialog):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Update booking status to cancelled
                cursor.execute(
                    "UPDATE bookings SET status = 'cancelled' WHERE id = %s",
                    (booking_id,)
                )
                
                connection.commit()
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success",
                    message="Booking has been cancelled successfully",
                    icon="check"
                )
                
                # Refresh the bookings list
                self.load_bookings(container)
                
            except Exception as e:
                connection.rollback()
                dialog.destroy()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to cancel booking: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def export_bookings_to_csv(self, mode="all"):
        import csv
        from tkinter import filedialog
        
        # Ask user where to save the CSV file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Bookings Report"
        )
        
        if not file_path:
            return  # User cancelled
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                query = """
                    SELECT 
                        b.pnr, u.name as user_name, u.email as user_email, b.booking_date, 
                        b.total_fare, b.status, b.payment_method, t.train_number, t.train_name, 
                        s.source, s.destination, s.departure_date, s.departure_time
                    FROM 
                        bookings b
                    JOIN 
                        users u ON b.user_id = u.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                """
                
                if mode == "today":
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    query += " WHERE DATE(b.booking_date) = %s"
                    params = (current_date,)
                elif mode == "cancelled":
                    query += " WHERE b.status = 'cancelled'"
                    params = ()
                else:
                    params = ()
                
                query += " ORDER BY b.booking_date DESC"
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                bookings = cursor.fetchall()
                
                if bookings:
                    # Write to CSV
                    with open(file_path, mode='w', newline='') as csv_file:
                        fieldnames = bookings[0].keys()
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        for booking in bookings:
                            writer.writerow(booking)
                    
                    CTkMessagebox(
                        title="Success",
                        message=f"Bookings successfully exported to {file_path}",
                        icon="check"
                    )
                else:
                    CTkMessagebox(
                        title="No Data",
                        message="No bookings data to export",
                        icon="warning"
                    )
                
            except Exception as e:
                CTkMessagebox(
                    title="Export Error",
                    message=f"Failed to export bookings: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_admin_revenue_tab(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Add sidebar (same as in other tabs)
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator and admin info (same as other tabs)
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons (same as other tabs, but highlight "Revenue")
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Revenue" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Revenue" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Revenue Analytics", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Revenue content frame - This will contain all revenue content
        revenue_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        revenue_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === NON-SCROLLABLE SECTION ===
        # Date range filter - Fixed at top
        filter_frame = ctk.CTkFrame(revenue_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        filter_label = ctk.CTkLabel(filter_frame, text="Select Date Range:")
        filter_label.pack(side="left", padx=10)
        
        # From date
        from_label = ctk.CTkLabel(filter_frame, text="From:")
        from_label.pack(side="left", padx=(20, 5))
        
        from_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        from_frame.pack(side="left")
        
        # Calculate date 30 days ago
        from_date = (datetime.now() - timedelta(days=30)).date()
        from_date_entry = DateEntry(
            from_frame, 
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            year=from_date.year,
            month=from_date.month,
            day=from_date.day
        )
        from_date_entry.pack(fill="both", expand=True)
        
        # To date
        to_label = ctk.CTkLabel(filter_frame, text="To:")
        to_label.pack(side="left", padx=(20, 5))
        
        to_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        to_frame.pack(side="left")
        
        to_date = datetime.now().date()
        to_date_entry = DateEntry(
            to_frame, 
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            year=to_date.year,
            month=to_date.month,
            day=to_date.day
        )
        to_date_entry.pack(fill="both", expand=True)
        
        # Apply filter button
        apply_filter_button = ctk.CTkButton(
            filter_frame,
            text="Apply",
            width=100,
            height=30,
            command=lambda: self.update_revenue_analytics_with_scroll(
                summary_cards_frame,
                scrollable_content,
                from_date_entry.get_date(),
                to_date_entry.get_date()
            )
        )
        apply_filter_button.pack(side="left", padx=20)
        
        # Export report button
        export_button = ctk.CTkButton(
            filter_frame,
            text="Export Report",
            command=lambda: self.export_revenue_report(
                from_date_entry.get_date(),
                to_date_entry.get_date()
            ),
            width=120,
            height=30,
            fg_color=("green", "dark green"),
            hover_color=("darkgreen", "green4")
        )
        export_button.pack(side="right", padx=20)
        
        # Summary cards - Fixed at top
        summary_cards_frame = ctk.CTkFrame(revenue_frame, fg_color="transparent")
        summary_cards_frame.pack(fill="x", pady=10)
        
        # === SCROLLABLE SECTION ===
        # Create a scrollable frame for charts and tables
        scrollable_content = ctk.CTkScrollableFrame(revenue_frame)
        scrollable_content.pack(fill="both", expand=True, pady=(10, 0))

        # Load initial data for the default date range (last 30 days)
        self.update_revenue_analytics_with_scroll(
            summary_cards_frame,
            scrollable_content,
            from_date,
            to_date
        )

    def update_revenue_analytics_with_scroll(self, summary_frame, scrollable_content, from_date, to_date):
        # Clear frames
        for widget in summary_frame.winfo_children():
            widget.destroy()
        
        for widget in scrollable_content.winfo_children():
            widget.destroy()
        
        # Format dates for database queries
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get total revenue and booking counts
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN b.status = 'confirmed' THEN b.total_fare ELSE 0 END) as total_revenue,
                        COUNT(CASE WHEN b.status = 'confirmed' THEN 1 ELSE NULL END) as confirmed_bookings,
                        COUNT(CASE WHEN b.status = 'cancelled' THEN 1 ELSE NULL END) as cancelled_bookings,
                        COUNT(*) as total_bookings
                    FROM 
                        bookings b
                    WHERE 
                        DATE(b.booking_date) BETWEEN %s AND %s
                """, (from_date_str, to_date_str))
                
                summary_data = cursor.fetchone()
                
                # Get revenue by class
                cursor.execute("""
                    SELECT 
                        p.seat_class,
                        SUM(CASE WHEN b.status = 'confirmed' THEN b.total_fare ELSE 0 END) as revenue,
                        COUNT(*) as passengers
                    FROM 
                        passengers p
                    JOIN 
                        bookings b ON p.booking_id = b.id
                    WHERE 
                        DATE(b.booking_date) BETWEEN %s AND %s
                    GROUP BY 
                        p.seat_class
                """, (from_date_str, to_date_str))
                
                class_revenue_data = cursor.fetchall()
                
                # Get daily revenue data for the chart
                cursor.execute("""
                    SELECT 
                        DATE(b.booking_date) as date,
                        SUM(CASE WHEN b.status = 'confirmed' THEN b.total_fare ELSE 0 END) as revenue,
                        COUNT(*) as bookings
                    FROM 
                        bookings b
                    WHERE 
                        DATE(b.booking_date) BETWEEN %s AND %s
                    GROUP BY 
                        DATE(b.booking_date)
                    ORDER BY 
                        date
                """, (from_date_str, to_date_str))
                
                daily_revenue_data = cursor.fetchall()
                
                # Get route-wise revenue data
                cursor.execute("""
                    SELECT 
                        s.source, s.destination,
                        SUM(CASE WHEN b.status = 'confirmed' THEN b.total_fare ELSE 0 END) as revenue,
                        COUNT(*) as bookings
                    FROM 
                        bookings b
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    WHERE 
                        DATE(b.booking_date) BETWEEN %s AND %s
                    GROUP BY 
                        s.source, s.destination
                    ORDER BY 
                        revenue DESC
                    LIMIT 10
                """, (from_date_str, to_date_str))
                
                route_revenue_data = cursor.fetchall()
                
                # Get revenue by payment method
                cursor.execute("""
                    SELECT 
                        IFNULL(b.payment_method, 'not specified') as payment_method,
                        SUM(CASE WHEN b.status = 'confirmed' THEN b.total_fare ELSE 0 END) as revenue,
                        COUNT(*) as bookings
                    FROM 
                        bookings b
                    WHERE 
                        DATE(b.booking_date) BETWEEN %s AND %s
                    GROUP BY 
                        b.payment_method
                """, (from_date_str, to_date_str))
                
                payment_revenue_data = cursor.fetchall()
                
                # Create summary cards (non-scrollable)
                self.create_revenue_summary_cards(summary_frame, summary_data)
                
                # Create charts and tables (scrollable)
                
                # Daily Revenue Chart
                daily_chart_frame = ctk.CTkFrame(scrollable_content)
                daily_chart_frame.pack(fill="x", pady=10)
                self.create_daily_revenue_chart(daily_chart_frame, daily_revenue_data)
                
                # Class Revenue Chart
                class_chart_frame = ctk.CTkFrame(scrollable_content)
                class_chart_frame.pack(fill="x", pady=10)
                self.create_class_revenue_chart(class_chart_frame, class_revenue_data)
                
                # Revenue breakdown table
                table_frame = ctk.CTkFrame(scrollable_content)
                table_frame.pack(fill="x", pady=10)
                self.create_revenue_table(table_frame, route_revenue_data, payment_revenue_data)
                
            except Exception as e:
                print(f"Error loading revenue data: {e}")
                error_label = ctk.CTkLabel(
                    summary_frame, 
                    text=f"Error loading revenue data: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def create_revenue_summary_cards(self, parent, data):
        # Create a frame to hold the cards
        cards_container = ctk.CTkFrame(parent, fg_color="transparent")
        cards_container.pack(fill="x")
        
        # Configure grid layout for cards
        cards_container.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Card data
        total_revenue = data.get('total_revenue') or 0
        confirmed_bookings = data.get('confirmed_bookings') or 0
        cancelled_bookings = data.get('cancelled_bookings') or 0
        total_bookings = data.get('total_bookings') or 0
        
        # Calculate cancellation rate
        cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
        avg_booking_value = (total_revenue / confirmed_bookings) if confirmed_bookings > 0 else 0
        
        # Create the cards
        metrics = [
            ("Total Revenue", format_currency(total_revenue), "assets/revenue_icon.png", THEME_COLORS[self.current_theme]["primary"]),
            ("Confirmed Bookings", f"{confirmed_bookings}", "assets/booking_icon.png", THEME_COLORS[self.current_theme]["success"]),
            ("Avg. Booking Value", format_currency(avg_booking_value), "assets/ticket_icon.png", THEME_COLORS[self.current_theme]["accent"]),
            ("Cancellation Rate", f"{cancellation_rate:.1f}%", "assets/cancel_icon.png", THEME_COLORS[self.current_theme]["danger"])
        ]
        
        for i, (title, value, icon_path, card_color) in enumerate(metrics):
            card = ctk.CTkFrame(cards_container)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            
            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(fill="both", expand=True, padx=15, pady=15)
            
            # Icon and title
            header_frame = ctk.CTkFrame(card_content, fg_color="transparent")
            header_frame.pack(fill="x", pady=(0, 10))
            
            try:
                icon_img = load_image(icon_path, (24, 24))
                icon_label = ctk.CTkLabel(header_frame, image=icon_img, text="")
                icon_label.image = icon_img
                icon_label.pack(side="left", padx=(0, 5))
            except:
                pass
                
            title_label = ctk.CTkLabel(
                header_frame, 
                text=title,
                font=ctk.CTkFont(size=14)
            )
            title_label.pack(side="left")
            
            # Value
            value_label = ctk.CTkLabel(
                card_content, 
                text=str(value),
                font=ctk.CTkFont(size=20, weight="bold")
            )
            value_label.pack(pady=10)
            
            # Add a color indicator
            indicator = ctk.CTkFrame(card, fg_color=card_color, height=5)
            indicator.pack(side="bottom", fill="x")
    
    def create_daily_revenue_chart(self, parent, data):
        # Create title
        title_label = ctk.CTkLabel(
            parent, 
            text="Daily Revenue Trend", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 0), padx=10, anchor="w")
        
        # Extract data for chart
        dates = []
        revenues = []
        
        if data:
            for entry in data:
                date_str = entry['date'].strftime('%d/%m/%Y') if isinstance(entry['date'], datetime) else entry['date']
                dates.append(date_str)
                revenues.append(float(entry['revenue']) if entry['revenue'] else 0)
        else:
            # Add dummy data if no data is available
            current_date = datetime.now()
            for i in range(7):
                date = (current_date - timedelta(days=i)).strftime('%d/%m/%Y')
                dates.insert(0, date)
                revenues.insert(0, 0)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        
        # Set background color to match CTk theme
        bg_color = "white" if self.current_theme == "light" else "#2d2d2d"
        text_color = "black" if self.current_theme == "light" else "white"
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Create line chart
        ax.plot(dates, revenues, marker='o', linewidth=2, color=THEME_COLORS[self.current_theme]["primary"])
        
        # Adjust x-axis labels dynamically based on the date range
        if len(dates) > 10:
            ax.set_xticks(dates[::len(dates) // 10])  # Show only a subset of labels
        plt.xticks(rotation=45, ha="right")
        
        # Add data labels for important points (e.g., min and max)
        if revenues:
            max_idx = revenues.index(max(revenues))
            min_idx = revenues.index(min(revenues))
            ax.annotate(f"Max: ₹{int(revenues[max_idx]):,}",
                        xy=(dates[max_idx], revenues[max_idx]),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        color=text_color,
                        fontsize=8)
            ax.annotate(f"Min: ₹{int(revenues[min_idx]):,}",
                        xy=(dates[min_idx], revenues[min_idx]),
                        xytext=(0, -15),
                        textcoords='offset points',
                        ha='center',
                        color=text_color,
                        fontsize=8)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'₹{int(x):,}'))
        
        # Customize chart
        ax.set_xlabel('Date', color=text_color)
        ax.set_ylabel('Revenue (₹)', color=text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('gray')
        ax.spines['left'].set_color('gray')
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        ax.yaxis.grid(True, linestyle='--', alpha=0.7, color='gray')
        
        plt.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_class_revenue_chart(self, parent, data):
        # Create title
        title_label = ctk.CTkLabel(
            parent, 
            text="Revenue by Travel Class", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 0), padx=10, anchor="w")
        
        # Extract data for chart
        classes = []
        revenues = []
        passengers = []
        
        if data:
            for entry in data:
                classes.append(entry['seat_class'].capitalize())
                revenues.append(float(entry['revenue']) if entry['revenue'] else 0)
                passengers.append(int(entry['passengers']) if entry['passengers'] else 0)
        else:
            # Add dummy data if no data is available
            classes = ['Sleeper', 'AC', 'General']
            revenues = [0, 0, 0]
            passengers = [0, 0, 0]
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        
        # Set background color to match CTk theme
        bg_color = "white" if self.current_theme == "light" else "#2d2d2d"
        text_color = "black" if self.current_theme == "light" else "white"
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Create bar chart
        x = range(len(classes))
        bars = ax.bar(
            x, revenues,
            color=[
                THEME_COLORS[self.current_theme]["primary"],
                THEME_COLORS[self.current_theme]["secondary"],
                THEME_COLORS[self.current_theme]["accent"]
            ]
        )
        
        # Set x-axis ticks
        ax.set_xticks(x)
        ax.set_xticklabels(classes)
        
        # Add data labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + 0.1,
                f"₹{int(height):,}",
                ha='center', 
                va='bottom',
                color=text_color,
                fontsize=8
            )
        
        # Add passenger count as text on bars
        for i, p in enumerate(passengers):
            ax.text(
                i,
                bars[i].get_height() / 2,
                f"{p} pax",
                ha='center', 
                va='center',
                color='white',
                fontweight='bold',
                fontsize=8
            )
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'₹{int(x):,}'))
        
        # Customize chart
        ax.set_xlabel('Travel Class', color=text_color)
        ax.set_ylabel('Revenue (₹)', color=text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('gray')
        ax.spines['left'].set_color('gray')
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        ax.yaxis.grid(True, linestyle='--', alpha=0.7, color='gray')
        
        plt.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_revenue_table(self, parent, route_data, payment_data):
        # Create notebook for tables
        tabview = ctk.CTkTabview(parent)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        tab_routes = tabview.add("Revenue by Routes")
        tab_payment = tabview.add("Revenue by Payment Method")
        
        # Routes table
        routes_label = ctk.CTkLabel(
            tab_routes, 
            text="Top Routes by Revenue", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        routes_label.pack(pady=(10, 10), padx=10, anchor="w")
        
        # Create routes table
        routes_frame = ctk.CTkFrame(tab_routes)
        routes_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Headers
        header_frame = ctk.CTkFrame(routes_frame, fg_color=("gray80", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=5)
        
        header_cols = [
            ("Route", 300),
            ("Revenue", 150),
            ("Bookings", 100),
            ("Avg. Ticket Value", 150)
        ]
        
        for i, (text, width) in enumerate(header_cols):
            ctk.CTkLabel(
                header_frame, 
                text=text, 
                font=ctk.CTkFont(weight="bold"),
                width=width
            ).grid(row=0, column=i, padx=10, pady=5)
        
        # Routes data
        routes_scroll = ctk.CTkScrollableFrame(routes_frame, fg_color="transparent")
        routes_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        if route_data:
            for i, route in enumerate(route_data):
                route_frame = ctk.CTkFrame(routes_scroll)
                route_frame.pack(fill="x", pady=2)
                
                route_name = f"{route['source']} → {route['destination']}"
                revenue = float(route['revenue']) if route['revenue'] else 0
                bookings = int(route['bookings']) if route['bookings'] else 0
                avg_value = revenue / bookings if bookings > 0 else 0
                
                ctk.CTkLabel(route_frame, text=route_name, width=header_cols[0][1], anchor="w").grid(row=0, column=0, padx=10, pady=5)
                ctk.CTkLabel(route_frame, text=format_currency(revenue), width=header_cols[1][1]).grid(row=0, column=1, padx=10, pady=5)
                ctk.CTkLabel(route_frame, text=str(bookings), width=header_cols[2][1]).grid(row=0, column=2, padx=10, pady=5)
                ctk.CTkLabel(route_frame, text=format_currency(avg_value), width=header_cols[3][1]).grid(row=0, column=3, padx=10, pady=5)
        else:
            # No data message
            no_data_label = ctk.CTkLabel(
                routes_scroll, 
                text="No route revenue data available for the selected period", 
                text_color=("gray50", "gray70")
            )
            no_data_label.pack(pady=20)
        
        # Payment methods table
        payment_label = ctk.CTkLabel(
            tab_payment, 
            text="Revenue by Payment Method", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        payment_label.pack(pady=(10, 10), padx=10, anchor="w")
        
        # Create payment table
        payment_frame = ctk.CTkFrame(tab_payment)
        payment_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Headers
        header_frame = ctk.CTkFrame(payment_frame, fg_color=("gray80", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=5)
        
        payment_cols = [
            ("Payment Method", 300),
            ("Revenue", 150),
            ("Bookings", 100),
            ("Percentage", 150)
        ]
        
        for i, (text, width) in enumerate(payment_cols):
            ctk.CTkLabel(
                header_frame, 
                text=text, 
                font=ctk.CTkFont(weight="bold"),
                width=width
            ).grid(row=0, column=i, padx=10, pady=5)
        
        # Payment data
        payment_scroll = ctk.CTkScrollableFrame(payment_frame, fg_color="transparent")
        payment_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        if payment_data:
            # Calculate total revenue for percentage
            total_revenue = sum(float(pm['revenue']) if pm['revenue'] else 0 for pm in payment_data)
            
            for i, payment in enumerate(payment_data):
                payment_frame = ctk.CTkFrame(payment_scroll)
                payment_frame.pack(fill="x", pady=2)
                
                method = payment['payment_method'].replace('_', ' ').title()
                revenue = float(payment['revenue']) if payment['revenue'] else 0
                bookings = int(payment['bookings']) if payment['bookings'] else 0
                percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                
                ctk.CTkLabel(payment_frame, text=method, width=payment_cols[0][1], anchor="w").grid(row=0, column=0, padx=10, pady=5)
                ctk.CTkLabel(payment_frame, text=format_currency(revenue), width=payment_cols[1][1]).grid(row=0, column=1, padx=10, pady=5)
                ctk.CTkLabel(payment_frame, text=str(bookings), width=payment_cols[2][1]).grid(row=0, column=2, padx=10, pady=5)
                ctk.CTkLabel(payment_frame, text=f"{percentage:.1f}%", width=payment_cols[3][1]).grid(row=0, column=3, padx=10, pady=5)
        else:
            # No data message
            no_data_label = ctk.CTkLabel(
                payment_scroll, 
                text="No payment method data available for the selected period", 
                text_color=("gray50", "gray70")
            )
            no_data_label.pack(pady=20)
    
    def export_revenue_report(self, from_date, to_date):
        import csv
        from tkinter import filedialog
        
        # Ask user where to save the CSV file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Revenue Report"
        )
        
        if not file_path:
            return  # User cancelled
        
        # Format dates for database queries
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get daily revenue data for the report
                cursor.execute("""
                    SELECT 
                        DATE(b.booking_date) as date,
                        SUM(CASE WHEN b.status = 'confirmed' THEN b.total_fare ELSE 0 END) as revenue,
                        COUNT(CASE WHEN b.status = 'confirmed' THEN 1 ELSE NULL END) as confirmed_bookings,
                        COUNT(CASE WHEN b.status = 'cancelled' THEN 1 ELSE NULL END) as cancelled_bookings,
                        COUNT(*) as total_bookings
                    FROM 
                        bookings b
                    WHERE 
                        DATE(b.booking_date) BETWEEN %s AND %s
                    GROUP BY 
                        DATE(b.booking_date)
                    ORDER BY 
                        date
                """, (from_date_str, to_date_str))
                
                daily_data = cursor.fetchall()
                
                if daily_data:
                    # Write to CSV
                    with open(file_path, mode='w', newline='') as csv_file:
                        fieldnames = ['Date', 'Revenue', 'Confirmed Bookings', 'Cancelled Bookings', 'Total Bookings']
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        for entry in daily_data:
                            writer.writerow({
                                'Date': entry['date'],
                                'Revenue': entry['revenue'],
                                'Confirmed Bookings': entry['confirmed_bookings'],
                                'Cancelled Bookings': entry['cancelled_bookings'],
                                'Total Bookings': entry['total_bookings']
                            })
                    
                    CTkMessagebox(
                        title="Success",
                        message=f"Revenue report successfully exported to {file_path}",
                        icon="check"
                    )
                else:
                    CTkMessagebox(
                        title="No Data",
                        message="No revenue data to export for the selected period",
                        icon="warning"
                    )
                
            except Exception as e:
                CTkMessagebox(
                    title="Export Error",
                    message=f"Failed to export revenue report: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_admin_passengers_tab(self):
        # Similar pattern to other admin tabs
        # This tab shows all passengers data across bookings
        
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame with sidebar
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Add sidebar (same as in other tabs)
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator and admin info
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Passengers" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Passengers" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Passenger Management", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Passengers content
        passengers_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        passengers_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Search and filter frame
        controls_frame = ctk.CTkFrame(passengers_frame)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        search_label = ctk.CTkLabel(controls_frame, text="Search Passengers:")
        search_label.pack(side="left", padx=10)
        
        search_entry = ctk.CTkEntry(controls_frame, width=200, height=35)
        search_entry.pack(side="left", padx=5)
        
        search_button = ctk.CTkButton(
            controls_frame, 
            text="Search",
            command=lambda: self.search_passengers(passengers_scroll, search_entry.get()),
            width=80,
            height=35
        )
        search_button.pack(side="left", padx=5)
        
        # Filter by class
        filter_label = ctk.CTkLabel(controls_frame, text="Filter by Class:")
        filter_label.pack(side="left", padx=(20, 5))
        
        class_var = StringVar(value="All")
        class_menu = ctk.CTkOptionMenu(
            controls_frame, 
            values=["All", "Sleeper", "AC", "General"],
            variable=class_var,
            width=120,
            height=35
        )
        class_menu.pack(side="left", padx=5)
        
        filter_button = ctk.CTkButton(
            controls_frame, 
            text="Apply Filter",
            command=lambda: self.filter_passengers_by_class(passengers_scroll, class_var.get()),
            width=100,
            height=35
        )
        filter_button.pack(side="left", padx=5)
        
        reset_button = ctk.CTkButton(
            controls_frame, 
            text="Reset",
            command=lambda: [self.load_passengers(passengers_scroll), search_entry.delete(0, 'end'), class_var.set("All")],
            width=80,
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        reset_button.pack(side="left", padx=5)
        
        # Export button (on the right)
        export_button = ctk.CTkButton(
            controls_frame,
            text="Export to CSV",
            command=self.export_passengers_to_csv,
            width=120,
            height=35,
            fg_color=("green", "dark green"),
            hover_color=("darkgreen", "green4")
        )
        export_button.pack(side="right", padx=10)
        
        # Create a scrollable frame for the passengers list
        passengers_scroll = ctk.CTkScrollableFrame(passengers_frame)
        passengers_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load passengers
        self.load_passengers(passengers_scroll)
    
    def load_passengers(self, container):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT 
                        p.id, p.name, p.age, p.gender, p.seat_class, p.seat_number,
                        b.pnr, b.booking_date, b.status,
                        s.source, s.destination, s.departure_date, s.departure_time,
                        t.train_number, t.train_name
                    FROM 
                        passengers p
                    JOIN 
                        bookings b ON p.booking_id = b.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    ORDER BY 
                        s.departure_date DESC, s.departure_time DESC
                """)
                
                passengers = cursor.fetchall()
                
                if not passengers:
                    no_passengers_label = ctk.CTkLabel(
                        container, 
                        text="No passengers found",
                        text_color=("gray50", "gray70")
                    )
                    no_passengers_label.pack(pady=20)
                    return
                
                # Display the passengers
                self.display_passengers(container, passengers)
                
            except Exception as e:
                print(f"Error loading passengers: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error loading passengers: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def search_passengers(self, container, search_term):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        if not search_term:
            self.load_passengers(container)
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Search by passenger name or PNR
                search_pattern = f"%{search_term}%"
                
                cursor.execute("""
                    SELECT 
                        p.id, p.name, p.age, p.gender, p.seat_class, p.seat_number,
                        b.pnr, b.booking_date, b.status,
                        s.source, s.destination, s.departure_date, s.departure_time,
                        t.train_number, t.train_name
                    FROM 
                        passengers p
                    JOIN 
                        bookings b ON p.booking_id = b.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        p.name LIKE %s OR b.pnr LIKE %s
                    ORDER BY 
                        s.departure_date DESC, s.departure_time DESC
                """, (search_pattern, search_pattern))
                
                passengers = cursor.fetchall()
                
                if not passengers:
                    no_passengers_label = ctk.CTkLabel(
                        container, 
                        text=f"No passengers found matching '{search_term}'",
                        text_color=("gray50", "gray70")
                    )
                    no_passengers_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Passengers", 
                        command=lambda: self.load_passengers(container),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the passengers
                self.display_passengers(container, passengers)
                
            except Exception as e:
                print(f"Error searching passengers: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error searching passengers: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def filter_passengers_by_class(self, container, seat_class):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        if seat_class == "All":
            self.load_passengers(container)
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT 
                        p.id, p.name, p.age, p.gender, p.seat_class, p.seat_number,
                        b.pnr, b.booking_date, b.status,
                        s.source, s.destination, s.departure_date, s.departure_time,
                        t.train_number, t.train_name
                    FROM 
                        passengers p
                    JOIN 
                        bookings b ON p.booking_id = b.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        p.seat_class = %s
                    ORDER BY 
                        s.departure_date DESC, s.departure_time DESC
                """, (seat_class.lower(),))
                
                passengers = cursor.fetchall()
                
                if not passengers:
                    no_passengers_label = ctk.CTkLabel(
                        container, 
                        text=f"No passengers found in {seat_class} class",
                        text_color=("gray50", "gray70")
                    )
                    no_passengers_label.pack(pady=20)
                    
                    # Show reset filter button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Passengers", 
                        command=lambda: self.load_passengers(container),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the passengers
                self.display_passengers(container, passengers)
                
            except Exception as e:
                print(f"Error filtering passengers: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error filtering passengers: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def display_passengers(self, container, passengers):
        # Headers
        header_frame = ctk.CTkFrame(container, fg_color=("gray80", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=5)
        
        header_columns = [
            ("Passenger Name", 150),
            ("Age/Gender", 100),
            ("Class/Seat", 120),
            ("PNR/Status", 120),
            ("Train", 120),
            ("Journey", 200),
            ("Departure", 120)
        ]
        
        for i, (text, width) in enumerate(header_columns):
            header_label = ctk.CTkLabel(
                header_frame, 
                text=text, 
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Passenger rows
        for i, passenger in enumerate(passengers):
            row_frame = ctk.CTkFrame(container)
            row_frame.pack(fill="x", pady=2)
            
            # Format gender and class for display
            gender_display = passenger['gender'].capitalize()
            class_display = passenger['seat_class'].capitalize()
            seat_display = passenger['seat_number'] if passenger['seat_number'] else "Not assigned"
            
            # Format status with color
            status_color = "#43a047" if passenger['status'] == 'confirmed' else "#e53935"
            status_text = "Confirmed" if passenger['status'] == 'confirmed' else "Cancelled"
            
            ctk.CTkLabel(row_frame, text=passenger['name'], width=header_columns[0][1], anchor="w").grid(row=0, column=0, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"{passenger['age']} / {gender_display}", width=header_columns[1][1]).grid(row=0, column=1, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"{class_display} / {seat_display}", width=header_columns[2][1]).grid(row=0, column=2, padx=5, pady=8, sticky="w")
            
            # PNR and status
            pnr_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            pnr_frame.grid(row=0, column=3, padx=5, pady=5)
            
            ctk.CTkLabel(pnr_frame, text=passenger['pnr']).pack(anchor="w")
            ctk.CTkLabel(pnr_frame, text=status_text, text_color=status_color, font=ctk.CTkFont(size=12)).pack(anchor="w")
            
            ctk.CTkLabel(row_frame, text=f"{passenger['train_number']}\n{passenger['train_name']}", width=header_columns[4][1]).grid(row=0, column=4, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"{passenger['source']} → {passenger['destination']}", width=header_columns[5][1], wraplength=180).grid(row=0, column=5, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"{passenger['departure_date']}\n{passenger['departure_time']}", width=header_columns[6][1]).grid(row=0, column=6, padx=5, pady=8, sticky="w")
    
    def export_passengers_to_csv(self):
        import csv
        from tkinter import filedialog
        
        # Ask user where to save the CSV file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Passengers Report"
        )
        
        if not file_path:
            return  # User cancelled
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT 
                        p.name as passenger_name, p.age, p.gender, p.seat_class, p.seat_number,
                        b.pnr, b.status, b.booking_date,
                        s.source, s.destination, s.departure_date, s.departure_time,
                        t.train_number, t.train_name
                    FROM 
                        passengers p
                    JOIN 
                        bookings b ON p.booking_id = b.id
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    ORDER BY 
                        s.departure_date DESC, s.departure_time DESC
                """)
                
                passengers = cursor.fetchall()
                
                if passengers:
                    # Write to CSV
                    with open(file_path, mode='w', newline='') as csv_file:
                        fieldnames = passengers[0].keys()
                        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                        
                        writer.writeheader()
                        for passenger in passengers:
                            writer.writerow(passenger)
                    
                    CTkMessagebox(
                        title="Success",
                        message=f"Passengers data successfully exported to {file_path}",
                        icon="check"
                    )
                else:
                    CTkMessagebox(
                        title="No Data",
                        message="No passenger data to export",
                        icon="warning"
                    )
                
            except Exception as e:
                CTkMessagebox(
                    title="Export Error",
                    message=f"Failed to export passengers data: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_admin_settings_tab(self):
        # Similar pattern to other admin tabs
        # This tab allows admin to manage app settings and user accounts
        
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame with sidebar
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Add sidebar (same as in other tabs)
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator and admin info
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # Admin name and role
        admin_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        admin_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        admin_name = ctk.CTkLabel(
            admin_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        admin_name.pack(anchor="w")
        
        admin_role = ctk.CTkLabel(
            admin_frame, 
            text="Administrator", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        admin_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_admin_dashboard, "assets/dashboard_icon.png"),
            ("Manage Trains", lambda: self.show_admin_tab("trains"), "assets/train_icon.png"),
            ("Manage Schedules", lambda: self.show_admin_tab("schedules"), "assets/schedule_icon.png"),
            ("Bookings", lambda: self.show_admin_tab("bookings"), "assets/booking_icon.png"),
            ("Revenue", lambda: self.show_admin_tab("revenue"), "assets/revenue_icon.png"),
            ("Passengers", lambda: self.show_admin_tab("passengers"), "assets/passenger_icon.png"),
            ("Settings", lambda: self.show_admin_tab("settings"), "assets/settings_icon.png")
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Settings" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Settings" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="System Settings", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Settings content
        settings_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create a tabview for different settings
        tabview = ctk.CTkTabview(settings_frame)
        tabview.pack(fill="both", expand=True)
        
        # Add tabs
        tab_users = tabview.add("User Management")
        tab_account = tabview.add("Account Settings")
        tab_system = tabview.add("System Info")
        
        # Setup each tab
        self.setup_user_management_tab(tab_users)
        self.setup_account_settings_tab(tab_account)
        self.setup_system_info_tab(tab_system)
    
    def setup_user_management_tab(self, parent):
        # Create frame for user management
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)  # For controls
        parent.grid_rowconfigure(1, weight=1)  # For user list
        
        # Controls frame
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Search controls
        search_label = ctk.CTkLabel(controls_frame, text="Search Users:")
        search_label.pack(side="left", padx=10)
        
        search_entry = ctk.CTkEntry(controls_frame, width=200, height=35)
        search_entry.pack(side="left", padx=5)
        
        search_button = ctk.CTkButton(
            controls_frame, 
            text="Search",
            command=lambda: self.search_users(users_scroll, search_entry.get()),
            width=80,
            height=35
        )
        search_button.pack(side="left", padx=5)
        
        reset_button = ctk.CTkButton(
            controls_frame, 
            text="Reset",
            command=lambda: [self.load_users(users_scroll), search_entry.delete(0, 'end')],
            width=80,
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        reset_button.pack(side="left", padx=5)
        
        # Add user button
        add_user_button = ctk.CTkButton(
            controls_frame,
            text="Add New User",
            command=self.show_add_user_dialog,
            width=120,
            height=35,
            fg_color=("green", "dark green"),
            hover_color=("darkgreen", "green4")
        )
        add_user_button.pack(side="right", padx=10)
        
        # Users list
        users_frame = ctk.CTkFrame(parent)
        users_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create scrollable frame for the users list
        users_scroll = ctk.CTkScrollableFrame(users_frame)
        users_scroll.pack(fill="both", expand=True)
        
        # Load users
        self.load_users(users_scroll)
    
    def load_users(self, container):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT id, name, email, is_admin, theme, 
                           DATE_FORMAT(created_at, '%Y-%m-%d') as joined_date
                    FROM users
                    ORDER BY name
                """)
                
                users = cursor.fetchall()
                
                if not users:
                    no_users_label = ctk.CTkLabel(
                        container, 
                        text="No users found",
                        text_color=("gray50", "gray70")
                    )
                    no_users_label.pack(pady=20)
                    return
                
                # Display the users
                self.display_users(container, users)
                
            except Exception as e:
                print(f"Error loading users: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error loading users: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def search_users(self, container, search_term):
        # Clear the container
        for widget in container.winfo_children():
            widget.destroy()
        
        if not search_term:
            self.load_users(container)
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Search by name or email
                search_pattern = f"%{search_term}%"
                
                cursor.execute("""
                    SELECT id, name, email, is_admin, theme, 
                           DATE_FORMAT(created_at, '%Y-%m-%d') as joined_date
                    FROM users
                    WHERE name LIKE %s OR email LIKE %s
                    ORDER BY name
                """, (search_pattern, search_pattern))
                
                users = cursor.fetchall()
                
                if not users:
                    no_users_label = ctk.CTkLabel(
                        container, 
                        text=f"No users found matching '{search_term}'",
                        text_color=("gray50", "gray70")
                    )
                    no_users_label.pack(pady=20)
                    
                    # Show reset search button
                    reset_button = ctk.CTkButton(
                        container, 
                        text="Show All Users", 
                        command=lambda: self.load_users(container),
                        height=35
                    )
                    reset_button.pack(pady=10)
                    return
                
                # Display the users
                self.display_users(container, users)
                
            except Exception as e:
                print(f"Error searching users: {e}")
                error_label = ctk.CTkLabel(
                    container, 
                    text=f"Error searching users: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
    
    def display_users(self, container, users):
        # Headers
        header_frame = ctk.CTkFrame(container, fg_color=("gray80", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=5)
        
        header_columns = [
            ("Name", 150),
            ("Email", 200),
            ("Role", 100),
            ("Theme", 100),
            ("Joined Date", 120),
            ("Actions", 150)
        ]
        
        for i, (text, width) in enumerate(header_columns):
            header_label = ctk.CTkLabel(
                header_frame, 
                text=text, 
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # User rows
        for i, user in enumerate(users):
            row_frame = ctk.CTkFrame(container)
            row_frame.pack(fill="x", pady=2)
            
            # Format role and theme for display
            role_display = "Admin" if user['is_admin'] else "User"
            theme_display = user['theme'].capitalize() if user['theme'] else "Light"
            
            ctk.CTkLabel(row_frame, text=user['name'], width=header_columns[0][1], anchor="w").grid(row=0, column=0, padx=5, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=user['email'], width=header_columns[1][1], anchor="w").grid(row=0, column=1, padx=5, pady=8, sticky="w")
            
            # Role with custom style
            role_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            role_frame.grid(row=0, column=2, padx=5, pady=5)
            
            role_color = "#1e88e5" if user['is_admin'] else "#43a047"
            role_label = ctk.CTkLabel(
                role_frame,
                text=role_display,
                font=ctk.CTkFont(size=12),
                fg_color=role_color,
                corner_radius=5,
                text_color="white",
                width=80,
                height=20
            )
            role_label.pack()
            
            ctk.CTkLabel(row_frame, text=theme_display, width=header_columns[3][1]).grid(row=0, column=3, padx=5, pady=8)
            ctk.CTkLabel(row_frame, text=user['joined_date'], width=header_columns[4][1]).grid(row=0, column=4, padx=5, pady=8)
            
            # Actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=5, padx=5, pady=5, sticky="w")
            
            # Edit button
            edit_button = ctk.CTkButton(
                actions_frame,
                text="Edit",
                width=60,
                height=30,
                command=lambda u=user: self.show_edit_user_dialog(u)
            )
            edit_button.grid(row=0, column=0, padx=2)
            
            # Only allow deleting if the user is not the current user
            if user['id'] != self.current_user['id']:
                delete_button = ctk.CTkButton(
                    actions_frame,
                    text="Delete",
                    width=60,
                    height=30,
                    fg_color="#e53935",
                    hover_color="#c62828",
                    command=lambda u=user: self.show_delete_user_dialog(u)
                )
                delete_button.grid(row=0, column=1, padx=2)
    
    def show_add_user_dialog(self):
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add New User")
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Title
        title_label = ctk.CTkLabel(
            dialog, 
            text="Add New User", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # Form
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)
        
        # Name
        name_label = ctk.CTkLabel(form_frame, text="Full Name:")
        name_label.pack(anchor="w", pady=(10, 5))
        
        name_entry = ctk.CTkEntry(form_frame, height=35)
        name_entry.pack(fill="x")
        
        # Email
        email_label = ctk.CTkLabel(form_frame, text="Email:")
        email_label.pack(anchor="w", pady=(10, 5))
        
        email_entry = ctk.CTkEntry(form_frame, height=35)
        email_entry.pack(fill="x")
        
        # Password
        password_label = ctk.CTkLabel(form_frame, text="Password:")
        password_label.pack(anchor="w", pady=(10, 5))
        
        password_entry = ctk.CTkEntry(form_frame, height=35, show="•")
        password_entry.pack(fill="x")
        
        # Confirm Password
        confirm_password_label = ctk.CTkLabel(form_frame, text="Confirm Password:")
        confirm_password_label.pack(anchor="w", pady=(10, 5))
        
        confirm_password_entry = ctk.CTkEntry(form_frame, height=35, show="•")
        confirm_password_entry.pack(fill="x")
        
        # Role
        role_label = ctk.CTkLabel(form_frame, text="Role:")
        role_label.pack(anchor="w", pady=(10, 5))
        
        role_var = IntVar(value=0)  # 0 = User, 1 = Admin
        
        role_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        role_frame.pack(fill="x")
        
        user_radio = ctk.CTkRadioButton(
            role_frame, 
            text="Regular User",
            variable=role_var,
            value=0
        )
        user_radio.pack(side="left", padx=(0, 20))
        
        admin_radio = ctk.CTkRadioButton(
            role_frame, 
            text="Administrator",
            variable=role_var,
            value=1
        )
        admin_radio.pack(side="left")
        
        # Theme
        theme_label = ctk.CTkLabel(form_frame, text="Default Theme:")
        theme_label.pack(anchor="w", pady=(10, 5))
        
        theme_var = StringVar(value="light")
        
        theme_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        theme_frame.pack(fill="x")
        
        light_radio = ctk.CTkRadioButton(
            theme_frame, 
            text="Light",
            variable=theme_var,
            value="light"
        )
        light_radio.pack(side="left", padx=(0, 20))
        
        dark_radio = ctk.CTkRadioButton(
            theme_frame, 
            text="Dark",
            variable=theme_var,
            value="dark"
        )
        dark_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Add Button
        add_button = ctk.CTkButton(
            buttons_frame,
            text="Add User",
            command=lambda: self.add_user(
                name_entry.get(),
                email_entry.get(),
                password_entry.get(),
                confirm_password_entry.get(),
                bool(role_var.get()),
                theme_var.get(),
                dialog
            ),
            height=40
        )
        add_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy,
            height=40,
            fg_color="gray",
            hover_color="gray30"
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def add_user(self, name, email, password, confirm_password, is_admin, theme, dialog):
        # Validate inputs
        if not name or not email or not password or not confirm_password:
            CTkMessagebox(
                title="Error",
                message="Please fill in all fields",
                icon="cancel"
            )
            return
        
        if not validate_email(email):
            CTkMessagebox(
                title="Error",
                message="Please enter a valid email address",
                icon="cancel"
            )
            return
        
        if password != confirm_password:
            CTkMessagebox(
                title="Error",
                message="Passwords do not match",
                icon="cancel"
            )
            return
        
        if len(password) < 6:
            CTkMessagebox(
                title="Error",
                message="Password must be at least 6 characters long",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    CTkMessagebox(
                        title="Error",
                        message="Email already registered",
                        icon="cancel"
                    )
                    return
                
                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (name, email, password, is_admin, theme) VALUES (%s, %s, %s, %s, %s)",
                    (name, email, hashed_password, is_admin, theme)
                )
                
                connection.commit()
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success",
                    message="User added successfully",
                    icon="check"
                )
                
                # Refresh the users list
                for widget in self.app.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkTabview):
                                        for tab in grandchild.winfo_children():
                                            for content in tab.winfo_children():
                                                for scroll in content.winfo_children():
                                                    if isinstance(scroll, ctk.CTkScrollableFrame):
                                                        self.load_users(scroll)
                
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to add user: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_edit_user_dialog(self, user):
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Edit User: {user['name']}")
        dialog.geometry("500x450")
        dialog.resizable(True, True)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Title
        title_label = ctk.CTkLabel(
            dialog, 
            text=f"Edit User: {user['name']}", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # Form
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)
        
        # Name
        name_label = ctk.CTkLabel(form_frame, text="Full Name:")
        name_label.pack(anchor="w", pady=(10, 5))
        
        name_entry = ctk.CTkEntry(form_frame, height=35)
        name_entry.insert(0, user['name'])
        name_entry.pack(fill="x")
        
        # Email
        email_label = ctk.CTkLabel(form_frame, text="Email:")
        email_label.pack(anchor="w", pady=(10, 5))
        
        email_entry = ctk.CTkEntry(form_frame, height=35)
        email_entry.insert(0, user['email'])
        email_entry.pack(fill="x")
        
        # Password (optional for updates)
        password_label = ctk.CTkLabel(form_frame, text="New Password (leave blank to keep current):")
        password_label.pack(anchor="w", pady=(10, 5))
        
        password_entry = ctk.CTkEntry(form_frame, height=35, show="•")
        password_entry.pack(fill="x")
        
        # Role
        role_label = ctk.CTkLabel(form_frame, text="Role:")
        role_label.pack(anchor="w", pady=(10, 5))
        
        role_var = IntVar(value=1 if user['is_admin'] else 0)  # 0 = User, 1 = Admin
        
        role_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        role_frame.pack(fill="x")
        
        user_radio = ctk.CTkRadioButton(
            role_frame, 
            text="Regular User",
            variable=role_var,
            value=0
        )
        user_radio.pack(side="left", padx=(0, 20))
        
        admin_radio = ctk.CTkRadioButton(
            role_frame, 
            text="Administrator",
            variable=role_var,
            value=1
        )
        admin_radio.pack(side="left")
        
        # Theme
        theme_label = ctk.CTkLabel(form_frame, text="Theme:")
        theme_label.pack(anchor="w", pady=(10, 5))
        
        theme_var = StringVar(value=user['theme'] or "light")
        
        theme_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        theme_frame.pack(fill="x")
        
        light_radio = ctk.CTkRadioButton(
            theme_frame, 
            text="Light",
            variable=theme_var,
            value="light"
        )
        light_radio.pack(side="left", padx=(0, 20))
        
        dark_radio = ctk.CTkRadioButton(
            theme_frame, 
            text="Dark",
            variable=theme_var,
            value="dark"
        )
        dark_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Update Button
        update_button = ctk.CTkButton(
            buttons_frame,
            text="Update User",
            command=lambda: self.update_user(
                user['id'],
                name_entry.get(),
                email_entry.get(),
                password_entry.get(),
                bool(role_var.get()),
                theme_var.get(),
                dialog
            ),
            height=40
        )
        update_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy,
            height=40,
            fg_color="gray",
            hover_color="gray30"
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def update_user(self, user_id, name, email, password, is_admin, theme, dialog):
        # Validate inputs
        if not name or not email:
            CTkMessagebox(
                title="Error",
                message="Name and email are required",
                icon="cancel"
            )
            return
        
        if not validate_email(email):
            CTkMessagebox(
                title="Error",
                message="Please enter a valid email address",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Check if email already exists for another user
                cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
                if cursor.fetchone():
                    CTkMessagebox(
                        title="Error",
                        message="Email already registered to another user",
                        icon="cancel"
                    )
                    return
                
                # Update user
                if password:
                    # Hash the new password if provided
                    if len(password) < 6:
                        CTkMessagebox(
                            title="Error",
                            message="Password must be at least 6 characters long",
                            icon="cancel"
                        )
                        return
                    
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute(
                        "UPDATE users SET name = %s, email = %s, password = %s, is_admin = %s, theme = %s WHERE id = %s",
                        (name, email, hashed_password, is_admin, theme, user_id)
                    )
                else:
                    # Keep the existing password
                    cursor.execute(
                        "UPDATE users SET name = %s, email = %s, is_admin = %s, theme = %s WHERE id = %s",
                        (name, email, is_admin, theme, user_id)
                    )
                
                connection.commit()
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success",
                    message="User updated successfully",
                    icon="check"
                )
                
                # Refresh the users list
                for widget in self.app.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkTabview):
                                        for tab in grandchild.winfo_children():
                                            for content in tab.winfo_children():
                                                for scroll in content.winfo_children():
                                                    if isinstance(scroll, ctk.CTkScrollableFrame):
                                                        self.load_users(scroll)
                
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to update user: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_delete_user_dialog(self, user):
        # Create a confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.app)
        confirm_dialog.title("Delete User")
        confirm_dialog.geometry("400x200")
        confirm_dialog.resizable(False, False)
        confirm_dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Warning icon
        try:
            warning_img = load_image("assets/warning_icon.png", (64, 64))
            warning_label = ctk.CTkLabel(confirm_dialog, image=warning_img, text="")
            warning_label.image = warning_img
            warning_label.pack(pady=(20, 0))
        except:
            pass
        
        message_label = ctk.CTkLabel(
            confirm_dialog,
            text=f"Are you sure you want to delete the user '{user['name']}'?\nThis will also delete all associated data.",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=20)
        
        buttons_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Delete Button
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            fg_color="#e53935",
            hover_color="#c62828",
            command=lambda: self.delete_user(user['id'], confirm_dialog),
            height=35
        )
        delete_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            fg_color="gray",
            hover_color="gray30",
            command=confirm_dialog.destroy,
            height=35
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def delete_user(self, user_id, dialog):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Delete user (cascading will handle related records)
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                connection.commit()
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success",
                    message="User deleted successfully",
                    icon="check"
                )
                
                # Refresh the users list
                for widget in self.app.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkTabview):
                                        for tab in grandchild.winfo_children():
                                            for content in tab.winfo_children():
                                                for scroll in content.winfo_children():
                                                    if isinstance(scroll, ctk.CTkScrollableFrame):
                                                        self.load_users(scroll)
                
            except Exception as e:
                connection.rollback()
                dialog.destroy()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to delete user: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def setup_account_settings_tab(self, parent):
        # Create frame for account settings
        account_scroll = ctk.CTkScrollableFrame(parent)
        account_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Account information
        account_info_label = ctk.CTkLabel(
            account_scroll, 
            text="Your Account Information", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        account_info_label.pack(pady=(0, 10), anchor="w")
        
        # Current user details
        info_frame = ctk.CTkFrame(account_scroll)
        info_frame.pack(fill="x", pady=10)
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT name, email, is_admin, created_at
                    FROM users
                    WHERE id = %s
                """, (self.current_user['id'],))
                
                user_info = cursor.fetchone()
                
                if user_info:
                    info_grid = ctk.CTkFrame(info_frame, fg_color="transparent")
                    info_grid.pack(fill="x", padx=15, pady=15)
                    
                    info_items = [
                        ("Name:", user_info['name']),
                        ("Email:", user_info['email']),
                        ("Role:", "Administrator" if user_info['is_admin'] else "Regular User"),
                        ("Account Created:", str(user_info['created_at']))
                    ]
                    
                    for i, (label, value) in enumerate(info_items):
                        label_widget = ctk.CTkLabel(
                            info_grid, 
                            text=label,
                            font=ctk.CTkFont(weight="bold"),
                            width=120,
                            anchor="w"
                        )
                        label_widget.grid(row=i, column=0, padx=5, pady=8, sticky="w")
                        
                        value_widget = ctk.CTkLabel(
                            info_grid, 
                            text=value,
                            anchor="w"
                        )
                        value_widget.grid(row=i, column=1, padx=5, pady=8, sticky="w")
                
            except Exception as e:
                print(f"Error fetching account info: {e}")
            finally:
                cursor.close()
                connection.close()
        
        # Change password section
        password_label = ctk.CTkLabel(
            account_scroll, 
            text="Change Password", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        password_label.pack(pady=(20, 10), anchor="w")
        
        password_frame = ctk.CTkFrame(account_scroll)
        password_frame.pack(fill="x", pady=10)
        
        password_form = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_form.pack(fill="x", padx=15, pady=15)
        
        # Current password
        current_password_label = ctk.CTkLabel(password_form, text="Current Password:")
        current_password_label.pack(anchor="w", pady=(0, 5))
        
        current_password_entry = ctk.CTkEntry(password_form, show="•", height=35)
        current_password_entry.pack(fill="x", pady=(0, 10))
        
        # New password
        new_password_label = ctk.CTkLabel(password_form, text="New Password:")
        new_password_label.pack(anchor="w", pady=(0, 5))
        
        new_password_entry = ctk.CTkEntry(password_form, show="•", height=35)
        new_password_entry.pack(fill="x", pady=(0, 10))
        
        # Confirm new password
        confirm_password_label = ctk.CTkLabel(password_form, text="Confirm New Password:")
        confirm_password_label.pack(anchor="w", pady=(0, 5))
        
        confirm_password_entry = ctk.CTkEntry(password_form, show="•", height=35)
        confirm_password_entry.pack(fill="x", pady=(0, 10))
        
        # Change password button
        change_password_button = ctk.CTkButton(
            password_form,
            text="Change Password",
            command=lambda: self.change_password(
                current_password_entry.get(),
                new_password_entry.get(),
                confirm_password_entry.get(),
                [current_password_entry, new_password_entry, confirm_password_entry]
            ),
            height=35
        )
        change_password_button.pack(pady=10)
        
        # Theme preferences
        theme_label = ctk.CTkLabel(
            account_scroll, 
            text="Theme Preferences", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        theme_label.pack(pady=(20, 10), anchor="w")
        
        theme_frame = ctk.CTkFrame(account_scroll)
        theme_frame.pack(fill="x", pady=10)
        
        theme_options = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_options.pack(fill="x", padx=15, pady=15)
        
        theme_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        light_theme_btn = ctk.CTkRadioButton(
            theme_options,
            text="Light Theme",
            variable=theme_var,
            value="Light",
            command=lambda: self.change_appearance_mode("Light")
        )
        light_theme_btn.pack(anchor="w", pady=5)
        
        dark_theme_btn = ctk.CTkRadioButton(
            theme_options,
            text="Dark Theme",
            variable=theme_var,
            value="Dark",
            command=lambda: self.change_appearance_mode("Dark")
        )
        dark_theme_btn.pack(anchor="w", pady=5)
    
    def change_password(self, current_password, new_password, confirm_password, entries):
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            CTkMessagebox(
                title="Error",
                message="Please fill in all fields",
                icon="cancel"
            )
            return
        
        if new_password != confirm_password:
            CTkMessagebox(
                title="Error",
                message="New passwords do not match",
                icon="cancel"
            )
            return
        
        if len(new_password) < 6:
            CTkMessagebox(
                title="Error",
                message="New password must be at least 6 characters long",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Verify current password
                cursor.execute("SELECT password FROM users WHERE id = %s", (self.current_user['id'],))
                user_data = cursor.fetchone()
                
                if not user_data or not bcrypt.checkpw(current_password.encode('utf-8'), user_data['password'].encode('utf-8')):
                    CTkMessagebox(
                        title="Error",
                        message="Current password is incorrect",
                        icon="cancel"
                    )
                    return
                
                # Update password
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "UPDATE users SET password = %s WHERE id = %s",
                    (hashed_password, self.current_user['id'])
                )
                
                connection.commit()
                
                CTkMessagebox(
                    title="Success",
                    message="Password changed successfully",
                    icon="check"
                )
                
                # Clear password fields
                for entry in entries:
                    entry.delete(0, 'end')
                
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to change password: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def setup_system_info_tab(self, parent):
        # Create frame for system information
        system_scroll = ctk.CTkScrollableFrame(parent)
        system_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # App information
        app_info_label = ctk.CTkLabel(
            system_scroll, 
            text="Application Information", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        app_info_label.pack(pady=(0, 10), anchor="w")
        
        app_info_frame = ctk.CTkFrame(system_scroll)
        app_info_frame.pack(fill="x", pady=10)
        
        app_info = ctk.CTkFrame(app_info_frame, fg_color="transparent")
        app_info.pack(fill="x", padx=15, pady=15)
        
        app_items = [
            ("Application Name:", "Railways - Modern Railway Reservation System"),
            ("Version:", "2.0.0"),
            ("Last Updated:", "2025-05-01"),
            ("Developed By:", "Codebase Team")
        ]
        
        for i, (label, value) in enumerate(app_items):
            label_widget = ctk.CTkLabel(
                app_info, 
                text=label,
                font=ctk.CTkFont(weight="bold"),
                width=150,
                anchor="w"
            )
            label_widget.grid(row=i, column=0, padx=5, pady=8, sticky="w")
            
            value_widget = ctk.CTkLabel(
                app_info, 
                text=value,
                anchor="w"
            )
            value_widget.grid(row=i, column=1, padx=5, pady=8, sticky="w")
        
        # Database statistics
        db_stats_label = ctk.CTkLabel(
            system_scroll, 
            text="Database Statistics", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        db_stats_label.pack(pady=(20, 10), anchor="w")
        
        db_stats_frame = ctk.CTkFrame(system_scroll)
        db_stats_frame.pack(fill="x", pady=10)
        
        db_stats = ctk.CTkFrame(db_stats_frame, fg_color="transparent")
        db_stats.pack(fill="x", padx=15, pady=15)
        
        # Fetch statistics from database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Get counts for different tables
                cursor.execute("SELECT COUNT(*) FROM users")
                users_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trains")
                trains_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM schedules")
                schedules_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM bookings")
                bookings_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM passengers")
                passengers_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(total_fare) FROM bookings WHERE status = 'confirmed'")
                total_revenue = cursor.fetchone()[0] or 0
                
                stats_items = [
                    ("Total Users:", str(users_count)),
                    ("Total Trains:", str(trains_count)),
                    ("Total Schedules:", str(schedules_count)),
                    ("Total Bookings:", str(bookings_count)),
                    ("Total Passengers:", str(passengers_count)),
                    ("Total Revenue:", format_currency(total_revenue))
                ]
                
                for i, (label, value) in enumerate(stats_items):
                    label_widget = ctk.CTkLabel(
                        db_stats, 
                        text=label,
                        font=ctk.CTkFont(weight="bold"),
                        width=150,
                        anchor="w"
                    )
                    label_widget.grid(row=i, column=0, padx=5, pady=8, sticky="w")
                    
                    value_widget = ctk.CTkLabel(
                        db_stats, 
                        text=value,
                        anchor="w"
                    )
                    value_widget.grid(row=i, column=1, padx=5, pady=8, sticky="w")
                    
            except Exception as e:
                print(f"Error fetching database statistics: {e}")
                error_label = ctk.CTkLabel(
                    db_stats, 
                    text=f"Error fetching statistics: {str(e)}",
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        
        # System actions
        actions_label = ctk.CTkLabel(
            system_scroll, 
            text="System Actions", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        actions_label.pack(pady=(20, 10), anchor="w")
        
        actions_frame = ctk.CTkFrame(system_scroll)
        actions_frame.pack(fill="x", pady=10)
        
        actions = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions.pack(fill="x", padx=15, pady=15)
        
        # Backup Database button
        backup_button = ctk.CTkButton(
            actions,
            text="Backup Database",
            command=self.backup_database,
            height=35
        )
        backup_button.pack(fill="x", pady=5)
        
        # Check for updates
        updates_button = ctk.CTkButton(
            actions,
            text="Check for Updates",
            command=self.check_for_updates,
            height=35
        )
        updates_button.pack(fill="x", pady=5)
        
        # About button
        about_button = ctk.CTkButton(
            actions,
            text="About",
            command=self.show_about_dialog,
            height=35
        )
        about_button.pack(fill="x", pady=5)
    
    def backup_database(self):
        import subprocess
        from tkinter import filedialog
        import os
        from datetime import datetime
        
        # Ask user where to save the backup
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql")],
            title="Save Database Backup",
            initialfile=f"railway_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Get database credentials from environment variables
            host = os.getenv("MYSQL_HOST")
            user = os.getenv("MYSQL_USER")
            password = os.getenv("MYSQL_PASSWORD")
            database = os.getenv("MYSQL_DATABASE")
            
            # Create backup command
            backup_command = [
                "mysqldump",
                f"--host={host}",
                f"--user={user}",
                f"--password={password}",
                database,
                f"--result-file={file_path}"
            ]
            
            # Execute backup
            process = subprocess.Popen(
                backup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"mysqldump failed: {stderr.decode('utf-8')}")
            
            CTkMessagebox(
                title="Success",
                message=f"Database backup created successfully at {file_path}",
                icon="check"
            )
            
        except Exception as e:
            CTkMessagebox(
                title="Backup Error",
                message=f"Failed to backup database: {str(e)}",
                icon="cancel"
            )
    
    def check_for_updates(self):
        # Simulate checking for updates
        import time
        
        # Create progress dialog
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Checking for Updates")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Progress message
        msg_label = ctk.CTkLabel(
            dialog,
            text="Checking for updates...",
            font=ctk.CTkFont(size=14)
        )
        msg_label.pack(pady=(20, 10))
        
        # Progress bar
        progress = ctk.CTkProgressBar(dialog, width=300)
        progress.pack(pady=10)
        progress.set(0)
        
        def update_progress():
            # Simulate progress
            for i in range(1, 11):
                progress.set(i / 10)
                msg_label.configure(text=f"Checking for updates... {i*10}%")
                dialog.update()
                time.sleep(0.2)
            
            dialog.destroy()
            
            # Show result
            CTkMessagebox(
                title="Update Check",
                message="Your application is up to date! You are running the latest version (v2.0.0).",
                icon="check"
            )
        
        # Start progress after a short delay to let the dialog appear
        dialog.after(100, update_progress)
    
    def show_about_dialog(self):
        # Show about dialog with app information
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("About Railway Reservation System")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # App logo
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((100, 100), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(dialog, image=logo_photo, text="")
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 0))
        except:
            pass
        
        # App title
        app_title = ctk.CTkLabel(
            dialog,
            text="Railways",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        app_title.pack(pady=(10, 0))
        
        # App subtitle
        app_subtitle = ctk.CTkLabel(
            dialog,
            text="Modern Railway Reservation System",
            font=ctk.CTkFont(size=14)
        )
        app_subtitle.pack(pady=(0, 10))
        
        # Version
        version_label = ctk.CTkLabel(
            dialog,
            text="Version 2.0.0",
            font=ctk.CTkFont(size=12)
        )
        version_label.pack()
        
        # Separator
        separator = ctk.CTkFrame(dialog, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=20, pady=20)
        
        # Description
        description = ctk.CTkLabel(
            dialog,
            text="A comprehensive railway reservation system with modern UI/UX design.",
            wraplength=400
        )
        description.pack(pady=5)
        
        # Copyright
        copyright_label = ctk.CTkLabel(
            dialog,
            text="© 2024-2025 All rights reserved.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        copyright_label.pack(pady=5)
        
        # Current date time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        time_label = ctk.CTkLabel(
            dialog,
            text=f"Current System Time: {current_time}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        time_label.pack(pady=5)
        
        # Close button
        close_button = ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100
        )
        close_button.pack(pady=20)
    
    # User Dashboard
    def show_user_dashboard(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # User name and role
        user_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        user_name = ctk.CTkLabel(
            user_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_name.pack(anchor="w")
        
        user_role = ctk.CTkLabel(
            user_frame, 
            text="Passenger", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        user_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_user_dashboard, "assets/dashboard_icon.png"),
            ("Book Tickets", lambda: self.show_user_tab("book"), "assets/ticket_icon.png"),
            ("My Bookings", lambda: self.show_user_tab("bookings"), "assets/booking_icon.png"),
            ("Train Schedule", lambda: self.show_user_tab("schedule"), "assets/schedule_icon.png"),
            ("My Profile", lambda: self.show_user_tab("profile"), "assets/profile_icon.png"),
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Dashboard" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Dashboard" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Passenger Dashboard", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Current date and time
        current_datetime = datetime.now().strftime("%B %d, %Y %H:%M")
        date_label = ctk.CTkLabel(
            header_frame, 
            text=current_datetime,
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        date_label.pack(side="right", padx=20)
        
        # Dashboard content
        dashboard_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_frame = ctk.CTkFrame(dashboard_frame)
        welcome_frame.pack(fill="x", padx=10, pady=10)
        
        try:
            welcome_img = load_image("assets/ticket_icon.png", (60, 60))
            welcome_icon = ctk.CTkLabel(welcome_frame, image=welcome_img, text="")
            welcome_icon.image = welcome_img
            welcome_icon.pack(side="left", padx=20, pady=20)
        except:
            pass
        
        welcome_text = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        welcome_text.pack(side="left", fill="both", expand=True, padx=10, pady=20)
        
        welcome_title = ctk.CTkLabel(
            welcome_text, 
            text=f"Welcome back, {self.current_user['name']}!", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome_title.pack(anchor="w")
        
        welcome_subtitle = ctk.CTkLabel(
            welcome_text, 
            text="Book your journey with ease and comfort", 
            font=ctk.CTkFont(size=14)
        )
        welcome_subtitle.pack(anchor="w", pady=(5, 0))
        
        # Quick Actions
        actions_label = ctk.CTkLabel(
            dashboard_frame, 
            text="Quick Actions", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        actions_label.pack(anchor="w", padx=10, pady=(20, 10))
        
        # Quick actions grid
        actions_frame = ctk.CTkFrame(dashboard_frame)
        actions_frame.pack(fill="x", padx=10, pady=10)
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Book ticket card
        book_card = ctk.CTkFrame(actions_frame)
        book_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        try:
            book_img = load_image("assets/ticket_icon.png", (40, 40))
            book_icon = ctk.CTkLabel(book_card, image=book_img, text="")
            book_icon.image = book_img
            book_icon.pack(pady=(20, 10))
        except:
            pass
        
        book_title = ctk.CTkLabel(
            book_card, 
            text="Book New Ticket", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        book_title.pack(pady=5)
        
        book_button = ctk.CTkButton(
            book_card,
            text="Book Now",
            width=120,
            height=30,
            command=lambda: self.show_user_tab("book")
        )
        book_button.pack(pady=(5, 20))
        
        # View bookings card
        view_card = ctk.CTkFrame(actions_frame)
        view_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        try:
            view_img = load_image("assets/booking_icon.png", (40, 40))
            view_icon = ctk.CTkLabel(view_card, image=view_img, text="")
            view_icon.image = view_img
            view_icon.pack(pady=(20, 10))
        except:
            pass
        
        view_title = ctk.CTkLabel(
            view_card, 
            text="My Bookings", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        view_title.pack(pady=5)
        
        view_button = ctk.CTkButton(
            view_card,
            text="View All",
            width=120,
            height=30,
            command=lambda: self.show_user_tab("bookings")
        )
        view_button.pack(pady=(5, 20))
        
        # Train schedule card
        schedule_card = ctk.CTkFrame(actions_frame)
        schedule_card.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        try:
            schedule_img = load_image("assets/schedule_icon.png", (40, 40))
            schedule_icon = ctk.CTkLabel(schedule_card, image=schedule_img, text="")
            schedule_icon.image = schedule_img
            schedule_icon.pack(pady=(20, 10))
        except:
            pass
        
        schedule_title = ctk.CTkLabel(
            schedule_card, 
            text="Train Schedule", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        schedule_title.pack(pady=5)
        
        schedule_button = ctk.CTkButton(
            schedule_card,
            text="Check Schedule",
            width=120,
            height=30,
            command=lambda: self.show_user_tab("schedule")
        )
        schedule_button.pack(pady=(5, 20))
        
        # Recent bookings and upcoming journeys
        dashboard_bottom = ctk.CTkFrame(dashboard_frame, fg_color="transparent")
        dashboard_bottom.pack(fill="both", expand=True, padx=10, pady=10)
        dashboard_bottom.grid_columnconfigure(0, weight=1)
        dashboard_bottom.grid_columnconfigure(1, weight=1)
        dashboard_bottom.grid_rowconfigure(0, weight=1)
        
        # Recent bookings
        recent_bookings_frame = ctk.CTkFrame(dashboard_bottom)
        recent_bookings_frame.grid(row=0, column=0, padx=(0, 5), pady=10, sticky="nsew")
        
        recent_bookings_label = ctk.CTkLabel(
            recent_bookings_frame, 
            text="My Recent Bookings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        recent_bookings_label.pack(anchor="w", padx=15, pady=15)
        
        self.show_user_recent_bookings(recent_bookings_frame)
        
        # Upcoming journeys
        upcoming_frame = ctk.CTkFrame(dashboard_bottom)
        upcoming_frame.grid(row=0, column=1, padx=(5, 0), pady=10, sticky="nsew")
        
        upcoming_label = ctk.CTkLabel(
            upcoming_frame, 
            text="Upcoming Journeys", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        upcoming_label.pack(anchor="w", padx=15, pady=15)
        
        self.show_user_upcoming_journeys(upcoming_frame)
    
    def show_user_tab(self, tab_name):
        # This method handles navigation between user tabs
        if tab_name == "book":
            self.show_book_ticket_screen()
        elif tab_name == "bookings":
            self.show_user_bookings_screen()
        elif tab_name == "schedule":
            self.show_train_schedule_screen()
        elif tab_name == "profile":
            self.show_user_profile_screen()
    
    def show_user_recent_bookings(self, parent):
        # Create scrollable frame
        bookings_scroll = ctk.CTkScrollableFrame(parent)
        bookings_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Get recent bookings for current user
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT 
                        b.id, b.pnr, b.booking_date, b.total_fare, b.status,
                        t.train_name, s.source, s.destination, s.departure_date, s.departure_time
                    FROM 
                        bookings b
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        b.user_id = %s
                    ORDER BY 
                        b.booking_date DESC
                    LIMIT 3
                """, (self.current_user['id'],))
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_data_label = ctk.CTkLabel(
                        bookings_scroll, 
                        text="No recent bookings found",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_data_label.pack(pady=20)
                    return
                
                # Create bookings list
                for booking in bookings:
                    booking_frame = ctk.CTkFrame(bookings_scroll)
                    booking_frame.pack(fill="x", pady=5)
                    
                    # PNR and status
                    header_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    header_frame.pack(fill="x", padx=10, pady=(10, 5))
                    
                    pnr_label = ctk.CTkLabel(
                        header_frame,
                        text=f"PNR: {booking['pnr']}",
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
                    pnr_label.pack(side="left")
                    
                    status_color = "#43a047" if booking['status'] == 'confirmed' else "#e53935"
                    status_text = "Confirmed" if booking['status'] == 'confirmed' else "Cancelled"
                    
                    status_label = ctk.CTkLabel(
                        header_frame,
                        text=status_text,
                        font=ctk.CTkFont(size=12),
                        text_color=status_color
                    )
                    status_label.pack(side="right")
                    
                    # Train details
                    train_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    train_frame.pack(fill="x", padx=10, pady=(0, 5))
                    
                    train_label = ctk.CTkLabel(
                        train_frame,
                        text=f"{booking['train_name']}",
                        font=ctk.CTkFont(size=13)
                    )
                    train_label.pack(side="left")
                    
                    route_label = ctk.CTkLabel(
                        train_frame,
                        text=f"{booking['source']} → {booking['destination']}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    route_label.pack(side="right")
                    
                    # Bottom details
                    bottom_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", padx=10, pady=(0, 10))
                    
                    date_str = f"{booking['departure_date']} {booking['departure_time']}"
                    date_label = ctk.CTkLabel(
                        bottom_frame,
                        text=f"Departure: {date_str}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    date_label.pack(side="left")
                    
                    fare_label = ctk.CTkLabel(
                        bottom_frame,
                        text=format_currency(booking['total_fare']),
                        font=ctk.CTkFont(size=12, weight="bold")
                    )
                    fare_label.pack(side="right")
            except Exception as e:
                print(f"Error loading recent bookings: {e}")
                no_data_label = ctk.CTkLabel(
                    bookings_scroll, 
                    text="Error loading recent bookings",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_data_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            no_data_label = ctk.CTkLabel(
                bookings_scroll, 
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            no_data_label.pack(pady=20)
    
    def show_user_upcoming_journeys(self, parent):
        # Create scrollable frame
        journeys_scroll = ctk.CTkScrollableFrame(parent)
        journeys_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Get upcoming journeys for current user
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get current date
                current_date = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute("""
                    SELECT 
                        b.id, b.pnr, t.train_name, s.source, s.destination, 
                        s.departure_date, s.departure_time, s.status, s.delay_minutes
                    FROM 
                        bookings b
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        b.user_id = %s AND
                        b.status = 'confirmed' AND
                        (s.departure_date > %s OR (s.departure_date = %s AND s.departure_time >= %s))
                    ORDER BY 
                        s.departure_date, s.departure_time
                    LIMIT 3
                """, (self.current_user['id'], current_date, current_date, datetime.now().strftime('%H:%M')))
                journeys = cursor.fetchall()
                
                if not journeys:
                    no_data_label = ctk.CTkLabel(
                        journeys_scroll, 
                        text="No upcoming journeys found",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_data_label.pack(pady=20)
                    return
                
                # Create journeys list
                for journey in journeys:
                    journey_frame = ctk.CTkFrame(journeys_scroll)
                    journey_frame.pack(fill="x", pady=5)
                    
                    # Train details
                    header_frame = ctk.CTkFrame(journey_frame, fg_color="transparent")
                    header_frame.pack(fill="x", padx=10, pady=(10, 5))
                    
                    train_label = ctk.CTkLabel(
                        header_frame,
                        text=f"{journey['train_name']}",
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
                    train_label.pack(side="left")
                    
                    # Status indicator
                    status_color = "#43a047"  # Default green for on-time
                    status_text = "On Time"
                    
                    if journey['status'] == 'delayed':
                        status_color = "#ffb300"  # Orange for delayed
                        status_text = f"Delayed {journey['delay_minutes']} min"
                    elif journey['status'] == 'cancelled':
                        status_color = "#e53935"  # Red for cancelled
                        status_text = "Cancelled"
                    
                    status_label = ctk.CTkLabel(
                        header_frame,
                        text=status_text,
                        font=ctk.CTkFont(size=12),
                        text_color=status_color
                    )
                    status_label.pack(side="right")
                    
                    # Route
                    route_frame = ctk.CTkFrame(journey_frame, fg_color="transparent")
                    route_frame.pack(fill="x", padx=10, pady=(0, 5))
                    
                    route_label = ctk.CTkLabel(
                        route_frame,
                        text=f"{journey['source']} → {journey['destination']}",
                        font=ctk.CTkFont(size=13)
                    )
                    route_label.pack(side="left")
                    
                    # PNR
                    pnr_label = ctk.CTkLabel(
                        route_frame,
                        text=f"PNR: {journey['pnr']}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    pnr_label.pack(side="right")
                    
                    # Departure details
                    bottom_frame = ctk.CTkFrame(journey_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", padx=10, pady=(0, 10))
                    
                    date_label = ctk.CTkLabel(
                        bottom_frame,
                        text=f"Departure: {journey['departure_date']} {journey['departure_time']}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    date_label.pack(side="left")
                    
                    # View button
                    view_button = ctk.CTkButton(
                        bottom_frame,
                        text="View Details",
                        width=100,
                        height=25,
                        font=ctk.CTkFont(size=12),
                        command=lambda b=journey: self.show_booking_details_dialog(b['pnr'])
                    )
                    view_button.pack(side="right")
            except Exception as e:
                print(f"Error loading upcoming journeys: {e}")
                no_data_label = ctk.CTkLabel(
                    journeys_scroll, 
                    text="Error loading upcoming journeys",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                no_data_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            no_data_label = ctk.CTkLabel(
                journeys_scroll, 
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            no_data_label.pack(pady=20)
    
    def show_booking_details_dialog(self, pnr):
        # Fetch booking details
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get booking details
                cursor.execute("""
                    SELECT 
                        b.id, b.pnr, b.booking_date, b.total_fare, b.status, b.payment_method,
                        t.train_number, t.train_name,
                        s.source, s.destination, s.departure_date, s.departure_time,
                        s.arrival_date, s.arrival_time, s.status as train_status, s.delay_minutes
                    FROM 
                        bookings b
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        b.pnr = %s AND b.user_id = %s
                """, (pnr, self.current_user['id']))
                
                booking = cursor.fetchone()
                
                if not booking:
                    CTkMessagebox(
                        title="Error",
                        message="Booking details not found",
                        icon="cancel"
                    )
                    return
                
                # Get passengers for this booking
                cursor.execute("""
                    SELECT * FROM passengers WHERE booking_id = %s
                """, (booking['id'],))
                
                passengers = cursor.fetchall()
                
                # Create a dialog window
                dialog = ctk.CTkToplevel(self.app)
                dialog.title(f"Booking Details - PNR: {pnr}")
                dialog.geometry("600x500")
                dialog.resizable(False, False)
                dialog.grab_set()  # Make the dialog modal
                
                # Center the dialog
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() // 2) - (width // 2)
                y = (dialog.winfo_screenheight() // 2) - (height // 2)
                dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                
                # Create a scrollable frame
                scroll_frame = ctk.CTkScrollableFrame(dialog)
                scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                # PNR and status
                header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                header_frame.pack(fill="x", pady=(0, 10))
                
                pnr_label = ctk.CTkLabel(
                    header_frame, 
                    text=f"PNR: {booking['pnr']}", 
                    font=ctk.CTkFont(size=20, weight="bold")
                )
                pnr_label.pack(side="left")
                
                status_color = "#43a047" if booking['status'] == "confirmed" else "#e53935"
                status_text = "Confirmed" if booking['status'] == "confirmed" else "Cancelled"
                
                status_badge = ctk.CTkLabel(
                    header_frame,
                    text=status_text,
                    text_color="white",
                    fg_color=status_color,
                    corner_radius=5,
                    width=100,
                    height=25
                )
                status_badge.pack(side="right")
                
                # Train info
                train_frame = ctk.CTkFrame(scroll_frame)
                train_frame.pack(fill="x", pady=10)
                
                try:
                    train_img = load_image("assets/train_icon.png", (40, 40))
                    train_icon = ctk.CTkLabel(train_frame, image=train_img, text="")
                    train_icon.image = train_img
                    train_icon.pack(side="left", padx=(15, 10), pady=15)
                except:
                    pass
                
                train_info = ctk.CTkFrame(train_frame, fg_color="transparent")
                train_info.pack(side="left", fill="both", expand=True, padx=10, pady=15)
                
                train_name = ctk.CTkLabel(
                    train_info,
                    text=f"{booking['train_number']} - {booking['train_name']}",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                train_name.pack(anchor="w")
                
                # Route and time info
                route_label = ctk.CTkLabel(
                    train_info,
                    text=f"{booking['source']} → {booking['destination']}",
                    font=ctk.CTkFont(size=14)
                )
                route_label.pack(anchor="w", pady=(5, 0))
                
                # Journey dates
                journey_frame = ctk.CTkFrame(scroll_frame)
                journey_frame.pack(fill="x", pady=10)
                
                journey_frame.grid_columnconfigure(0, weight=1)
                journey_frame.grid_columnconfigure(1, weight=1)
                
                # Departure info
                departure_frame = ctk.CTkFrame(journey_frame, fg_color="transparent")
                departure_frame.grid(row=0, column=0, padx=15, pady=15, sticky="w")
                
                departure_title = ctk.CTkLabel(
                    departure_frame,
                    text="Departure",
                    font=ctk.CTkFont(weight="bold"),
                    text_color=("gray50", "gray70")
                )
                departure_title.pack(anchor="w")
                
                departure_date = ctk.CTkLabel(
                    departure_frame,
                    text=f"{booking['departure_date']}",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                departure_date.pack(anchor="w")
                
                departure_time = ctk.CTkLabel(
                    departure_frame,
                    text=f"{booking['departure_time']}",
                    font=ctk.CTkFont(size=14)
                )
                departure_time.pack(anchor="w")
                
                # Train status
                train_status_color = "#43a047"  # Default green for on-time
                train_status_text = "On Time"
                
                if booking['train_status'] == 'delayed':
                    train_status_color = "#ffb300"  # Orange for delayed
                    train_status_text = f"Delayed {booking['delay_minutes']} min"
                elif booking['train_status'] == 'cancelled':
                    train_status_color = "#e53935"  # Red for cancelled
                    train_status_text = "Cancelled"
                
                train_status_label = ctk.CTkLabel(
                    departure_frame,
                    text=train_status_text,
                    font=ctk.CTkFont(size=12),
                    text_color=train_status_color
                )
                train_status_label.pack(anchor="w", pady=(5, 0))
                
                # Arrival info
                arrival_frame = ctk.CTkFrame(journey_frame, fg_color="transparent")
                arrival_frame.grid(row=0, column=1, padx=15, pady=15, sticky="w")
                
                arrival_title = ctk.CTkLabel(
                    arrival_frame,
                    text="Arrival",
                    font=ctk.CTkFont(weight="bold"),
                    text_color=("gray50", "gray70")
                )
                arrival_title.pack(anchor="w")
                
                arrival_date = ctk.CTkLabel(
                    arrival_frame,
                    text=f"{booking['arrival_date']}",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                arrival_date.pack(anchor="w")
                
                arrival_time = ctk.CTkLabel(
                    arrival_frame,
                    text=f"{booking['arrival_time']}",
                    font=ctk.CTkFont(size=14)
                )
                arrival_time.pack(anchor="w")
                
                # Fare and payment info
                payment_frame = ctk.CTkFrame(scroll_frame)
                payment_frame.pack(fill="x", pady=10)
                
                payment_method_text = booking.get('payment_method', 'Not specified').replace('_', ' ').title()
                payment_info = ctk.CTkFrame(payment_frame, fg_color="transparent")
                payment_info.pack(side="left", fill="both", expand=True, padx=15, pady=15)
                
                booking_date_label = ctk.CTkLabel(
                    payment_info,
                    text=f"Booking Date: {booking['booking_date']}",
                    font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray70")
                )
                booking_date_label.pack(anchor="w")
                
                payment_label = ctk.CTkLabel(
                    payment_info,
                    text=f"Payment Method: {payment_method_text}",
                    font=ctk.CTkFont(size=12)
                )
                payment_label.pack(anchor="w", pady=(5, 0))
                
                fare_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
                fare_frame.pack(side="right", padx=15, pady=15)
                
                fare_label = ctk.CTkLabel(
                    fare_frame,
                    text="Total Fare:",
                    font=ctk.CTkFont(size=12)
                )
                fare_label.pack(anchor="e")
                
                fare_amount = ctk.CTkLabel(
                    fare_frame,
                    text=format_currency(booking['total_fare']),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                fare_amount.pack(anchor="e")
                
                # Passengers list
                passengers_label = ctk.CTkLabel(
                    scroll_frame, 
                    text="Passenger Details", 
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                passengers_label.pack(anchor="w", pady=(20, 10))
                
                if not passengers:
                    no_passengers_label = ctk.CTkLabel(
                        scroll_frame, 
                        text="No passenger details available",
                        text_color=("gray50", "gray70")
                    )
                    no_passengers_label.pack(pady=10)
                else:
                    # Create frame for passenger headers
                    passenger_header = ctk.CTkFrame(scroll_frame, fg_color=("gray80", "gray25"))
                    passenger_header.pack(fill="x", pady=(0, 5))
                    
                    # Create header labels
                    ctk.CTkLabel(passenger_header, text="Name", width=150, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Age", width=50, font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Gender", width=70, font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Class", width=80, font=ctk.CTkFont(weight="bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")
                    ctk.CTkLabel(passenger_header, text="Seat", width=80, font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=5, pady=5, sticky="w")
                    
                    # Add each passenger to the list
                    for j, passenger in enumerate(passengers):
                        passenger_frame = ctk.CTkFrame(scroll_frame)
                        passenger_frame.pack(fill="x", pady=1)
                        
                        # Format class and gender values to be more readable
                        seat_class = passenger['seat_class'].capitalize()
                        gender = passenger['gender'].capitalize()
                        
                        ctk.CTkLabel(passenger_frame, text=passenger['name'], width=150).grid(row=0, column=0, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=str(passenger['age']), width=50).grid(row=0, column=1, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=gender, width=70).grid(row=0, column=2, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=seat_class, width=80).grid(row=0, column=3, padx=5, pady=5, sticky="w")
                        ctk.CTkLabel(passenger_frame, text=passenger['seat_number'] or "Not assigned", width=80).grid(row=0, column=4, padx=5, pady=5, sticky="w")
                
                # Action buttons
                buttons_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                buttons_frame.pack(fill="x", pady=(20, 0))
                
                # Close button
                close_button = ctk.CTkButton(
                    buttons_frame,
                    text="Close",
                    command=dialog.destroy,
                    width=120,
                    height=35
                )
                close_button.pack(side="left", padx=(0, 10), fill="x", expand=True)
                
                # Cancel booking button (only if status is confirmed)
                if booking['status'] == 'confirmed':
                    cancel_button = ctk.CTkButton(
                        buttons_frame,
                        text="Cancel Booking",
                        command=lambda: self.cancel_user_booking(booking['id'], dialog),
                        width=120,
                        height=35,
                        fg_color="#e53935",
                        hover_color="#c62828"
                    )
                    cancel_button.pack(side="right", padx=(10, 0), fill="x", expand=True)
            except Exception as e:
                print(f"Error fetching booking details: {e}")
                CTkMessagebox(
                    title="Error",
                    message=f"Error fetching booking details: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def cancel_user_booking(self, booking_id, dialog=None):
        # Create a confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.app)
        confirm_dialog.title("Cancel Booking")
        confirm_dialog.geometry("400x200")
        confirm_dialog.resizable(False, False)
        confirm_dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Warning icon
        try:
            warning_img = load_image("assets/warning_icon.png", (64, 64))
            warning_label = ctk.CTkLabel(confirm_dialog, image=warning_img, text="")
            warning_label.image = warning_img
            warning_label.pack(pady=(20, 0))
        except:
            pass
        
        message_label = ctk.CTkLabel(
            confirm_dialog,
            text="Are you sure you want to cancel this booking?\nThis action cannot be undone.",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=20)
        
        buttons_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Cancel Booking Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel Booking",
            fg_color="#e53935",
            hover_color="#c62828",
            command=lambda: self.perform_cancel_user_booking(booking_id, confirm_dialog, dialog),
            height=35
        )
        cancel_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Keep Button
        keep_button = ctk.CTkButton(
            buttons_frame,
            text="Keep Booking",
            command=confirm_dialog.destroy,
            height=35
        )
        keep_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def perform_cancel_user_booking(self, booking_id, confirm_dialog, parent_dialog=None):
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Update booking status to cancelled
                cursor.execute(
                    "UPDATE bookings SET status = 'cancelled' WHERE id = %s AND user_id = %s",
                    (booking_id, self.current_user['id'])
                )
                
                connection.commit()
                confirm_dialog.destroy()
                
                if parent_dialog:
                    parent_dialog.destroy()
                
                CTkMessagebox(
                    title="Success",
                    message="Your booking has been cancelled successfully",
                    icon="check"
                )
                
                # Refresh the current view
                if any("bookings" in str(child) for child in self.app.winfo_children()):
                    self.show_user_bookings_screen()
                else:
                    self.show_user_dashboard()
            except Exception as e:
                connection.rollback()
                confirm_dialog.destroy()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to cancel booking: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_book_ticket_screen(self):
        # Implement the booking interface
        # Similar structure to admin tabs but with user-focused interface
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # User name and role
        user_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        user_name = ctk.CTkLabel(
            user_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_name.pack(anchor="w")
        
        user_role = ctk.CTkLabel(
            user_frame, 
            text="Passenger", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        user_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_user_dashboard, "assets/dashboard_icon.png"),
            ("Book Tickets", lambda: self.show_user_tab("book"), "assets/ticket_icon.png"),
            ("My Bookings", lambda: self.show_user_tab("bookings"), "assets/booking_icon.png"),
            ("Train Schedule", lambda: self.show_user_tab("schedule"), "assets/schedule_icon.png"),
            ("My Profile", lambda: self.show_user_tab("profile"), "assets/profile_icon.png"),
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Book Tickets" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Book Tickets" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Book Train Tickets", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Current date and time
        current_datetime = datetime.now().strftime("%B %d, %Y %H:%M")
        date_label = ctk.CTkLabel(
            header_frame, 
            text=current_datetime,
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        date_label.pack(side="right", padx=20)
        
        # Create a tabview for booking steps
        book_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        book_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tabview = ctk.CTkTabview(book_frame)
        tabview.pack(fill="both", expand=True)
        
        # Add tabs for booking steps
        search_tab = tabview.add("Search Trains")
        results_tab = tabview.add("Search Results")
        passengers_tab = tabview.add("Passenger Details")
        payment_tab = tabview.add("Payment")
        
        tabview.set("Search Trains")
        
        # Initialize total_fare_var here to avoid the error
        self.total_fare_var = StringVar(value=format_currency(0))
        
        # Instead of using .state(), use the segmented button to control tab visibility
        # Make only the first tab active initially
        tabview.set("Search Trains")
        
        # Disable clicking on unavailable tabs
        tabview._segmented_button.configure(state="normal")  # Make sure it's initially enabled
        
        # Setup search tab
        self.setup_search_trains_tab(search_tab, tabview)
        
        # Store references to tabs for later use
        self.booking_tabs = {
            "search": search_tab,
            "results": results_tab,
            "passengers": passengers_tab,
            "payment": payment_tab
        }
    
    def setup_search_trains_tab(self, parent, tabview):
        # Create a scrollable frame for the search trains tab
        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title and info
        title_label = ctk.CTkLabel(
            scrollable_frame, 
            text="Search for Trains", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 5))

        subtitle_label = ctk.CTkLabel(
            scrollable_frame, 
            text="Enter your journey details to find available trains"
        )
        subtitle_label.pack(pady=(0, 20))

        # Journey details form
        form_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=50)

        # Source and destination in one row
        route_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        route_frame.pack(fill="x", pady=10)
        route_frame.grid_columnconfigure(0, weight=1)
        route_frame.grid_columnconfigure(1, weight=1)

        # Source station
        source_label = ctk.CTkLabel(route_frame, text="From")
        source_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        source_var = StringVar()
        source_entry = ctk.CTkEntry(
            route_frame, 
            placeholder_text="Enter source station",
            height=40,
            textvariable=source_var
        )
        source_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # Destination station
        destination_label = ctk.CTkLabel(route_frame, text="To")
        destination_label.grid(row=0, column=1, sticky="w", pady=(0, 5))

        destination_var = StringVar()
        destination_entry = ctk.CTkEntry(
            route_frame, 
            placeholder_text="Enter destination station",
            height=40,
            textvariable=destination_var
        )
        destination_entry.grid(row=1, column=1, sticky="ew")

        # Date selection
        date_label = ctk.CTkLabel(form_frame, text="Journey Date")
        date_label.pack(anchor="w", pady=(20, 5))

        date_frame = ctk.CTkFrame(form_frame)
        date_frame.pack(fill="x", pady=(0, 20))

        # Get tomorrow's date as default
        tomorrow = datetime.now() + timedelta(days=1)

        date_entry = DateEntry(
            date_frame, 
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            year=tomorrow.year,
            month=tomorrow.month,
            day=tomorrow.day
        )
        date_entry.pack(fill="both", expand=True)

        # Class selection
        class_label = ctk.CTkLabel(form_frame, text="Travel Class")
        class_label.pack(anchor="w", pady=(10, 10))

        class_var = StringVar(value="all")

        class_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        class_frame.pack(fill="x", pady=(0, 20))

        all_radio = ctk.CTkRadioButton(
            class_frame, 
            text="All Classes",
            variable=class_var,
            value="all"
        )
        all_radio.pack(side="left", padx=(0, 20))

        sleeper_radio = ctk.CTkRadioButton(
            class_frame, 
            text="Sleeper",
            variable=class_var,
            value="sleeper"
        )
        sleeper_radio.pack(side="left", padx=(0, 20))

        ac_radio = ctk.CTkRadioButton(
            class_frame, 
            text="AC",
            variable=class_var,
            value="ac"
        )
        ac_radio.pack(side="left", padx=(0, 20))

        general_radio = ctk.CTkRadioButton(
            class_frame, 
            text="General",
            variable=class_var,
            value="general"
        )
        general_radio.pack(side="left")

        # Search button
        search_button = ctk.CTkButton(
            form_frame,
            text="Search Trains",
            command=lambda: self.search_trains_for_booking(
                source_var.get(),
                destination_var.get(),
                date_entry.get_date(),
                class_var.get(),
                tabview
            ),
            height=45,
            corner_radius=10
        )
        search_button.pack(pady=20, fill="x")

        # Popular routes section
        popular_label = ctk.CTkLabel(
            scrollable_frame, 
            text="Popular Routes", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        popular_label.pack(anchor="w", padx=50, pady=(30, 10))

        # Popular routes grid
        routes_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        routes_frame.pack(fill="x", padx=50, pady=(0, 20))

        # Sample popular routes
        popular_routes = [
            ("Delhi", "Mumbai"), 
            ("Chennai", "Bangalore"), 
            ("Kolkata", "Delhi"), 
            ("Mumbai", "Pune")
        ]

        for i, (src, dest) in enumerate(popular_routes):
            route_button = ctk.CTkButton(
                routes_frame,
                text=f"{src} → {dest}",
                command=lambda s=src, d=dest: self.set_route(source_var, destination_var, s, d),
                fg_color="transparent",
                border_width=1,
                text_color=(THEME_COLORS["light"]["primary"], THEME_COLORS["dark"]["primary"]),
                height=30
            )
            route_button.grid(row=i//2, column=i%2, padx=10, pady=5, sticky="ew")

        routes_frame.grid_columnconfigure(0, weight=1)
        routes_frame.grid_columnconfigure(1, weight=1)
    
    def set_route(self, source_var, dest_var, source, destination):
        source_var.set(source)
        dest_var.set(destination)
    
    def search_trains_for_booking(self, source, destination, journey_date, travel_class, tabview):
        # Validate inputs
        if not source or not destination:
            CTkMessagebox(
                title="Input Error",
                message="Please enter both source and destination stations",
                icon="cancel"
            )
            return
        
        if source.lower() == destination.lower():
            CTkMessagebox(
                title="Input Error",
                message="Source and destination stations cannot be the same",
                icon="cancel"
            )
            return
        
        # Format date for database query
        journey_date_str = journey_date.strftime('%Y-%m-%d')
        
        # Store search parameters for later use
        self.search_params = {
            "source": source,
            "destination": destination,
            "journey_date": journey_date_str,
            "travel_class": travel_class
        }
        
        # Query database for matching trains
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                query = """
                    SELECT 
                        s.id, s.source, s.destination, s.departure_date, s.departure_time,
                        s.arrival_date, s.arrival_time,
                        s.fare_sleeper, s.fare_ac, s.fare_general, s.status, s.delay_minutes,
                        t.id as train_id, t.train_number, t.train_name,
                        t.total_seats_sleeper, t.total_seats_ac, t.total_seats_general
                    FROM 
                        schedules s
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        LOWER(s.source) = LOWER(%s) AND 
                        LOWER(s.destination) = LOWER(%s) AND 
                        s.departure_date = %s
                    ORDER BY 
                        s.departure_time
                """
                
                cursor.execute(query, (source, destination, journey_date_str))
                trains = cursor.fetchall()
                
                if not trains:
                    CTkMessagebox(
                        title="No Trains Found",
                        message=f"No trains found from {source} to {destination} on {journey_date_str}",
                        icon="warning"
                    )
                    return
                
                # Store search results
                self.search_results = trains
                
                # Setup and show results tab
                self.setup_search_results_tab(self.booking_tabs["results"], tabview, trains, travel_class)
                tabview.set("Search Results")
                
                # Enable results tab
                tabview.tab("Search Results").state(["!disabled"])
                
            except Exception as e:
                print(f"Error searching trains: {e}")
                CTkMessagebox(
                    title="Search Error",
                    message=f"Error searching for trains: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def setup_search_results_tab(self, parent, tabview, trains, travel_class):
        # Clear previous content
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Header with search details
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        search_details = self.search_params
        route_text = f"{search_details['source']} → {search_details['destination']}"
        date_text = f"Date: {search_details['journey_date']}"
        
        route_label = ctk.CTkLabel(
            header_frame,
            text=route_text,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        route_label.pack(side="left")
        
        date_label = ctk.CTkLabel(
            header_frame,
            text=date_text,
            font=ctk.CTkFont(size=14)
        )
        date_label.pack(side="right")
        
        # Filter frame
        filter_frame = ctk.CTkFrame(parent)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        filter_label = ctk.CTkLabel(filter_frame, text="Filter by:")
        filter_label.pack(side="left", padx=10)
        
        # Filter buttons
        all_button = ctk.CTkButton(
            filter_frame,
            text="All Classes",
            command=lambda: self.filter_search_results(parent, tabview, "all"),
            width=100,
            height=30,
            fg_color=THEME_COLORS[self.current_theme]["primary"] if travel_class == "all" else "gray"
        )
        all_button.pack(side="left", padx=5)
        
        sleeper_button = ctk.CTkButton(
            filter_frame,
            text="Sleeper",
            command=lambda: self.filter_search_results(parent, tabview, "sleeper"),
            width=100,
            height=30,
            fg_color=THEME_COLORS[self.current_theme]["primary"] if travel_class == "sleeper" else "gray"
        )
        sleeper_button.pack(side="left", padx=5)
        
        ac_button = ctk.CTkButton(
            filter_frame,
            text="AC",
            command=lambda: self.filter_search_results(parent, tabview, "ac"),
            width=100,
            height=30,
            fg_color=THEME_COLORS[self.current_theme]["primary"] if travel_class == "ac" else "gray"
        )
        ac_button.pack(side="left", padx=5)
        
        general_button = ctk.CTkButton(
            filter_frame,
            text="General",
            command=lambda: self.filter_search_results(parent, tabview, "general"),
            width=100,
            height=30,
            fg_color=THEME_COLORS[self.current_theme]["primary"] if travel_class == "general" else "gray"
        )
        general_button.pack(side="left", padx=5)
        
        # Sort options
        sort_label = ctk.CTkLabel(filter_frame, text="Sort by:")
        sort_label.pack(side="left", padx=(20, 10))
        
        sort_var = StringVar(value="departure_time")
        sort_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=["Departure Time", "Duration", "Price"],
            command=lambda x: self.sort_search_results(parent, tabview, x.lower().replace(" ", "_"), travel_class),
            variable=sort_var,
            width=120,
            height=30
        )
        sort_menu.pack(side="left", padx=5)
        
        # Results count
        count_label = ctk.CTkLabel(
            filter_frame,
            text=f"{len(trains)} trains found",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        count_label.pack(side="right", padx=10)
        
        # Create scroll frame for train results
        results_scroll = ctk.CTkScrollableFrame(parent)
        results_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Show train results
        self.display_train_search_results(results_scroll, tabview, trains, travel_class)
        
        # Back button
        back_button = ctk.CTkButton(
            parent,
            text="Back to Search",
            command=lambda: tabview.set("Search Trains"),
            width=150,
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        back_button.pack(side="left", padx=10, pady=10)
    
    def filter_search_results(self, parent, tabview, travel_class):
        # Update search params
        self.search_params["travel_class"] = travel_class
        
        # Rebuild the results tab with the new filter
        self.setup_search_results_tab(parent, tabview, self.search_results, travel_class)
    
    def sort_search_results(self, parent, tabview, sort_by, travel_class):
        sorted_results = list(self.search_results)
        
        if sort_by == "departure_time":
            sorted_results.sort(key=lambda x: (x['departure_date'], x['departure_time']))
        elif sort_by == "duration":
            # Calculate duration for each train
            for train in sorted_results:
                departure = datetime.combine(
                    train['departure_date'] if isinstance(train['departure_date'], datetime.date) else datetime.strptime(str(train['departure_date']), '%Y-%m-%d').date(),
                    train['departure_time'] if isinstance(train['departure_time'], datetime.time) else datetime.strptime(str(train['departure_time']), '%H:%M:%S').time()
                )
                arrival = datetime.combine(
                    train['arrival_date'] if isinstance(train['arrival_date'], datetime.date) else datetime.strptime(str(train['arrival_date']), '%Y-%m-%d').date(),
                    train['arrival_time'] if isinstance(train['arrival_time'], datetime.time) else datetime.strptime(str(train['arrival_time']), '%H:%M:%S').time()
                )
                train['duration'] = (arrival - departure).total_seconds()
            
            sorted_results.sort(key=lambda x: x['duration'])
        elif sort_by == "price":
            # Sort by the selected travel class price
            if travel_class == "sleeper" or travel_class == "all":
                sorted_results.sort(key=lambda x: float(x['fare_sleeper']))
            elif travel_class == "ac":
                sorted_results.sort(key=lambda x: float(x['fare_ac']))
            elif travel_class == "general":
                sorted_results.sort(key=lambda x: float(x['fare_general']))
        
        # Store sorted results and rebuild the tab
        self.search_results = sorted_results
        self.setup_search_results_tab(parent, tabview, sorted_results, travel_class)
    
    def display_train_search_results(self, container, tabview, trains, travel_class):
        # Display each train as a card
        for train in trains:
            # Create a card for the train
            train_card = ctk.CTkFrame(container)
            train_card.pack(fill="x", pady=5, padx=5)
            
            # Train info and status
            header_frame = ctk.CTkFrame(train_card, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(15, 10))
            
            train_info = f"{train['train_number']} - {train['train_name']}"
            train_label = ctk.CTkLabel(
                header_frame,
                text=train_info,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            train_label.pack(side="left")
            
            # Train status
            status_color = "#43a047"  # Default green for on-time
            status_text = "On Time"
            
            if train['status'] == 'delayed':
                status_color = "#ffb300"  # Orange for delayed
                status_text = f"Delayed {train['delay_minutes']} min"
            elif train['status'] == 'cancelled':
                status_color = "#e53935"  # Red for cancelled
                status_text = "Cancelled"
            
            status_label = ctk.CTkLabel(
                header_frame,
                text=status_text,
                font=ctk.CTkFont(size=14),
                text_color=status_color
            )
            status_label.pack(side="right")
            
            # Time and journey details
            time_frame = ctk.CTkFrame(train_card, fg_color="transparent")
            time_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # Departure info
            departure_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
            departure_frame.pack(side="left")
            
            departure_time = ctk.CTkLabel(
                departure_frame,
                text=train['departure_time'],
                font=ctk.CTkFont(size=18)
            )
            departure_time.pack(anchor="w")
            
            departure_date = ctk.CTkLabel(
                departure_frame,
                text=train['departure_date'],
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray70")
            )
            departure_date.pack(anchor="w")
            
            # Arrow
            arrow_label = ctk.CTkLabel(
                time_frame,
                text="→",
                font=ctk.CTkFont(size=18),
                text_color=THEME_COLORS[self.current_theme]["primary"]
            )
            arrow_label.pack(side="left", padx=20)
            
            # Arrival info
            arrival_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
            arrival_frame.pack(side="left")
            
            arrival_time = ctk.CTkLabel(
                arrival_frame,
                text=train['arrival_time'],
                font=ctk.CTkFont(size=18)
            )
            arrival_time.pack(anchor="w")
            
            arrival_date = ctk.CTkLabel(
                arrival_frame,
                text=train['arrival_date'],
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray70")
            )
            arrival_date.pack(anchor="w")
            
            # Duration
            try:
                departure_datetime = datetime.combine(
                    train['departure_date'] if isinstance(train['departure_date'], datetime.date) else datetime.strptime(str(train['departure_date']), '%Y-%m-%d').date(),
                    train['departure_time'] if isinstance(train['departure_time'], datetime.time) else datetime.strptime(str(train['departure_time']), '%H:%M:%S').time()
                )
                arrival_datetime = datetime.combine(
                    train['arrival_date'] if isinstance(train['arrival_date'], datetime.date) else datetime.strptime(str(train['arrival_date']), '%Y-%m-%d').date(),
                    train['arrival_time'] if isinstance(train['arrival_time'], datetime.time) else datetime.strptime(str(train['arrival_time']), '%H:%M:%S').time()
                )
                
                # Calculate duration
                duration = arrival_datetime - departure_datetime
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                duration_text = f"{int(hours)}h {int(minutes)}m"
            except:
                duration_text = "N/A"
            
            duration_label = ctk.CTkLabel(
                time_frame,
                text=f"Duration: {duration_text}",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray70")
            )
            duration_label.pack(side="right")
            
            # Price and booking
            bottom_frame = ctk.CTkFrame(train_card, fg_color="transparent")
            bottom_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            # Seats info
            seats_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
            seats_frame.pack(side="left")
            
            # Check available seats (simplified for demo - would normally query for actual available seats)
            # In a real app, you'd calculate available seats by checking existing bookings
            available_sleeper = train['total_seats_sleeper']
            available_ac = train['total_seats_ac']
            available_general = train['total_seats_general']
            
            seats_label = ctk.CTkLabel(
                seats_frame,
                text=f"Available Seats - Sleeper: {available_sleeper} | AC: {available_ac} | General: {available_general}",
                font=ctk.CTkFont(size=12)
            )
            seats_label.pack(anchor="w")
            
            # Price and book button
            price_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
            price_frame.pack(side="right")
            
            # Show price based on selected class
            if travel_class == "sleeper" or travel_class == "all":
                price = train['fare_sleeper']
                price_class = "Sleeper"
            elif travel_class == "ac":
                price = train['fare_ac']
                price_class = "AC"
            elif travel_class == "general":
                price = train['fare_general']
                price_class = "General"
            else:
                price = train['fare_sleeper']  # Default to sleeper
                price_class = "Sleeper"
            
            price_label = ctk.CTkLabel(
                price_frame,
                text=f"{price_class}: {format_currency(price)}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            price_label.pack(side="left", padx=(0, 10))
            
            # Book button (disabled if train is cancelled)
            book_button = ctk.CTkButton(
                price_frame,
                text="Book Now",
                width=100,
                height=30,
                command=lambda t=train, c=travel_class: self.start_passenger_details(t, c, tabview),
                state="normal" if train['status'] != 'cancelled' else "disabled"
            )
            book_button.pack(side="left")
    
    def start_passenger_details(self, train, travel_class, tabview):
        # Store selected train and class for later use
        self.selected_train = train
        self.selected_class = travel_class if travel_class != "all" else "sleeper"  # Default to sleeper if "all" was selected
        
        # Setup passenger details tab
        self.setup_passenger_details_tab(self.booking_tabs["passengers"], tabview)
        
        # Enable passenger details tab and switch to it by directly setting the tab
        tabview.set("Passenger Details")
    
    def setup_passenger_details_tab(self, parent, tabview):
        # Clear previous content
        for widget in parent.winfo_children():
            widget.destroy()
        
        self.total_fare_var = StringVar()

        # Header with train details
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        train = self.selected_train
        travel_class = self.selected_class.capitalize()
        
        # Train info
        train_label = ctk.CTkLabel(
            header_frame,
            text=f"{train['train_number']} - {train['train_name']}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        train_label.pack(anchor="w")
        
        # Journey details
        journey_label = ctk.CTkLabel(
            header_frame,
            text=f"{train['source']} → {train['destination']} | {train['departure_date']} {train['departure_time']} | Class: {travel_class}",
            font=ctk.CTkFont(size=14)
        )
        journey_label.pack(anchor="w", pady=(5, 0))
        
        # Get fare for selected class
        if self.selected_class == "sleeper":
            fare = float(train['fare_sleeper'])
        elif self.selected_class == "ac":
            fare = float(train['fare_ac'])
        else:  # general
            fare = float(train['fare_general'])
        
        # Fare display
        fare_label = ctk.CTkLabel(
            header_frame,
            text=f"Fare per passenger: {format_currency(fare)}",
            font=ctk.CTkFont(size=14),
            text_color=THEME_COLORS[self.current_theme]["primary"]
        )
        fare_label.pack(anchor="w", pady=(5, 0))

        self.total_fare_var.set(format_currency(fare))
        
        # Passenger details section
        details_frame = ctk.CTkFrame(parent)
        details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            details_frame,
            text="Passenger Details",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=15)
        
        # Number of passengers
        passenger_count_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        passenger_count_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        count_label = ctk.CTkLabel(
            passenger_count_frame,
            text="Number of Passengers:",
            font=ctk.CTkFont(size=14)
        )
        count_label.pack(side="left")
        
        # Create a custom frame for counter with +/- buttons
        counter_frame = ctk.CTkFrame(passenger_count_frame)
        counter_frame.pack(side="left", padx=10)
        
        self.passenger_count = IntVar(value=1)
        
        def update_count(delta):
            new_value = self.passenger_count.get() + delta
            if 1 <= new_value <= 6:  # Limit to 6 passengers
                self.passenger_count.set(new_value)
                self.recreate_passenger_forms(passenger_forms_container)
        
        minus_button = ctk.CTkButton(
            counter_frame,
            text="-",
            width=30,
            height=30,
            command=lambda: update_count(-1)
        )
        minus_button.pack(side="left")
        
        count_display = ctk.CTkLabel(
            counter_frame,
            textvariable=self.passenger_count,
            width=30,
            height=30
        )
        count_display.pack(side="left", padx=10)
        
        plus_button = ctk.CTkButton(
            counter_frame,
            text="+",
            width=30,
            height=30,
            command=lambda: update_count(1)
        )
        plus_button.pack(side="left")
        
        # Max passengers note
        max_note = ctk.CTkLabel(
            passenger_count_frame,
            text="(Maximum 6 passengers per booking)",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        max_note.pack(side="left", padx=10)
        
        # Passenger forms container (scrollable)
        passenger_forms_scroll = ctk.CTkScrollableFrame(details_frame)
        passenger_forms_scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        passenger_forms_container = ctk.CTkFrame(passenger_forms_scroll, fg_color="transparent")
        passenger_forms_container.pack(fill="x")
        
        # Create initial passenger form
        self.recreate_passenger_forms(passenger_forms_container)
        
        # Total fare and buttons
        bottom_frame = ctk.CTkFrame(parent)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        
        # Back button
        back_button = ctk.CTkButton(
            bottom_frame,
            text="Back to Results",
            command=lambda: tabview.set("Search Results"),
            width=150,
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        back_button.pack(side="left", padx=10, pady=10)
        
        # Calculate total fare
        self.total_fare_var = StringVar(value=format_currency(fare))
        total_fare_label = ctk.CTkLabel(
            bottom_frame,
            text="Total Fare:",
            font=ctk.CTkFont(size=14)
        )
        total_fare_label.pack(side="left", padx=(20, 5))
        
        total_fare_value = ctk.CTkLabel(
            bottom_frame,
            textvariable=self.total_fare_var,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        total_fare_value.pack(side="left")
        
        # Continue to payment button
        continue_button = ctk.CTkButton(
            bottom_frame,
            text="Continue to Payment",
            command=lambda: self.validate_and_proceed_to_payment(tabview),
            width=180,
            height=35
        )
        continue_button.pack(side="right", padx=10, pady=10)
        
        # Update total fare when passenger count changes
        self.passenger_count.trace_add("write", lambda *args: self.update_total_fare())
    
    def recreate_passenger_forms(self, container):
        # Clear existing forms
        for widget in container.winfo_children():
            widget.destroy()
        
        # Store passenger form fields
        self.passenger_forms = []
        
        # Create forms based on passenger count
        for i in range(1, self.passenger_count.get() + 1):
            passenger_frame = ctk.CTkFrame(container)
            passenger_frame.pack(fill="x", pady=10)
            
            # Title for each passenger
            title_label = ctk.CTkLabel(
                passenger_frame,
                text=f"Passenger {i}" + (" (Lead Passenger)" if i == 1 else ""),
                font=ctk.CTkFont(weight="bold")
            )
            title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 15), sticky="w")
            
            # Name
            name_label = ctk.CTkLabel(passenger_frame, text="Full Name:")
            name_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            
            name_entry = ctk.CTkEntry(passenger_frame, width=200)
            name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
            
            # Age
            age_label = ctk.CTkLabel(passenger_frame, text="Age:")
            age_label.grid(row=1, column=2, padx=10, pady=5, sticky="w")
            
            age_entry = ctk.CTkEntry(passenger_frame, width=80)
            age_entry.grid(row=1, column=3, padx=10, pady=5, sticky="w")
            
            # Gender
            gender_label = ctk.CTkLabel(passenger_frame, text="Gender:")
            gender_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            
            gender_var = StringVar(value="male")
            
            gender_frame = ctk.CTkFrame(passenger_frame, fg_color="transparent")
            gender_frame.grid(row=2, column=1, padx=10, pady=5, sticky="w")
            
            male_radio = ctk.CTkRadioButton(
                gender_frame, 
                text="Male",
                variable=gender_var,
                value="male"
            )
            male_radio.pack(side="left", padx=(0, 20))
            
            female_radio = ctk.CTkRadioButton(
                gender_frame, 
                text="Female",
                variable=gender_var,
                value="female"
            )
            female_radio.pack(side="left", padx=(0, 20))
            
            other_radio = ctk.CTkRadioButton(
                gender_frame, 
                text="Other",
                variable=gender_var,
                value="other"
            )
            other_radio.pack(side="left")
            
            # Seat preference
            seat_label = ctk.CTkLabel(passenger_frame, text="Seat Preference:")
            seat_label.grid(row=2, column=2, padx=10, pady=5, sticky="w")
            
            seat_var = StringVar(value="no_preference")
            
            seat_frame = ctk.CTkFrame(passenger_frame, fg_color="transparent")
            seat_frame.grid(row=2, column=3, padx=10, pady=5, sticky="w")
            
            seat_menu = ctk.CTkOptionMenu(
                seat_frame,
                values=["No Preference", "Window", "Aisle"],
                variable=seat_var,
                width=120
            )
            seat_menu.pack()
            
            # Store form fields
            self.passenger_forms.append({
                "name_entry": name_entry,
                "age_entry": age_entry,
                "gender_var": gender_var,
                "seat_var": seat_var
            })
        
        # Update total fare
        self.update_total_fare()
    
    def update_total_fare(self):

        # Check if the attribute exists first
        if not hasattr(self, 'total_fare_var') or self.total_fare_var is None:
            self.total_fare_var = StringVar(value="₹0.00")

        # Get base fare for selected class
        if self.selected_class == "sleeper":
            fare = float(self.selected_train['fare_sleeper'])
        elif self.selected_class == "ac":
            fare = float(self.selected_train['fare_ac'])
        else:  # general
            fare = float(self.selected_train['fare_general'])
        
        # Calculate total fare based on passenger count
        total = fare * self.passenger_count.get()
        
        # Update display
        self.total_fare_var.set(format_currency(total))
    
    def validate_and_proceed_to_payment(self, tabview):
        # Validate all passenger forms
        passengers_data = []
        
        for i, form in enumerate(self.passenger_forms):
            name = form["name_entry"].get().strip()
            age_str = form["age_entry"].get().strip()
            gender = form["gender_var"].get()
            seat_preference = form["seat_var"].get()
            
            # Validate inputs
            if not name:
                CTkMessagebox(
                    title="Validation Error",
                    message=f"Please enter name for Passenger {i+1}",
                    icon="cancel"
                )
                return
            
            if not age_str:
                CTkMessagebox(
                    title="Validation Error",
                    message=f"Please enter age for Passenger {i+1}",
                    icon="cancel"
                )
                return
            
            try:
                age = int(age_str)
                if age <= 0 or age > 120:
                    raise ValueError("Age must be between 1 and 120")
            except ValueError:
                CTkMessagebox(
                    title="Validation Error",
                    message=f"Please enter a valid age for Passenger {i+1}",
                    icon="cancel"
                )
                return
            
            # Store valid passenger data
            passengers_data.append({
                "name": name,
                "age": age,
                "gender": gender,
                "seat_preference": seat_preference
            })
        
        # Store passenger data for payment
        self.passengers_data = passengers_data
        
        # Setup payment tab
        self.setup_payment_tab(self.booking_tabs["payment"], tabview)
        
        # Enable payment tab and switch to it
        tabview.set("Payment")
    
    def setup_payment_tab(self, parent, tabview):
        # Clear previous content
        for widget in parent.winfo_children():
            widget.destroy()

        # Create a scrollable frame for the payment tab
        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header with summary
        header_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        # Booking summary title
        summary_title = ctk.CTkLabel(
            header_frame,
            text="Booking Summary",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        summary_title.pack(anchor="w")

        # Train details
        train = self.selected_train
        travel_class = self.selected_class.capitalize()

        train_label = ctk.CTkLabel(
            header_frame,
            text=f"{train['train_number']} - {train['train_name']}",
            font=ctk.CTkFont(size=16)
        )
        train_label.pack(anchor="w", pady=(10, 0))

        journey_label = ctk.CTkLabel(
            header_frame,
            text=f"{train['source']} → {train['destination']} | {train['departure_date']} {train['departure_time']} | Class: {travel_class}",
            font=ctk.CTkFont(size=14)
        )
        journey_label.pack(anchor="w", pady=(5, 0))

        # Passenger count
        passenger_label = ctk.CTkLabel(
            header_frame,
            text=f"Passengers: {self.passenger_count.get()}",
            font=ctk.CTkFont(size=14)
        )
        passenger_label.pack(anchor="w", pady=(5, 0))

        # Total fare
        total_fare_label = ctk.CTkLabel(
            header_frame,
            text=f"Total Fare: {self.total_fare_var.get()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=THEME_COLORS[self.current_theme]["primary"]
        )
        total_fare_label.pack(anchor="w", pady=(5, 10))

        # Payment details section
        payment_frame = ctk.CTkFrame(scrollable_frame)
        payment_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Payment title
        payment_title = ctk.CTkLabel(
            payment_frame,
            text="Payment Details",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        payment_title.pack(anchor="w", padx=15, pady=15)

        # Payment form
        form_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Payment method
        method_label = ctk.CTkLabel(
            form_frame,
            text="Payment Method:",
            font=ctk.CTkFont(size=14)
        )
        method_label.pack(anchor="w", pady=(0, 10))

        self.payment_method = StringVar(value="credit_card")

        # Credit Card
        cc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        cc_frame.pack(fill="x", pady=5)

        cc_radio = ctk.CTkRadioButton(
            cc_frame, 
            text="Credit Card",
            variable=self.payment_method,
            value="credit_card",
            command=lambda: self.show_payment_form("credit_card", payment_details_frame)
        )
        cc_radio.pack(anchor="w")

        # Debit Card
        dc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        dc_frame.pack(fill="x", pady=5)

        dc_radio = ctk.CTkRadioButton(
            dc_frame, 
            text="Debit Card",
            variable=self.payment_method,
            value="debit_card",
            command=lambda: self.show_payment_form("debit_card", payment_details_frame)
        )
        dc_radio.pack(anchor="w")

        # Net Banking
        nb_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        nb_frame.pack(fill="x", pady=5)

        nb_radio = ctk.CTkRadioButton(
            nb_frame, 
            text="Net Banking",
            variable=self.payment_method,
            value="net_banking",
            command=lambda: self.show_payment_form("net_banking", payment_details_frame)
        )
        nb_radio.pack(anchor="w")

        # UPI
        upi_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        upi_frame.pack(fill="x", pady=5)

        upi_radio = ctk.CTkRadioButton(
            upi_frame, 
            text="UPI",
            variable=self.payment_method,
            value="upi",
            command=lambda: self.show_payment_form("upi", payment_details_frame)
        )
        upi_radio.pack(anchor="w")

        # Create a container for the dynamically changing payment details form
        payment_details_frame = ctk.CTkFrame(payment_frame, fg_color="transparent")
        payment_details_frame.pack(fill="x", padx=15, pady=15)

        # Show initial form
        self.show_payment_form("credit_card", payment_details_frame)

        # Terms and conditions
        terms_var = IntVar(value=0)
        terms_checkbox = ctk.CTkCheckBox(
            payment_frame, 
            text="I agree to the Terms and Conditions", 
            variable=terms_var,
            checkbox_width=20,
            checkbox_height=20
        )
        terms_checkbox.pack(anchor="w", padx=15, pady=(20, 10))

        # Bottom buttons
        buttons_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)

        # Back button
        back_button = ctk.CTkButton(
            buttons_frame,
            text="Back",
            command=lambda: tabview.set("Passenger Details"),
            width=100,
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        back_button.pack(side="left", padx=10, pady=10)

        # Make Payment button
        pay_button = ctk.CTkButton(
            buttons_frame,
            text="Make Payment",
            command=lambda: self.process_payment(terms_var.get()),
            width=150,
            height=40
        )
        pay_button.pack(side="right", padx=10, pady=10)
    
    def show_payment_form(self, payment_type, container):
        # Clear previous content
        for widget in container.winfo_children():
            widget.destroy()
        
        # Store the payment details fields
        self.payment_fields = {}
        
        if payment_type in ["credit_card", "debit_card"]:
            # Card number
            card_label = ctk.CTkLabel(container, text="Card Number:")
            card_label.pack(anchor="w", pady=(0, 5))
            
            card_entry = ctk.CTkEntry(container, width=300, placeholder_text="Enter 16-digit card number")
            card_entry.pack(fill="x", pady=(0, 10))
            self.payment_fields["card_number"] = card_entry
            
            # Card details row
            card_details = ctk.CTkFrame(container, fg_color="transparent")
            card_details.pack(fill="x", pady=(0, 10))
            card_details.grid_columnconfigure(0, weight=1)
            card_details.grid_columnconfigure(1, weight=1)
            
            # Expiry date
            expiry_label = ctk.CTkLabel(card_details, text="Expiry Date (MM/YY):")
            expiry_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
            
            expiry_entry = ctk.CTkEntry(card_details, placeholder_text="MM/YY")
            expiry_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5))
            self.payment_fields["expiry"] = expiry_entry
            
            # CVV
            cvv_label = ctk.CTkLabel(card_details, text="CVV:")
            cvv_label.grid(row=0, column=1, sticky="w", pady=(0, 5), padx=(5, 0))
            
            cvv_entry = ctk.CTkEntry(card_details, placeholder_text="XXX", width=100)
            cvv_entry.grid(row=1, column=1, sticky="w", padx=(5, 0))
            self.payment_fields["cvv"] = cvv_entry
            
            # Cardholder name
            name_label = ctk.CTkLabel(container, text="Cardholder Name:")
            name_label.pack(anchor="w", pady=(0, 5))
            
            name_entry = ctk.CTkEntry(container, width=300, placeholder_text="Enter name as on card")
            name_entry.pack(fill="x", pady=(0, 10))
            self.payment_fields["name"] = name_entry
            
        elif payment_type == "net_banking":
            # Bank selection
            bank_label = ctk.CTkLabel(container, text="Select Bank:")
            bank_label.pack(anchor="w", pady=(0, 5))
            
            bank_var = StringVar(value="None")
            
            banks = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank", "Other"]
            bank_menu = ctk.CTkOptionMenu(
                container,
                values=banks,
                variable=bank_var,
                width=300
            )
            bank_menu.pack(fill="x", pady=(0, 10))
            self.payment_fields["bank"] = bank_var
            
        elif payment_type == "upi":
            # UPI ID
            upi_label = ctk.CTkLabel(container, text="UPI ID:")
            upi_label.pack(anchor="w", pady=(0, 5))
            
            upi_entry = ctk.CTkEntry(container, width=300, placeholder_text="yourname@upi")
            upi_entry.pack(fill="x", pady=(0, 10))
            self.payment_fields["upi_id"] = upi_entry
            
            # UPI verification note
            note_label = ctk.CTkLabel(
                container,
                text="You will receive a payment request on your UPI app.",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray70")
            )
            note_label.pack(anchor="w", pady=(5, 0))
    
    def process_payment(self, terms_agreed):
        # Validate terms agreement
        if not terms_agreed:
            CTkMessagebox(
                title="Terms Required",
                message="Please agree to the Terms and Conditions to proceed",
                icon="cancel"
            )
            return

        # Validate payment details based on method
        payment_method = self.payment_method.get()

        if payment_method in ["credit_card", "debit_card"]:
            card_number_entry = self.payment_fields.get("card_number")
            card_number = card_number_entry.get().strip() if card_number_entry else ""

            expiry_entry = self.payment_fields.get("expiry")
            expiry = expiry_entry.get().strip() if expiry_entry else ""

            cvv_entry = self.payment_fields.get("cvv")
            cvv = cvv_entry.get().strip() if cvv_entry else ""

            name_entry = self.payment_fields.get("name")
            name = name_entry.get().strip() if name_entry else ""

            if not card_number or not expiry or not cvv or not name:
                CTkMessagebox(
                    title="Validation Error",
                    message="Please fill in all card details",
                    icon="cancel"
                )
                return

            # Basic card validation
            if not card_number.isdigit() or len(card_number) != 16:
                CTkMessagebox(
                    title="Validation Error",
                    message="Please enter a valid 16-digit card number",
                    icon="cancel"
                )
                return

            # Very simple expiry validation (MM/YY format)
            if not re.match(r'^(0[1-9]|1[0-2])/\d{2}$', expiry):
                CTkMessagebox(
                    title="Validation Error",
                    message="Please enter a valid expiry date in MM/YY format",
                    icon="cancel"
                )
                return

            # CVV validation
            if not cvv.isdigit() or not (3 <= len(cvv) <= 4):
                CTkMessagebox(
                    title="Validation Error",
                    message="Please enter a valid CVV (3 or 4 digits)",
                    icon="cancel"
                )
                return

        elif payment_method == "net_banking":
            bank = self.payment_fields.get("bank").get() if self.payment_fields.get("bank") else None

            if not bank or bank == "None":
                CTkMessagebox(
                    title="Validation Error",
                    message="Please select a bank",
                    icon="cancel"
                )
                return

        elif payment_method == "upi":
            upi_entry = self.payment_fields.get("upi_id")
            upi_id = upi_entry.get().strip() if upi_entry else ""

            if not upi_id or "@" not in upi_id:
                CTkMessagebox(
                    title="Validation Error",
                    message="Please enter a valid UPI ID",
                    icon="cancel"
                )
                return

        # Show payment processing dialog
        self.show_payment_processing()
    
    def show_payment_processing(self):
        # Create processing dialog
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Processing Payment")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Progress message
        msg_label = ctk.CTkLabel(
            dialog,
            text="Processing your payment...",
            font=ctk.CTkFont(size=16)
        )
        msg_label.pack(pady=(40, 20))
        
        # Progress bar
        progress = ctk.CTkProgressBar(dialog, width=300)
        progress.pack(pady=10)
        progress.set(0)
        
        # Simulate payment processing
        def update_progress():
            for i in range(1, 11):
                progress.set(i / 10)
                
                if i == 3:
                    msg_label.configure(text="Validating payment details...")
                elif i == 6:
                    msg_label.configure(text="Processing transaction...")
                elif i == 9:
                    msg_label.configure(text="Completing booking...")
                
                dialog.update()
                dialog.after(300)
            
            dialog.destroy()
            self.complete_booking()
        
        # Start progress after a short delay
        dialog.after(500, update_progress)
    
    def complete_booking(self):
        # Get base fare for selected class
        if self.selected_class == "sleeper":
            fare = float(self.selected_train['fare_sleeper'])
        elif self.selected_class == "ac":
            fare = float(self.selected_train['fare_ac'])
        else:  # general
            fare = float(self.selected_train['fare_general'])
        
        # Calculate total fare
        total_fare = fare * len(self.passengers_data)
        
        # Save booking to database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Begin transaction
                connection.start_transaction()
                
                # Generate PNR
                pnr = generate_pnr()
                
                # Insert booking
                cursor.execute(
                    """
                    INSERT INTO bookings 
                    (user_id, schedule_id, pnr, total_fare, status, payment_method)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.current_user['id'],
                        self.selected_train['id'],
                        pnr,
                        total_fare,
                        'confirmed',
                        self.payment_method.get()
                    )
                )
                
                # Get booking ID
                booking_id = cursor.lastrowid
                
                # Insert passengers
                for passenger in self.passengers_data:
                    cursor.execute(
                        """
                        INSERT INTO passengers
                        (booking_id, name, age, gender, seat_class)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            booking_id,
                            passenger['name'],
                            passenger['age'],
                            passenger['gender'],
                            self.selected_class
                        )
                    )
                
                # Commit transaction
                connection.commit()
                
                # Show success message
                self.show_booking_confirmation(pnr)
                
            except Exception as e:
                connection.rollback()
                print(f"Error completing booking: {e}")
                
                CTkMessagebox(
                    title="Booking Error",
                    message=f"Failed to complete booking: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def show_booking_confirmation(self, pnr):
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Booking Confirmed")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Success icon
        try:
            success_img = load_image("assets/success_icon.png", (64, 64))
            success_icon = ctk.CTkLabel(dialog, image=success_img, text="")
            success_icon.image = success_img
            success_icon.pack(pady=(30, 0))
        except:
            pass
        
        # Success message
        success_msg = ctk.CTkLabel(
            dialog,
            text="Booking Confirmed!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=THEME_COLORS[self.current_theme]["success"]
        )
        success_msg.pack(pady=(10, 20))
        
        # PNR details
        pnr_frame = ctk.CTkFrame(dialog)
        pnr_frame.pack(fill="x", padx=40, pady=10)
        
        pnr_label = ctk.CTkLabel(
            pnr_frame,
            text="PNR Number:",
            font=ctk.CTkFont(size=14)
        )
        pnr_label.pack(side="left", padx=10, pady=10)
        
        pnr_value = ctk.CTkLabel(
            pnr_frame,
            text=pnr,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        pnr_value.pack(side="right", padx=10, pady=10)
        
        # Train details
        train_info = ctk.CTkLabel(
            dialog,
            text=f"{self.selected_train['train_number']} - {self.selected_train['train_name']}",
            font=ctk.CTkFont(size=16)
        )
        train_info.pack(pady=(10, 0))
        
        journey_info = ctk.CTkLabel(
            dialog,
            text=f"{self.selected_train['source']} → {self.selected_train['destination']}",
            font=ctk.CTkFont(size=14)
        )
        journey_info.pack(pady=(5, 0))
        
        date_info = ctk.CTkLabel(
            dialog,
            text=f"Date: {self.selected_train['departure_date']} | Time: {self.selected_train['departure_time']}",
            font=ctk.CTkFont(size=14)
        )
        date_info.pack(pady=(5, 0))
        
        passengers_info = ctk.CTkLabel(
            dialog,
            text=f"Passengers: {len(self.passengers_data)} | Class: {self.selected_class.capitalize()}",
            font=ctk.CTkFont(size=14)
        )
        passengers_info.pack(pady=(5, 20))
        
        # Note
        note_label = ctk.CTkLabel(
            dialog,
            text="You can view your booking details in the 'My Bookings' section",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        note_label.pack(pady=(10, 0))
        
        # Close and View Booking buttons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=40, pady=(20, 30))
        
        close_button = ctk.CTkButton(
            buttons_frame,
            text="Close",
            command=lambda: [dialog.destroy(), self.show_user_dashboard()],
            height=35,
            fg_color="gray",
            hover_color="gray30"
        )
        close_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        view_button = ctk.CTkButton(
            buttons_frame,
            text="View Booking",
            command=lambda: [dialog.destroy(), self.show_booking_details_dialog(pnr), self.show_user_bookings_screen()],
            height=35
        )
        view_button.pack(side="right", fill="x", expand=True, padx=(5, 0))
    
    def show_user_bookings_screen(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # User name and role
        user_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        user_name = ctk.CTkLabel(
            user_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_name.pack(anchor="w")
        
        user_role = ctk.CTkLabel(
            user_frame, 
            text="Passenger", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        user_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_user_dashboard, "assets/dashboard_icon.png"),
            ("Book Tickets", lambda: self.show_user_tab("book"), "assets/ticket_icon.png"),
            ("My Bookings", lambda: self.show_user_tab("bookings"), "assets/booking_icon.png"),
            ("Train Schedule", lambda: self.show_user_tab("schedule"), "assets/schedule_icon.png"),
            ("My Profile", lambda: self.show_user_tab("profile"), "assets/profile_icon.png"),
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "My Bookings" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "My Bookings" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="My Bookings", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Bookings content
        bookings_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        bookings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs for different booking types
        tabview = ctk.CTkTabview(bookings_frame)
        tabview.pack(fill="both", expand=True)
        
        # Add tabs
        upcoming_tab = tabview.add("Upcoming Journeys")
        completed_tab = tabview.add("Completed Journeys")
        cancelled_tab = tabview.add("Cancelled Bookings")
        
        # Load bookings for each tab
        self.load_user_bookings(upcoming_tab, "upcoming")
        self.load_user_bookings(completed_tab, "completed")
        self.load_user_bookings(cancelled_tab, "cancelled")
    
    def load_user_bookings(self, parent, booking_type):
        # Create scrollable frame
        bookings_scroll = ctk.CTkScrollableFrame(parent)
        bookings_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        # Get user bookings
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                if booking_type == "upcoming":
                    # Get upcoming journeys
                    cursor.execute("""
                        SELECT 
                            b.id, b.pnr, b.booking_date, b.total_fare, b.status,
                            t.train_number, t.train_name,
                            s.source, s.destination, s.departure_date, s.departure_time,
                            s.arrival_date, s.arrival_time, s.status as train_status, s.delay_minutes
                        FROM 
                            bookings b
                        JOIN 
                            schedules s ON b.schedule_id = s.id
                        JOIN 
                            trains t ON s.train_id = t.id
                        WHERE 
                            b.user_id = %s AND
                            b.status = 'confirmed' AND
                            (s.departure_date > %s OR (s.departure_date = %s AND s.departure_time >= %s))
                        ORDER BY 
                            s.departure_date, s.departure_time
                    """, (self.current_user['id'], current_date, current_date, current_time))
                elif booking_type == "completed":
                    # Get completed journeys
                    cursor.execute("""
                        SELECT 
                            b.id, b.pnr, b.booking_date, b.total_fare, b.status,
                            t.train_number, t.train_name,
                            s.source, s.destination, s.departure_date, s.departure_time,
                            s.arrival_date, s.arrival_time, s.status as train_status, s.delay_minutes
                        FROM 
                            bookings b
                        JOIN 
                            schedules s ON b.schedule_id = s.id
                        JOIN 
                            trains t ON s.train_id = t.id
                        WHERE 
                            b.user_id = %s AND
                            b.status = 'confirmed' AND
                            (s.departure_date < %s OR (s.departure_date = %s AND s.departure_time < %s))
                        ORDER BY 
                            s.departure_date DESC, s.departure_time DESC
                    """, (self.current_user['id'], current_date, current_date, current_time))
                elif booking_type == "cancelled":
                    # Get cancelled bookings
                    cursor.execute("""
                        SELECT 
                            b.id, b.pnr, b.booking_date, b.total_fare, b.status,
                            t.train_number, t.train_name,
                            s.source, s.destination, s.departure_date, s.departure_time,
                            s.arrival_date, s.arrival_time, s.status as train_status, s.delay_minutes
                        FROM 
                            bookings b
                        JOIN 
                            schedules s ON b.schedule_id = s.id
                        JOIN 
                            trains t ON s.train_id = t.id
                        WHERE 
                            b.user_id = %s AND
                            b.status = 'cancelled'
                        ORDER BY 
                            b.booking_date DESC
                    """, (self.current_user['id'],))
                
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_bookings_label = ctk.CTkLabel(
                        bookings_scroll, 
                        text=f"No {booking_type} bookings found",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_bookings_label.pack(pady=20)
                    
                    # Show Book Now button if no upcoming bookings
                    if booking_type == "upcoming":
                        book_now_button = ctk.CTkButton(
                            bookings_scroll,
                            text="Book a Ticket Now",
                            command=lambda: self.show_user_tab("book"),
                            height=40
                        )
                        book_now_button.pack(pady=10)
                    
                    return
                
                # Display bookings
                for booking in bookings:
                    booking_frame = ctk.CTkFrame(bookings_scroll)
                    booking_frame.pack(fill="x", pady=10)
                    
                    # Top row with train info and status
                    top_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    top_frame.pack(fill="x", padx=15, pady=(15, 5))
                    
                    train_info = ctk.CTkLabel(
                        top_frame,
                        text=f"{booking['train_number']} - {booking['train_name']}",
                        font=ctk.CTkFont(size=16, weight="bold")
                    )
                    train_info.pack(side="left")
                    
                    # Status badge
                    status_color = "#43a047" if booking['status'] == "confirmed" else "#e53935"
                    status_text = "Confirmed" if booking['status'] == "confirmed" else "Cancelled"
                    
                    status_badge = ctk.CTkLabel(
                        top_frame,
                        text=status_text,
                        text_color="white",
                        fg_color=status_color,
                        corner_radius=5,
                        width=80,
                        height=25
                    )
                    status_badge.pack(side="right")
                    
                    # PNR row
                    pnr_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    pnr_frame.pack(fill="x", padx=15, pady=(0, 5))
                    
                    pnr_label = ctk.CTkLabel(
                        pnr_frame,
                        text=f"PNR: {booking['pnr']}",
                        font=ctk.CTkFont(size=13)
                    )
                    pnr_label.pack(side="left")
                    
                    booking_date = ctk.CTkLabel(
                        pnr_frame,
                        text=f"Booked on: {booking['booking_date']}",
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")
                    )
                    booking_date.pack(side="right")
                    
                    # Route and time
                    route_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    route_frame.pack(fill="x", padx=15, pady=(5, 5))
                    
                    route_info = ctk.CTkLabel(
                        route_frame,
                        text=f"{booking['source']} → {booking['destination']}",
                        font=ctk.CTkFont(size=14)
                    )
                    route_info.pack(side="left")
                    
                    # Train status for upcoming journeys
                    if booking_type == "upcoming":
                        status_color = "#43a047"  # Default green for on-time
                        status_text = "On Time"
                        
                        if booking['train_status'] == 'delayed':
                            status_color = "#ffb300"  # Orange for delayed
                            status_text = f"Delayed {booking['delay_minutes']} min"
                        elif booking['train_status'] == 'cancelled':
                            status_color = "#e53935"  # Red for cancelled
                            status_text = "Train Cancelled"
                        
                        train_status = ctk.CTkLabel(
                            route_frame,
                            text=status_text,
                            font=ctk.CTkFont(size=12),
                            text_color=status_color
                        )
                        train_status.pack(side="right")
                    
                    # Departure and arrival info
                    time_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    time_frame.pack(fill="x", padx=15, pady=(0, 5))
                    
                    departure_info = ctk.CTkLabel(
                        time_frame,
                        text=f"Departure: {booking['departure_date']} {booking['departure_time']}",
                        font=ctk.CTkFont(size=12)
                    )
                    departure_info.pack(side="left")
                    
                    arrival_info = ctk.CTkLabel(
                        time_frame,
                        text=f"Arrival: {booking['arrival_date']} {booking['arrival_time']}",
                        font=ctk.CTkFont(size=12)
                    )
                    arrival_info.pack(side="right")
                    
                    # Bottom row with fare and actions
                    bottom_frame = ctk.CTkFrame(booking_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", padx=15, pady=(5, 15))
                    
                    fare_label = ctk.CTkLabel(
                        bottom_frame,
                        text=f"Total Fare: {format_currency(booking['total_fare'])}",
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
                    fare_label.pack(side="left")
                    
                    # View Details button
                    view_button = ctk.CTkButton(
                        bottom_frame,
                        text="View Details",
                        width=120,
                        height=30,
                        command=lambda pnr=booking['pnr']: self.show_booking_details_dialog(pnr)
                    )
                    view_button.pack(side="right", padx=(10, 0))
                    
                    # Cancel button (only for upcoming journeys and confirmed status)
                    if booking_type == "upcoming" and booking['status'] == "confirmed":
                        cancel_button = ctk.CTkButton(
                            bottom_frame,
                            text="Cancel",
                            width=100,
                            height=30,
                            fg_color="#e53935",
                            hover_color="#c62828",
                            command=lambda b_id=booking['id']: self.cancel_user_booking(b_id)
                        )
                        cancel_button.pack(side="right")
                
            except Exception as e:
                print(f"Error loading bookings: {e}")
                error_label = ctk.CTkLabel(
                    bookings_scroll, 
                    text=f"Error loading bookings: {str(e)}",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            error_label = ctk.CTkLabel(
                bookings_scroll, 
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            error_label.pack(pady=20)
    
    def show_train_schedule_screen(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # User name and role
        user_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        user_name = ctk.CTkLabel(
            user_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_name.pack(anchor="w")
        
        user_role = ctk.CTkLabel(
            user_frame, 
            text="Passenger", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        user_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_user_dashboard, "assets/dashboard_icon.png"),
            ("Book Tickets", lambda: self.show_user_tab("book"), "assets/ticket_icon.png"),
            ("My Bookings", lambda: self.show_user_tab("bookings"), "assets/booking_icon.png"),
            ("Train Schedule", lambda: self.show_user_tab("schedule"), "assets/schedule_icon.png"),
            ("My Profile", lambda: self.show_user_tab("profile"), "assets/profile_icon.png"),
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Train Schedule" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "Train Schedule" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="Train Schedule", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Current date and time
        current_datetime = datetime.now().strftime("%B %d, %Y %H:%M")
        date_label = ctk.CTkLabel(
            header_frame, 
            text=current_datetime,
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        date_label.pack(side="right", padx=20)
        
        # Schedule content
        schedule_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        schedule_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Search section
        search_frame = ctk.CTkFrame(schedule_frame)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        # Title
        search_title = ctk.CTkLabel(
            search_frame,
            text="Search Train Schedule",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        search_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Form grid
        form_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=15, pady=(0, 15))
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=1)
        
        # Train number
        train_label = ctk.CTkLabel(form_frame, text="Train Number (optional):")
        train_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        train_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter train number", height=35)
        train_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        # Date
        date_label = ctk.CTkLabel(form_frame, text="Date:")
        date_label.grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        date_frame = ctk.CTkFrame(form_frame)
        date_frame.grid(row=1, column=1, sticky="ew")
        
        date_entry = DateEntry(
            date_frame, 
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        date_entry.pack(fill="both", expand=True)
        
        # Source and destination
        source_label = ctk.CTkLabel(form_frame, text="Source Station (optional):")
        source_label.grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        source_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter source station", height=35)
        source_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10))
        
        destination_label = ctk.CTkLabel(form_frame, text="Destination Station (optional):")
        destination_label.grid(row=2, column=1, sticky="w", pady=(10, 5))
        
        destination_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter destination station", height=35)
        destination_entry.grid(row=3, column=1, sticky="ew")
        
        # Search button
        button_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        search_button = ctk.CTkButton(
            button_frame,
            text="Search Schedule",
            command=lambda: self.search_train_schedule(
                train_entry.get(),
                date_entry.get_date(),
                source_entry.get(),
                destination_entry.get(),
                schedule_results_frame
            ),
            height=40
        )
        search_button.pack(pady=10, fill="x")
        
        # Results section
        schedule_results_frame = ctk.CTkFrame(schedule_frame)
        schedule_results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Default instruction text
        instruction_label = ctk.CTkLabel(
            schedule_results_frame,
            text="Enter search criteria and click 'Search Schedule' to view train schedules",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray70")
        )
        instruction_label.pack(pady=40)
    
    def search_train_schedule(self, train_number, date, source, destination, results_frame):
        # Clear previous results
        for widget in results_frame.winfo_children():
            widget.destroy()
        
        # Check if at least one search field is provided
        if not train_number and not source and not destination:
            # Only date is provided, ask for more specific criteria
            warning_label = ctk.CTkLabel(
                results_frame,
                text="Please provide at least one of: Train Number, Source Station, or Destination Station",
                font=ctk.CTkFont(size=14),
                text_color="#e53935"
            )
            warning_label.pack(pady=20)
            return
        
        # Format date for database query
        date_str = date.strftime('%Y-%m-%d')
        
        # Build the query
        base_query = """
            SELECT 
                s.id, t.train_number, t.train_name, s.source, s.destination,
                s.departure_date, s.departure_time, s.arrival_date, s.arrival_time,
                s.status, s.delay_minutes
            FROM 
                schedules s
            JOIN 
                trains t ON s.train_id = t.id
            WHERE 
                s.departure_date = %s
        """
        
        query_params = [date_str]
        
        # Add optional filters
        if train_number:
            base_query += " AND t.train_number LIKE %s"
            query_params.append(f"%{train_number}%")
        
        if source:
            base_query += " AND LOWER(s.source) LIKE %s"
            query_params.append(f"%{source.lower()}%")
        
        if destination:
            base_query += " AND LOWER(s.destination) LIKE %s"
            query_params.append(f"%{destination.lower()}%")
        
        # Add order by
        base_query += " ORDER BY s.departure_time"
        
        # Query database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute(base_query, query_params)
                schedules = cursor.fetchall()
                
                if not schedules:
                    no_results_label = ctk.CTkLabel(
                        results_frame,
                        text="No train schedules found matching your criteria",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_results_label.pack(pady=20)
                    return
                
                # Create scrollable results
                results_scroll = ctk.CTkScrollableFrame(results_frame)
                results_scroll.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Results title with count
                title_label = ctk.CTkLabel(
                    results_scroll,
                    text=f"Found {len(schedules)} train schedules for {date_str}",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                title_label.pack(anchor="w", pady=(0, 15))
                
                # Display schedules
                self.display_train_schedules(results_scroll, schedules)
                
            except Exception as e:
                print(f"Error searching schedules: {e}")
                error_label = ctk.CTkLabel(
                    results_frame,
                    text=f"Error searching schedules: {str(e)}",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            error_label = ctk.CTkLabel(
                results_frame,
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            error_label.pack(pady=20)
    
    def display_train_schedules(self, container, schedules):
        # Display each schedule
        for schedule in schedules:
            schedule_frame = ctk.CTkFrame(container)
            schedule_frame.pack(fill="x", pady=5)
            
            # Train info and status
            header_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(15, 5))
            
            train_info = ctk.CTkLabel(
                header_frame,
                text=f"{schedule['train_number']} - {schedule['train_name']}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            train_info.pack(side="left")
            
            # Status indicator
            status_color = "#43a047"  # Default green for on-time
            status_text = "On Time"
            
            if schedule['status'] == 'delayed':
                status_color = "#ffb300"  # Orange for delayed
                status_text = f"Delayed {schedule['delay_minutes']} min"
            elif schedule['status'] == 'cancelled':
                status_color = "#e53935"  # Red for cancelled
                status_text = "Cancelled"
            
            status_label = ctk.CTkLabel(
                header_frame,
                text=status_text,
                font=ctk.CTkFont(size=14),
                text_color=status_color
            )
            status_label.pack(side="right")
            
            # Route info
            route_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
            route_frame.pack(fill="x", padx=15, pady=(0, 5))
            
            route_info = ctk.CTkLabel(
                route_frame,
                text=f"{schedule['source']} → {schedule['destination']}",
                font=ctk.CTkFont(size=14)
            )
            route_info.pack(anchor="w")
            
            # Time info
            time_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
            time_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            # Create two columns for departure and arrival
            time_frame.columnconfigure(0, weight=1)
            time_frame.columnconfigure(1, weight=1)
            
            # Departure info
            dep_title = ctk.CTkLabel(
                time_frame,
                text="Departure:",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray70")
            )
            dep_title.grid(row=0, column=0, sticky="w")
            
            dep_time = ctk.CTkLabel(
                time_frame,
                text=f"{schedule['departure_date']} {schedule['departure_time']}",
                font=ctk.CTkFont(size=14)
            )
            dep_time.grid(row=1, column=0, sticky="w")
            
            # Arrival info
            arr_title = ctk.CTkLabel(
                time_frame,
                text="Arrival:",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray70")
            )
            arr_title.grid(row=0, column=1, sticky="w")
            
            arr_time = ctk.CTkLabel(
                time_frame,
                text=f"{schedule['arrival_date']} {schedule['arrival_time']}",
                font=ctk.CTkFont(size=14)
            )
            arr_time.grid(row=1, column=1, sticky="w")
            
            # Add a "Book Now" button
            book_button = ctk.CTkButton(
                time_frame,
                text="Book Now",
                width=100,
                height=30,
                command=lambda s=schedule: self.book_from_schedule(s)
            )
            book_button.grid(row=0, column=2, rowspan=2)
    
    def book_from_schedule(self, schedule):
        # Store selection for booking
        source = schedule['source']
        destination = schedule['destination']
        departure_date = schedule['departure_date']
        
        # Navigate to booking screen
        self.show_user_tab("book")
        
        # Wait for booking screen to appear and then fill the form
        def fill_booking_form():
            for widget in self.app.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame):
                            for content in child.winfo_children():
                                if isinstance(content, ctk.CTkTabview):
                                    # Found the tabview in the booking screen
                                    search_tab = content.tab("Search Trains")
                                    
                                    # Find the source and destination entries
                                    for form in search_tab.winfo_children():
                                        if isinstance(form, ctk.CTkFrame):
                                            for form_content in form.winfo_children():
                                                if isinstance(form_content, ctk.CTkFrame) and form_content.winfo_toplevel() == self.app:
                                                    for entry in form_content.winfo_children():
                                                        if isinstance(entry, ctk.CTkEntry):
                                                            # Try to identify entries by placeholder text
                                                            if hasattr(entry, '_placeholder_text'):
                                                                if "source" in str(entry._placeholder_text).lower():
                                                                    entry.delete(0, 'end')
                                                                    entry.insert(0, source)
                                                                elif "destination" in str(entry._placeholder_text).lower():
                                                                    entry.delete(0, 'end')
                                                                    entry.insert(0, destination)
                                    
                                    # Show a message that form has been prefilled
                                    CTkMessagebox(
                                        title="Booking Form Prefilled",
                                        message=f"The booking form has been prefilled with your selected journey details.\n\nPlease click 'Search Trains' to continue.",
                                        icon="info"
                                    )
                                    return
            
            # If we couldn't find the form elements, show a message
            CTkMessagebox(
                title="Automatic Fill Failed",
                message="Could not automatically fill the booking form. Please enter your journey details manually.",
                icon="warning"
            )
        
        # Schedule the form filling after a short delay
        self.app.after(500, fill_booking_form)
    
    def show_user_profile_screen(self):
        # Clear the window
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.app, corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Sidebar frame
        sidebar_frame = ctk.CTkFrame(main_frame, width=200, corner_radius=0)
        sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Add logo to sidebar
        try:
            logo_img = Image.open("assets/train_logo.png")
            logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="  Railways", compound="left",
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.image = logo_photo
            logo_label.pack(pady=(20, 20), padx=20)
        except:
            logo_label = ctk.CTkLabel(sidebar_frame, text="🚄 Railways", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
            logo_label.pack(pady=(20, 20), padx=20)
        
        # Sidebar separator
        separator = ctk.CTkFrame(sidebar_frame, height=1, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=15, pady=(0, 10))
        
        # User name and role
        user_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=15, pady=(10, 20))
        
        user_name = ctk.CTkLabel(
            user_frame, 
            text=self.current_user['name'], 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_name.pack(anchor="w")
        
        user_role = ctk.CTkLabel(
            user_frame, 
            text="Passenger", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray80")
        )
        user_role.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_user_dashboard, "assets/dashboard_icon.png"),
            ("Book Tickets", lambda: self.show_user_tab("book"), "assets/ticket_icon.png"),
            ("My Bookings", lambda: self.show_user_tab("bookings"), "assets/booking_icon.png"),
            ("Train Schedule", lambda: self.show_user_tab("schedule"), "assets/schedule_icon.png"),
            ("My Profile", lambda: self.show_user_tab("profile"), "assets/profile_icon.png"),
        ]
        
        for text, command, icon_path in nav_buttons:
            try:
                icon_img = load_image(icon_path, (20, 20))
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    image=icon_img,
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "My Profile" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
                button.image = icon_img
            except:
                button = ctk.CTkButton(
                    sidebar_frame, 
                    text=text, 
                    anchor="w",
                    height=40,
                    fg_color="transparent" if text != "My Profile" else None,
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    corner_radius=5,
                    command=command
                )
            button.pack(fill="x", padx=10, pady=5)
        
        # Logout button at bottom of sidebar
        sidebar_frame.pack_propagate(False)  # Prevent sidebar from resizing
        
        sidebar_bottom = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=10, pady=20)
        
        # Theme toggle
        appearance_label = ctk.CTkLabel(sidebar_bottom, text="Appearance Mode:")
        appearance_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        appearance_options = ["Light", "Dark"]
        appearance_var = StringVar(value="Light" if self.current_theme == "light" else "Dark")
        
        appearance_menu = ctk.CTkOptionMenu(
            sidebar_bottom, 
            values=appearance_options,
            command=self.change_appearance_mode,
            variable=appearance_var,
            width=120
        )
        appearance_menu.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Logout button
        logout_button = ctk.CTkButton(
            sidebar_bottom, 
            text="Logout", 
            command=self.logout,
            fg_color="#e53935",
            hover_color="#c62828",
            height=40
        )
        logout_button.pack(fill="x", pady=10)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color=("gray95", "gray15"))
        content_frame.pack(side="right", fill="both", expand=True)
        
        # Header frame
        header_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color=("white", "gray20"), height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Header title
        header_title = ctk.CTkLabel(
            header_frame, 
            text="My Profile", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_title.pack(side="left", padx=20)
        
        # Profile content
        profile_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        profile_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs for different profile sections
        tabview = ctk.CTkTabview(profile_frame)
        tabview.pack(fill="both", expand=True)
        
        # Add tabs
        profile_tab = tabview.add("Profile Information")
        security_tab = tabview.add("Security Settings")
        booking_history_tab = tabview.add("Booking History")
        
        # Setup each tab
        self.setup_profile_info_tab(profile_tab)
        self.setup_security_settings_tab(security_tab)
        self.setup_booking_history_tab(booking_history_tab)
    
    def setup_profile_info_tab(self, parent):
        # Load user data
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                cursor.execute("SELECT * FROM users WHERE id = %s", (self.current_user['id'],))
                user_data = cursor.fetchone()
                
                if not user_data:
                    error_label = ctk.CTkLabel(
                        parent,
                        text="Could not load user data",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    error_label.pack(pady=20)
                    return
                
                # Profile sections frame
                profile_content = ctk.CTkFrame(parent, fg_color="transparent")
                profile_content.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Profile card at the top
                profile_card = ctk.CTkFrame(profile_content)
                profile_card.pack(fill="x", pady=10)
                
                # Profile header
                profile_header = ctk.CTkFrame(profile_card, fg_color="transparent")
                profile_header.pack(fill="x", padx=20, pady=(20, 5))
                
                # Profile avatar
                try:
                    if user_data.get('profile_pic'):
                        # If user has a profile pic, load it
                        avatar_img = Image.open(user_data['profile_pic'])
                    else:
                        # Use default avatar
                        avatar_img = Image.open("assets/avatar.png")
                    
                    avatar_img = avatar_img.resize((80, 80), Image.Resampling.LANCZOS)
                    avatar_photo = ImageTk.PhotoImage(avatar_img)
                    
                    avatar_label = ctk.CTkLabel(profile_header, image=avatar_photo, text="")
                    avatar_label.image = avatar_photo
                    avatar_label.pack(side="left", padx=(0, 20))
                except:
                    # If image loading fails, use a text placeholder
                    avatar_frame = ctk.CTkFrame(profile_header, width=80, height=80)
                    avatar_frame.pack(side="left", padx=(0, 20))
                    avatar_frame.pack_propagate(False)
                    
                    initials = "".join([name[0].upper() for name in user_data['name'].split() if name])
                    if not initials:
                        initials = "U"
                    
                    initials_label = ctk.CTkLabel(
                        avatar_frame,
                        text=initials,
                        font=ctk.CTkFont(size=30, weight="bold")
                    )
                    initials_label.place(relx=0.5, rely=0.5, anchor="center")
                
                # User basic info
                user_info = ctk.CTkFrame(profile_header, fg_color="transparent")
                user_info.pack(side="left", fill="both", expand=True)
                
                user_name = ctk.CTkLabel(
                    user_info,
                    text=user_data['name'],
                    font=ctk.CTkFont(size=20, weight="bold")
                )
                user_name.pack(anchor="w")
                
                user_email = ctk.CTkLabel(
                    user_info,
                    text=user_data['email'],
                    font=ctk.CTkFont(size=14)
                )
                user_email.pack(anchor="w", pady=(5, 0))
                
                joined_date = ctk.CTkLabel(
                    user_info,
                    text=f"Member since {user_data['created_at'].strftime('%B %d, %Y') if isinstance(user_data['created_at'], datetime) else user_data['created_at']}",
                    font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray70")
                )
                joined_date.pack(anchor="w", pady=(5, 0))
                
                # Edit profile button
                edit_button = ctk.CTkButton(
                    profile_header,
                    text="Edit Profile",
                    width=120,
                    height=35,
                    command=lambda: self.show_edit_profile_dialog(user_data)
                )
                edit_button.pack(side="right")
                
                # Profile details section
                details_section = ctk.CTkFrame(profile_content)
                details_section.pack(fill="x", pady=10)
                
                details_title = ctk.CTkLabel(
                    details_section,
                    text="Personal Details",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                details_title.pack(anchor="w", padx=20, pady=15)
                
                # Details grid
                details_grid = ctk.CTkFrame(details_section, fg_color="transparent")
                details_grid.pack(fill="x", padx=20, pady=(0, 15))
                
                # Two columns layout
                details_grid.columnconfigure(0, weight=1)
                details_grid.columnconfigure(1, weight=1)
                
                # Row 1: Name
                name_label = ctk.CTkLabel(
                    details_grid,
                    text="Full Name:",
                    font=ctk.CTkFont(weight="bold")
                )
                name_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
                
                name_value = ctk.CTkLabel(
                    details_grid,
                    text=user_data['name']
                )
                name_value.grid(row=0, column=1, sticky="w", padx=5, pady=5)
                
                # Row 2: Email
                email_label = ctk.CTkLabel(
                    details_grid,
                    text="Email:",
                    font=ctk.CTkFont(weight="bold")
                )
                email_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
                
                email_value = ctk.CTkLabel(
                    details_grid,
                    text=user_data['email']
                )
                email_value.grid(row=1, column=1, sticky="w", padx=5, pady=5)
                
                # Row 3: Phone
                phone_label = ctk.CTkLabel(
                    details_grid,
                    text="Phone:",
                    font=ctk.CTkFont(weight="bold")
                )
                phone_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
                
                phone_value = ctk.CTkLabel(
                    details_grid,
                    text=user_data.get('phone') or "Not provided"
                )
                phone_value.grid(row=2, column=1, sticky="w", padx=5, pady=5)
                
                # Row 4: Theme
                theme_label = ctk.CTkLabel(
                    details_grid,
                    text="Preferred Theme:",
                    font=ctk.CTkFont(weight="bold")
                )
                theme_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
                
                theme_value = ctk.CTkLabel(
                    details_grid,
                    text=user_data.get('theme', 'Light').capitalize()
                )
                theme_value.grid(row=3, column=1, sticky="w", padx=5, pady=5)
                
                # Activity summary section
                activity_section = ctk.CTkFrame(profile_content)
                activity_section.pack(fill="x", pady=10)
                
                activity_title = ctk.CTkLabel(
                    activity_section,
                    text="Account Summary",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                activity_title.pack(anchor="w", padx=20, pady=15)
                
                # Get booking stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_bookings,
                        COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_bookings,
                        COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_bookings,
                        SUM(CASE WHEN status = 'confirmed' THEN total_fare ELSE 0 END) as total_spent
                    FROM 
                        bookings
                    WHERE 
                        user_id = %s
                """, (self.current_user['id'],))
                
                stats = cursor.fetchone()
                
                # Stats grid
                stats_grid = ctk.CTkFrame(activity_section, fg_color="transparent")
                stats_grid.pack(fill="x", padx=20, pady=(0, 15))
                stats_grid.columnconfigure(0, weight=1)
                stats_grid.columnconfigure(1, weight=1)
                stats_grid.columnconfigure(2, weight=1)
                stats_grid.columnconfigure(3, weight=1)
                
                # Total bookings
                total_frame = ctk.CTkFrame(stats_grid)
                total_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
                
                total_label = ctk.CTkLabel(
                    total_frame,
                    text="Total Bookings",
                    font=ctk.CTkFont(size=12)
                )
                total_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                total_value = ctk.CTkLabel(
                    total_frame,
                    text=str(stats['total_bookings'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                total_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Confirmed bookings
                confirmed_frame = ctk.CTkFrame(stats_grid)
                confirmed_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
                
                confirmed_label = ctk.CTkLabel(
                    confirmed_frame,
                    text="Confirmed",
                    font=ctk.CTkFont(size=12)
                )
                confirmed_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                confirmed_value = ctk.CTkLabel(
                    confirmed_frame,
                    text=str(stats['confirmed_bookings'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                confirmed_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Cancelled bookings
                cancelled_frame = ctk.CTkFrame(stats_grid)
                cancelled_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
                
                cancelled_label = ctk.CTkLabel(
                    cancelled_frame,
                    text="Cancelled",
                    font=ctk.CTkFont(size=12)
                )
                cancelled_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                cancelled_value = ctk.CTkLabel(
                    cancelled_frame,
                    text=str(stats['cancelled_bookings'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                cancelled_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Total spent
                spent_frame = ctk.CTkFrame(stats_grid)
                spent_frame.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
                
                spent_label = ctk.CTkLabel(
                    spent_frame,
                    text="Total Spent",
                    font=ctk.CTkFont(size=12)
                )
                spent_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                spent_value = ctk.CTkLabel(
                    spent_frame,
                    text=format_currency(stats['total_spent'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                spent_value.pack(anchor="w", padx=10, pady=(0, 10))
                
            except Exception as e:
                print(f"Error loading profile data: {e}")
                error_label = ctk.CTkLabel(
                    parent,
                    text=f"Error loading profile data: {str(e)}",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            error_label = ctk.CTkLabel(
                parent,
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            error_label.pack(pady=20)
    
    def show_edit_profile_dialog(self, user_data):
        # Create a dialog window
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Edit Profile")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        dialog.grab_set()  # Make the dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Title
        title_label = ctk.CTkLabel(
            dialog, 
            text="Edit Profile Information", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # Form
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Name
        name_label = ctk.CTkLabel(form_frame, text="Full Name:")
        name_label.pack(anchor="w", pady=(10, 5))
        
        name_entry = ctk.CTkEntry(form_frame, height=35)
        name_entry.insert(0, user_data['name'])
        name_entry.pack(fill="x", pady=(0, 10))
        
        # Email (readonly)
        email_label = ctk.CTkLabel(form_frame, text="Email (cannot be changed):")
        email_label.pack(anchor="w", pady=(10, 5))
        
        email_entry = ctk.CTkEntry(form_frame, height=35, state="disabled")
        email_entry.insert(0, user_data['email'])
        email_entry.pack(fill="x", pady=(0, 10))
        
        # Phone
        phone_label = ctk.CTkLabel(form_frame, text="Phone Number:")
        phone_label.pack(anchor="w", pady=(10, 5))
        
        phone_entry = ctk.CTkEntry(form_frame, height=35)
        if user_data.get('phone'):
            phone_entry.insert(0, user_data['phone'])
        phone_entry.pack(fill="x", pady=(0, 10))
        
        # Theme
        theme_label = ctk.CTkLabel(form_frame, text="Preferred Theme:")
        theme_label.pack(anchor="w", pady=(10, 5))
        
        theme_var = StringVar(value=user_data.get('theme', 'light').capitalize())
        
        theme_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 10))
        
        light_radio = ctk.CTkRadioButton(
            theme_frame, 
            text="Light",
            variable=theme_var,
            value="Light"
        )
        light_radio.pack(side="left", padx=(0, 20))
        
        dark_radio = ctk.CTkRadioButton(
            theme_frame, 
            text="Dark",
            variable=theme_var,
            value="Dark"
        )
        dark_radio.pack(side="left")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Save Button
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save Changes",
            command=lambda: self.update_profile(
                user_data['id'],
                name_entry.get(),
                phone_entry.get(),
                theme_var.get().lower(),
                dialog
            ),
            height=40
        )
        save_button.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        # Cancel Button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy,
            height=40,
            fg_color="gray",
            hover_color="gray30"
        )
        cancel_button.pack(side="right", padx=(5, 0), fill="x", expand=True)
    
    def update_profile(self, user_id, name, phone, theme, dialog):
        # Validate inputs
        if not name:
            CTkMessagebox(
                title="Error",
                message="Name is required",
                icon="cancel"
            )
            return
        
        if phone and not validate_phone(phone):
            CTkMessagebox(
                title="Error",
                message="Please enter a valid phone number",
                icon="cancel"
            )
            return
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            try:
                # Update user profile
                if phone:
                    cursor.execute(
                        "UPDATE users SET name = %s, phone = %s, theme = %s WHERE id = %s",
                        (name, phone, theme, user_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET name = %s, theme = %s WHERE id = %s",
                        (name, theme, user_id)
                    )
                
                connection.commit()
                
                # Update current user info
                self.current_user['name'] = name
                self.current_theme = theme
                
                # Apply theme change
                ctk.set_appearance_mode(theme)
                
                dialog.destroy()
                
                CTkMessagebox(
                    title="Success",
                    message="Profile updated successfully",
                    icon="check"
                )
                
                # Refresh the profile page
                self.show_user_tab("profile")
                
            except Exception as e:
                connection.rollback()
                CTkMessagebox(
                    title="Error",
                    message=f"Failed to update profile: {str(e)}",
                    icon="cancel"
                )
            finally:
                cursor.close()
                connection.close()
    
    def setup_security_settings_tab(self, parent):
        # Create frame for password change
        password_frame = ctk.CTkFrame(parent)
        password_frame.pack(fill="x", padx=10, pady=10)
        
        # Title
        password_title = ctk.CTkLabel(
            password_frame,
            text="Change Password",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        password_title.pack(anchor="w", padx=15, pady=15)
        
        # Form
        form_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Current password
        current_password_label = ctk.CTkLabel(form_frame, text="Current Password:")
        current_password_label.pack(anchor="w", pady=(0, 5))
        
        current_password_entry = ctk.CTkEntry(form_frame, show="•", height=35)
        current_password_entry.pack(fill="x", pady=(0, 10))
        
        # New password
        new_password_label = ctk.CTkLabel(form_frame, text="New Password:")
        new_password_label.pack(anchor="w", pady=(0, 5))
        
        new_password_entry = ctk.CTkEntry(form_frame, show="•", height=35)
        new_password_entry.pack(fill="x", pady=(0, 10))
        
        # Confirm new password
        confirm_password_label = ctk.CTkLabel(form_frame, text="Confirm New Password:")
        confirm_password_label.pack(anchor="w", pady=(0, 5))
        
        confirm_password_entry = ctk.CTkEntry(form_frame, show="•", height=35)
        confirm_password_entry.pack(fill="x", pady=(0, 10))
        
        # Change password button
        change_password_button = ctk.CTkButton(
            form_frame,
            text="Change Password",
            command=lambda: self.change_password(
                current_password_entry.get(),
                new_password_entry.get(),
                confirm_password_entry.get(),
                [current_password_entry, new_password_entry, confirm_password_entry]
            ),
            height=40
        )
        change_password_button.pack(pady=10, fill="x")
        
        # Password requirements note
        requirements_label = ctk.CTkLabel(
            form_frame,
            text="Password must be at least 6 characters long",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        requirements_label.pack(anchor="w", pady=(0, 10))
    
    def setup_booking_history_tab(self, parent):
        # Create header frame with statistics
        stats_frame = ctk.CTkFrame(parent)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        # Title
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="Booking Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_title.pack(anchor="w", padx=15, pady=15)
        
        # Get booking stats
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            try:
                # Get overall statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_bookings,
                        COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_bookings,
                        COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_bookings,
                        SUM(CASE WHEN status = 'confirmed' THEN total_fare ELSE 0 END) as total_spent
                    FROM 
                        bookings
                    WHERE 
                        user_id = %s
                """, (self.current_user['id'],))
                
                stats = cursor.fetchone()
                
                # Create statistics grid
                stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
                stats_grid.pack(fill="x", padx=15, pady=(0, 15))
                stats_grid.columnconfigure(0, weight=1)
                stats_grid.columnconfigure(1, weight=1)
                stats_grid.columnconfigure(2, weight=1)
                stats_grid.columnconfigure(3, weight=1)
                
                # Total bookings
                total_frame = ctk.CTkFrame(stats_grid)
                total_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
                
                total_label = ctk.CTkLabel(
                    total_frame,
                    text="Total Bookings",
                    font=ctk.CTkFont(size=12)
                )
                total_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                total_value = ctk.CTkLabel(
                    total_frame,
                    text=str(stats['total_bookings'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                total_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Confirmed bookings
                confirmed_frame = ctk.CTkFrame(stats_grid)
                confirmed_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
                
                confirmed_label = ctk.CTkLabel(
                    confirmed_frame,
                    text="Confirmed",
                    font=ctk.CTkFont(size=12)
                )
                confirmed_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                confirmed_value = ctk.CTkLabel(
                    confirmed_frame,
                    text=str(stats['confirmed_bookings'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                confirmed_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Cancelled bookings
                cancelled_frame = ctk.CTkFrame(stats_grid)
                cancelled_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
                
                cancelled_label = ctk.CTkLabel(
                    cancelled_frame,
                    text="Cancelled",
                    font=ctk.CTkFont(size=12)
                )
                cancelled_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                cancelled_value = ctk.CTkLabel(
                    cancelled_frame,
                    text=str(stats['cancelled_bookings'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                cancelled_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Total spent
                spent_frame = ctk.CTkFrame(stats_grid)
                spent_frame.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
                
                spent_label = ctk.CTkLabel(
                    spent_frame,
                    text="Total Spent",
                    font=ctk.CTkFont(size=12)
                )
                spent_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                spent_value = ctk.CTkLabel(
                    spent_frame,
                    text=format_currency(stats['total_spent'] or 0),
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                spent_value.pack(anchor="w", padx=10, pady=(0, 10))
                
                # Recent bookings section
                recent_frame = ctk.CTkFrame(parent)
                recent_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                recent_title = ctk.CTkLabel(
                    recent_frame,
                    text="Recent Booking History",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                recent_title.pack(anchor="w", padx=15, pady=15)
                
                # Create scrollable frame for recent bookings
                recent_scroll = ctk.CTkScrollableFrame(recent_frame)
                recent_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
                
                # Get recent bookings
                cursor.execute("""
                    SELECT 
                        b.id, b.pnr, b.booking_date, b.total_fare, b.status,
                        t.train_name, s.source, s.destination, s.departure_date
                    FROM 
                        bookings b
                    JOIN 
                        schedules s ON b.schedule_id = s.id
                    JOIN 
                        trains t ON s.train_id = t.id
                    WHERE 
                        b.user_id = %s
                    ORDER BY 
                        b.booking_date DESC
                    LIMIT 10
                """, (self.current_user['id'],))
                
                bookings = cursor.fetchall()
                
                if not bookings:
                    no_bookings_label = ctk.CTkLabel(
                        recent_scroll,
                        text="No booking history found",
                        font=ctk.CTkFont(size=14),
                        text_color=("gray50", "gray70")
                    )
                    no_bookings_label.pack(pady=20)
                else:
                    # Create table header
                    header_frame = ctk.CTkFrame(recent_scroll, fg_color=("gray80", "gray25"))
                    header_frame.pack(fill="x", pady=(0, 5))
                    
                    header_columns = [
                        ("PNR", 100),
                        ("Date", 100),
                        ("Train", 150),
                        ("Route", 180),
                        ("Status", 80),
                        ("Fare", 100)
                    ]
                    
                    for i, (text, width) in enumerate(header_columns):
                        ctk.CTkLabel(
                            header_frame, 
                            text=text, 
                            font=ctk.CTkFont(weight="bold"),
                            width=width
                        ).grid(row=0, column=i, padx=5, pady=5)
                    
                    # Add booking rows
                    for booking in bookings:
                        row_frame = ctk.CTkFrame(recent_scroll)
                        row_frame.pack(fill="x", pady=2)
                        
                        # Format status for display
                        status_text = "Confirmed" if booking['status'] == "confirmed" else "Cancelled"
                        status_color = "#43a047" if booking['status'] == "confirmed" else "#e53935"
                        
                        # Route format
                        route_text = f"{booking['source']} → {booking['destination']}"
                        
                        # Add data to row
                        ctk.CTkLabel(row_frame, text=booking['pnr'], width=header_columns[0][1]).grid(row=0, column=0, padx=5, pady=8)
                        ctk.CTkLabel(row_frame, text=booking['booking_date'].strftime('%Y-%m-%d') if isinstance(booking['booking_date'], datetime) else booking['booking_date'], width=header_columns[1][1]).grid(row=0, column=1, padx=5, pady=8)
                        ctk.CTkLabel(row_frame, text=booking['train_name'], width=header_columns[2][1]).grid(row=0, column=2, padx=5, pady=8)
                        ctk.CTkLabel(row_frame, text=route_text, width=header_columns[3][1]).grid(row=0, column=3, padx=5, pady=8)
                        ctk.CTkLabel(row_frame, text=status_text, text_color=status_color, width=header_columns[4][1]).grid(row=0, column=4, padx=5, pady=8)
                        ctk.CTkLabel(row_frame, text=format_currency(booking['total_fare']), width=header_columns[5][1]).grid(row=0, column=5, padx=5, pady=8)
            except Exception as e:
                print(f"Error loading booking history: {e}")
                error_label = ctk.CTkLabel(
                    parent,
                    text=f"Error loading booking history: {str(e)}",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")
                )
                error_label.pack(pady=20)
            finally:
                cursor.close()
                connection.close()
        else:
            error_label = ctk.CTkLabel(
                parent,
                text="Could not connect to database",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            error_label.pack(pady=20)

# Main entry point
if __name__ == "__main__":
    app = RailwayReservationSystem()
    app.app.mainloop()