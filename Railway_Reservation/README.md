# Railway Reservation System

This project is a Railway Reservation System built using Python. It provides an enhanced UI/UX for booking train tickets, managing schedules, viewing bookings, and much more. The system supports both user and admin functionalities.

---

## Features

### User Features
- **Dashboard**: View upcoming journeys, recent bookings, and notifications.
- **Book Tickets**: Search for trains, view schedules, and book tickets.
- **Payment Options**: Choose from Credit Card, Debit Card, Net Banking, or UPI.
- **Profile Management**: Update personal information and view booking history.
- **Notifications**: Receive alerts about booking status and train delays.

### Admin Features
- **Admin Dashboard**: View statistics, upcoming departures, and revenue reports.
- **Manage Trains and Schedules**: Add, update, and delete train schedules.
- **Bookings Management**: View and manage all bookings and passenger details.
- **Generate Reports**: Analyze revenue and booking trends.

---

## Tech Stack
- **Frontend**: CustomTkinter for a modern desktop GUI.
- **Backend**: MySQL for database management.
- **Libraries**:
  - `bcrypt` for secure password hashing.
  - `customtkinter` for advanced GUI elements.
  - `mysql-connector-python` for interacting with the MySQL database.
  - `python-dotenv` for environment variable management.
  - `tkcalendar` for date selection.
  - `matplotlib` for generating charts and reports.

---

## Installation

### Prerequisites
- Python 3.8 or later.(it does not work on python 3.13 which is latest one, try 3.11 or lower versions )
- MySQL server installed on your machine.
- A code editor or IDE (e.g., Visual Studio Code, PyCharm).

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<username>/railway-reservation-system.git
   cd railway-reservation-system
   ```

2. **Set Up the Environment**:
   - Install Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Create a `.env` file in the root directory with the following content:
     ```
     MYSQL_HOST=localhost
     MYSQL_USER=root
     MYSQL_PASSWORD=your_password
     MYSQL_DATABASE=railway_system
     MYSQL_PORT=3306
     ```

3. **Set Up the Database**:
   - Launch your MySQL server.
   - Run the SQL script to set up the database:
     ```bash
     mysql -u root -p < database.sql
     ```

4. **Run the Application**:
   ```bash
   python main.py
   ```

---

## Usage

### User Login
- Launch the application and log in as a user using the following credentials:
  - Email: `john@example.com`
  - Password: `password123`

### Admin Login
- Admins can log in using the following credentials:
  - Email: `admin@railways.com`
  - Password: `admin123`

### Application Sections
1. **Dashboard**:
   - Users: View upcoming train journeys and notifications.
   - Admins: View statistics, revenue reports, and upcoming departures.

2. **Book Tickets**:
   - Search for trains by source, destination, and date.
   - Choose travel class (Sleeper, AC, or General).
   - Enter passenger details and make payment.

3. **Manage Trains (Admin)**:
   - Add new trains.
   - Update or delete existing train schedules.

4. **View Bookings**:
   - Users: View and cancel their bookings.
   - Admins: View all bookings and passenger details.

---

## Folder Structure
```
railway-reservation-system/
├── assets/                  # Images and icons for the application
├── main.py                  # Entry point of the application
├── database.sql             # SQL file to set up the database
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not included in repo)
└── README.md                # Documentation
```

---

## Entities and Relationships

### Key Entities
- **Users**: Stores user information and roles (admin/user).
- **Trains**: Stores information about trains and their capacities.
- **Schedules**: Stores train schedules, including source, destination, and fares.
- **Bookings**: Stores user bookings and payment information.
- **Passengers**: Stores details of passengers in each booking.
- **Notifications**: Stores alerts and notifications sent to users.

### Relationships
- Users `Makes` Bookings.
- Bookings `Contains` Passengers.
- Trains `Operates` Schedules.
- Users `Receives` Notifications.

---

## FAQ

**1. How do I reset my admin password?**
   - Update the `password` field in the `users` table for the admin user using a hashed value of the new password.

**2. I can't connect to the database.**
   - Ensure your MySQL server is running and the credentials in the `.env` file are correct.

**3. How do I add new trains?**
   - Log in as an admin and navigate to the "Manage Trains" section.

---

## Contribution
1. Fork the repository.
2. Create a branch for your feature or bug fix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes and push to your forked repository:
   ```bash
   git commit -m "Add feature"
   git push origin feature-name
   ```
4. Open a pull request to merge your changes.

---

## License
This project is licensed under the MIT License.
