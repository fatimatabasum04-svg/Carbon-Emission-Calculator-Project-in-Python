# test_connection.py - Fixed version

import psycopg2

# UPDATE THESE THREE LINES WITH YOUR CORRECT INFORMATION
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'carbom_emission',    # ← Changed from carbon_tracker to carbom_emission
    'user': 'postgres',
    'password': 'fatima123'             # ← CHANGE THIS to your actual PostgreSQL password
}

try:
    # Try to connect
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ SUCCESS! Connected to PostgreSQL database.")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM \"User\"")
    count = cursor.fetchone()[0]
    print(f"📊 Number of users in database: {count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check your password in DB_CONFIG")
    print("3. Make sure database 'carbom_emission' exists")
    print("4. Try password: postgres, admin, root, or the one you set")