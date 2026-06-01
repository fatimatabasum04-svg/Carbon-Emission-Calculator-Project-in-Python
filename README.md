# Carbon-Emission-Calculator-Project-in-Python
A web-based carbon footprint tracker built with **Python (Flask)** and **PostgreSQL**. Users can log daily activities, monitor their greenhouse gas emissions, set weekly reduction goals, and compete with friends through group leaderboards.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Database Configuration](#database-configuration)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [How Emissions Are Calculated](#how-emissions-are-calculated)
- [Running Tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Carbon Emission Calculator estimates and tracks greenhouse gas emissions by processing activity data — such as daily travel distance and monthly electricity usage — and applying standard emission factors to compute an aggregate carbon footprint in **kilograms of CO₂ equivalent (kg CO₂e)**.

Users register an account, log their activities, set a personal weekly emissions goal, and optionally join a group to compete on a shared leaderboard. The dashboard provides a real-time snapshot of weekly and monthly totals, goal progress, and historical trends.

## Features

| # | Feature | Description |
|---|---------|-------------|
| F1 | **User Authentication** | Register and log in with hashed passwords |
| F2 | **Group Management** | Create or join groups using a unique group code |
| F3 | **Weekly Goal Setting** | Set a personal weekly CO₂ target (kg) |
| F4 | **Activity Logging** | Add, view, and delete emission-producing activities |
| F5 | **Weekly Emission Summary** | Auto-calculated total for the current week |
| F6 | **Monthly Emission Summary** | Auto-calculated total for the current month |
| F7 | **Goal Status Indicator** | Visual feedback based on goal vs. actual |
| F8 | **Group Leaderboard** | Ranks groups by percentage of members who met their goal |
| F9 | **Activity Comparison Tool** | Compare two activity types side-by-side to show CO₂ savings |
| F10 | **Historical Trends** | Week-by-week emission history for the past N weeks |

## Tech Stack

- **Backend:** Python 3, Flask
- **Database:** PostgreSQL (via `psycopg2` with connection pooling)
- **Frontend:** HTML/Jinja2 templates
- **Security:** SHA-256 password hashing

## Project Structure

Carbon-Emission-Calculator-Project-in-Python/
├── app.py               # Flask application — routes and session management
├── database.py          # All PostgreSQL operations and business logic
├── test_connection.py   # Database connectivity test
├── test_functions.py    # Unit tests for core database functions
└── templates/           # HTML templates (Jinja2)
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── add_activity.html
    ├── create_group.html
    ├── leaderboard.html
    └── compare.html

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- `pip` (Python package manager)

## Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/fatimatabasum04-svg/Carbon-Emission-Calculator-Project-in-Python.git
cd Carbon-Emission-Calculator-Project-in-Python
```

**2. Install Python dependencies**

```bash
pip install flask psycopg2-binary
```

## Database Configuration

**1. Create the PostgreSQL database**

```sql
CREATE DATABASE carbom_emission;
```

**2. Update credentials in 'database.py'**

Open `database.py` and edit the `DB_CONFIG` block near the top:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'carbom_emission',
    'user': 'postgres',
    'password': 'YOUR_PASSWORD_HERE'   # ← change this
}
```

**3. Create the required tables**

Run the following SQL against your database to create the schema:

```sql
CREATE TABLE "User" (
    user_id     SERIAL PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    weekly_goal_kg NUMERIC(10,2),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE "Group" (
    group_id    SERIAL PRIMARY KEY,
    group_name  VARCHAR(100) UNIQUE NOT NULL,
    group_code  VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE User_Group (
    user_id     INT REFERENCES "User"(user_id),
    group_id    INT REFERENCES "Group"(group_id),
    PRIMARY KEY (user_id, group_id)
);

CREATE TABLE Activity_Type (
    type_id     SERIAL PRIMARY KEY,
    type_name   VARCHAR(100) NOT NULL,
    default_unit VARCHAR(20)
);

CREATE TABLE Emission_Factor (
    factor_id       SERIAL PRIMARY KEY,
    type_id         INT REFERENCES Activity_Type(type_id),
    factor_value    NUMERIC(10,6) NOT NULL,
    effective_date  DATE DEFAULT CURRENT_DATE
);

CREATE TABLE Activity (
    activity_id   SERIAL PRIMARY KEY,
    user_id       INT REFERENCES "User"(user_id),
    type_id       INT REFERENCES Activity_Type(type_id),
    quantity      NUMERIC(10,2) NOT NULL,
    unit          VARCHAR(20),
    activity_date DATE NOT NULL
);

CREATE TABLE Weekly_Goal_Status (
    user_id           INT REFERENCES "User"(user_id),
    week_start_date   DATE,
    total_emissions_kg NUMERIC(10,2),
    goal_met          BOOLEAN,
    PRIMARY KEY (user_id, week_start_date)
);
```

**4. Seed activity types and emission factors (example)**

```sql
INSERT INTO Activity_Type (type_name, default_unit) VALUES
    ('Car Travel', 'km'),
    ('Electricity Usage', 'kWh'),
    ('Flight', 'km'),
    ('Natural Gas', 'm3');

INSERT INTO Emission_Factor (type_id, factor_value) VALUES
    (1, 0.21),    -- 0.21 kg CO2 per km driven
    (2, 0.233),   -- 0.233 kg CO2 per kWh
    (3, 0.255),   -- 0.255 kg CO2 per km flown
    (4, 2.04);    -- 2.04 kg CO2 per m3 of natural gas
```

## Running the Application

```bash
python app.py
```

The app starts on `http://127.0.0.1:5000` by default. Open that URL in your browser to access the login page.

> **Security note:** Before deploying to production, replace the placeholder `secret_key` in `app.py` with a strong random value and store it as an environment variable.

## Usage Guide

1. **Register** a new account and set your weekly CO₂ goal (in kg).
2. **Log in** to access your personal dashboard.
3. **Add activities** (e.g., "drove 40 km by car today") from the *Add Activity* page.
4. Your **dashboard** automatically shows:
   - Weekly and monthly emission totals
   - Goal status (✅ met / ❌ exceeded)
   - Your 5 most recent activities
   - A 4-week historical trend
5. **Create or join a group** using a shared group code to appear on the leaderboard.
6. Use the **Compare** tool to see how much CO₂ you could save by switching between two activity types.

## How Emissions Are Calculated

Each activity's CO₂ contribution is:

```
emission_kg = quantity × emission_factor
```

Where `emission_factor` is sourced from the `Emission_Factor` table for the given activity type. Weekly and monthly totals are the sum of all logged activities within the respective date range.

## Running Tests

```bash
# Test database connectivity
python test_connection.py

# Test core database functions
python test_functions.py
```

## Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please make sure to run the existing tests before submitting.

## License

This project is open source. Feel free to use and adapt it for educational purposes.
