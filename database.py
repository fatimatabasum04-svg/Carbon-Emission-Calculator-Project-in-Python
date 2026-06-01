# ============================================================
# FILE: database.py
# Description: PostgreSQL connection and database operations
# for Group Carbon Challenge Tracker
# ============================================================

import psycopg2
from psycopg2 import sql, extras
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from datetime import datetime, date, timedelta
import hashlib
import os

# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'carbom_emission',
    'user': 'postgres',
    'password': 'fatima123'  # Change this to your actual password
}

# Create connection pool for better performance
connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_CONFIG
)

# ============================================================
# 2. CONNECTION MANAGER (Use this for all database operations)
# ============================================================

@contextmanager
def get_db_connection():
    """Get a database connection from the pool"""
    conn = connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        connection_pool.putconn(conn)

@contextmanager
def get_db_cursor():
    """Get a database cursor for executing queries"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            yield cursor
        finally:
            cursor.close()

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def hash_password(password):
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    """Verify a plain password against its hash"""
    return hash_password(plain_password) == hashed_password

# ============================================================
# 4. USER MANAGEMENT (F1: Registration and Login)
# ============================================================

def register_user(full_name, email, password, weekly_goal_kg):
    """
    F1: Register a new user
    Returns: (success, message, user_id)
    """
    try:
        with get_db_cursor() as cursor:
            # Check if email already exists
            cursor.execute(
                "SELECT user_id FROM \"User\" WHERE email = %s",
                (email,)
            )
            if cursor.fetchone():
                return False, "Email already registered", None
            
            # Insert new user
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO \"User\" (full_name, email, password_hash, weekly_goal_kg)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
            """, (full_name, email, password_hash, weekly_goal_kg))
            
            user_id = cursor.fetchone()[0]
            return True, "User registered successfully", user_id
            
    except Exception as e:
        return False, f"Registration error: {str(e)}", None

def login_user(email, password):
    """
    F1: Login a user
    Returns: (success, message, user_data)
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT user_id, full_name, email, password_hash, weekly_goal_kg, created_at
                FROM \"User\"
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return False, "User not found", None
            
            if verify_password(password, user['password_hash']):
                user_data = {
                    'user_id': user['user_id'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'weekly_goal_kg': float(user['weekly_goal_kg']),
                    'created_at': user['created_at']
                }
                return True, "Login successful", user_data
            else:
                return False, "Incorrect password", None
                
    except Exception as e:
        return False, f"Login error: {str(e)}", None

# ============================================================
# 5. GROUP MANAGEMENT (F2: Create/Join Groups)
# ============================================================

def create_group(group_name, group_code, user_id):
    """
    F2: Create a new group and add creator as member
    Returns: (success, message, group_id)
    """
    try:
        with get_db_cursor() as cursor:
            # Check if group name or code already exists
            cursor.execute(
                "SELECT group_id FROM \"Group\" WHERE group_name = %s OR group_code = %s",
                (group_name, group_code)
            )
            if cursor.fetchone():
                return False, "Group name or code already exists", None
            
            # Create group
            cursor.execute("""
                INSERT INTO \"Group\" (group_name, group_code)
                VALUES (%s, %s)
                RETURNING group_id
            """, (group_name, group_code))
            
            group_id = cursor.fetchone()[0]
            
            # Add creator to the group
            cursor.execute("""
                INSERT INTO User_Group (user_id, group_id)
                VALUES (%s, %s)
            """, (user_id, group_id))
            
            return True, "Group created successfully", group_id
            
    except Exception as e:
        return False, f"Create group error: {str(e)}", None

def join_group(group_code, user_id):
    """
    F2: Join an existing group using group code
    Returns: (success, message)
    """
    try:
        with get_db_cursor() as cursor:
            # Find group by code
            cursor.execute(
                "SELECT group_id, group_name FROM \"Group\" WHERE group_code = %s",
                (group_code,)
            )
            group = cursor.fetchone()
            
            if not group:
                return False, "Invalid group code"
            
            # Check if user is already in a group
            cursor.execute(
                "SELECT group_id FROM User_Group WHERE user_id = %s",
                (user_id,)
            )
            if cursor.fetchone():
                return False, "You are already in a group. Leave current group first."
            
            # Add user to group
            cursor.execute("""
                INSERT INTO User_Group (user_id, group_id)
                VALUES (%s, %s)
            """, (user_id, group['group_id']))
            
            return True, f"Joined group: {group['group_name']}"
            
    except Exception as e:
        return False, f"Join group error: {str(e)}"

def leave_group(user_id):
    """
    Allow user to leave their current group
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM User_Group WHERE user_id = %s RETURNING group_id",
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return True, "Left group successfully"
            else:
                return False, "You are not in any group"
                
    except Exception as e:
        return False, f"Leave group error: {str(e)}"

def get_user_group(user_id):
    """
    Get the group details for a user
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT g.group_id, g.group_name, g.group_code
                FROM \"Group\" g
                JOIN User_Group ug ON g.group_id = ug.group_id
                WHERE ug.user_id = %s
            """, (user_id,))
            
            group = cursor.fetchone()
            if group:
                return {
                    'group_id': group['group_id'],
                    'group_name': group['group_name'],
                    'group_code': group['group_code']
                }
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# ============================================================
# 6. WEEKLY GOAL MANAGEMENT (F3: Set Weekly Goal)
# ============================================================

def set_weekly_goal(user_id, weekly_goal_kg):
    """
    F3: Set or update user's weekly carbon goal
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE \"User\"
                SET weekly_goal_kg = %s
                WHERE user_id = %s
                RETURNING user_id
            """, (weekly_goal_kg, user_id))
            
            if cursor.fetchone():
                return True, f"Weekly goal set to {weekly_goal_kg} kg"
            return False, "User not found"
            
    except Exception as e:
        return False, f"Set goal error: {str(e)}"

def get_weekly_goal(user_id):
    """
    Get user's current weekly goal
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT weekly_goal_kg FROM \"User\" WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            if result:
                return float(result['weekly_goal_kg'])
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# ============================================================
# 7. ACTIVITY MANAGEMENT (F4: Add/Edit/Delete Activities)
# ============================================================

def get_activity_types():
    """
    Get all available activity types for dropdown menu
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT type_id, type_name, default_unit
                FROM Activity_Type
                ORDER BY type_name
            """)
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'type_id': row['type_id'],
                    'type_name': row['type_name'],
                    'default_unit': row['default_unit']
                })
            return activities
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def add_activity(user_id, type_id, quantity, unit, activity_date):
    """
    F4: Add a new activity for a user
    Returns: (success, message, emission_kg)
    """
    try:
        with get_db_cursor() as cursor:
            # Get emission factor for this activity type
            cursor.execute("""
                SELECT factor_value
                FROM Emission_Factor
                WHERE type_id = %s
                ORDER BY effective_date DESC
                LIMIT 1
            """, (type_id,))
            
            factor = cursor.fetchone()
            if not factor:
                return False, "No emission factor found for this activity type", None
            
            emission_kg = quantity * float(factor['factor_value'])
            
            # Insert activity
            cursor.execute("""
                INSERT INTO Activity (user_id, type_id, quantity, unit, activity_date)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING activity_id
            """, (user_id, type_id, quantity, unit, activity_date))
            
            activity_id = cursor.fetchone()[0]
            
            return True, "Activity added successfully", round(emission_kg, 2)
            
    except Exception as e:
        return False, f"Add activity error: {str(e)}", None

def get_user_activities(user_id, start_date=None, end_date=None):
    """
    Get all activities for a user within a date range
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT a.activity_id, a.quantity, a.unit, a.activity_date,
                       at.type_name, at.default_unit,
                       ef.factor_value,
                       (a.quantity * ef.factor_value) AS emission_kg
                FROM Activity a
                JOIN Activity_Type at ON a.type_id = at.type_id
                JOIN Emission_Factor ef ON a.type_id = ef.type_id
                WHERE a.user_id = %s
            """
            params = [user_id]
            
            if start_date:
                query += " AND a.activity_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND a.activity_date <= %s"
                params.append(end_date)
                
            query += " ORDER BY a.activity_date DESC"
            
            cursor.execute(query, params)
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'activity_id': row['activity_id'],
                    'type_name': row['type_name'],
                    'quantity': float(row['quantity']),
                    'unit': row['unit'],
                    'activity_date': row['activity_date'],
                    'emission_kg': float(row['emission_kg'])
                })
            return activities
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def delete_activity(activity_id, user_id):
    """
    Delete an activity (only if it belongs to the user)
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM Activity
                WHERE activity_id = %s AND user_id = %s
                RETURNING activity_id
            """, (activity_id, user_id))
            
            if cursor.fetchone():
                return True, "Activity deleted successfully"
            return False, "Activity not found or access denied"
            
    except Exception as e:
        return False, f"Delete error: {str(e)}"

def edit_activity(activity_id, user_id, quantity, unit, activity_date):
    """
    Edit an existing activity
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE Activity
                SET quantity = %s, unit = %s, activity_date = %s
                WHERE activity_id = %s AND user_id = %s
                RETURNING activity_id
            """, (quantity, unit, activity_date, activity_id, user_id))
            
            if cursor.fetchone():
                return True, "Activity updated successfully"
            return False, "Activity not found or access denied"
            
    except Exception as e:
        return False, f"Edit error: {str(e)}"

# ============================================================
# 8. EMISSION CALCULATION & VIEWING (F5, F6, F7)
# ============================================================

def calculate_total_emissions(user_id, period='week'):
    """
    F5 & F6: Calculate total emissions for a user
    period can be 'day', 'week', 'month', or 'custom'
    """
    try:
        with get_db_cursor() as cursor:
            today = date.today()
            
            if period == 'day':
                start_date = today
                end_date = today
            elif period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif period == 'month':
                start_date = today.replace(day=1)
                next_month = start_date.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day)
            else:
                return None
            
            cursor.execute("""
                SELECT COALESCE(SUM(a.quantity * ef.factor_value), 0) AS total_emissions
                FROM Activity a
                JOIN Emission_Factor ef ON a.type_id = ef.type_id
                WHERE a.user_id = %s
                AND a.activity_date BETWEEN %s AND %s
            """, (user_id, start_date, end_date))
            
            result = cursor.fetchone()
            return float(result['total_emissions']) if result else 0.0
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 0.0

def get_goal_status(user_id):
    """
    F7: Get goal status (green checkmark or red warning)
    """
    try:
        weekly_total = calculate_total_emissions(user_id, 'week')
        weekly_goal = get_weekly_goal(user_id)
        
        if weekly_goal is None:
            return {'status': 'no_goal', 'message': 'Please set a weekly goal'}
        
        if weekly_total <= weekly_goal:
            return {
                'status': 'met',
                'message': '✅ Goal Met (Green)',
                'current': weekly_total,
                'goal': weekly_goal,
                'remaining': weekly_goal - weekly_total
            }
        else:
            return {
                'status': 'exceeded',
                'message': '❌ Goal Exceeded (Red)',
                'current': weekly_total,
                'goal': weekly_goal,
                'over': weekly_total - weekly_goal
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

# ============================================================
# 9. GROUP LEADERBOARD (F8)
# ============================================================

def get_group_leaderboard():
    """
    F8: Get group leaderboard ranking
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    g.group_name,
                    COUNT(DISTINCT u.user_id) AS total_members,
                    COUNT(DISTINCT CASE WHEN wgs.goal_met = TRUE THEN wgs.user_id END) AS members_met_goal,
                    ROUND(
                        (COUNT(DISTINCT CASE WHEN wgs.goal_met = TRUE THEN wgs.user_id END) * 100.0) / 
                        NULLIF(COUNT(DISTINCT u.user_id), 0), 2
                    ) AS success_percentage
                FROM "Group" g
                JOIN User_Group ug ON g.group_id = ug.group_id
                JOIN "User" u ON ug.user_id = u.user_id
                LEFT JOIN Weekly_Goal_Status wgs ON u.user_id = wgs.user_id
                    AND wgs.week_start_date = DATE_TRUNC('week', CURRENT_DATE)
                GROUP BY g.group_name, g.group_id
                ORDER BY success_percentage DESC
            """)
            
            leaderboard = []
            rank = 1
            for row in cursor.fetchall():
                leaderboard.append({
                    'rank': rank,
                    'group_name': row['group_name'],
                    'total_members': row['total_members'],
                    'members_met_goal': row['members_met_goal'],
                    'success_percentage': float(row['success_percentage']) if row['success_percentage'] else 0.0
                })
                rank += 1
            return leaderboard
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def get_group_members(group_id):
    """
    Get all members of a group with their goal status
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.user_id,
                    u.full_name,
                    u.weekly_goal_kg,
                    wgs.goal_met,
                    wgs.total_emissions_kg
                FROM "User" u
                JOIN User_Group ug ON u.user_id = ug.user_id
                LEFT JOIN Weekly_Goal_Status wgs ON u.user_id = wgs.user_id
                    AND wgs.week_start_date = DATE_TRUNC('week', CURRENT_DATE)
                WHERE ug.group_id = %s
            """, (group_id,))
            
            members = []
            for row in cursor.fetchall():
                members.append({
                    'user_id': row['user_id'],
                    'full_name': row['full_name'],
                    'weekly_goal_kg': float(row['weekly_goal_kg']) if row['weekly_goal_kg'] else None,
                    'goal_met': row['goal_met'],
                    'total_emissions_kg': float(row['total_emissions_kg']) if row['total_emissions_kg'] else 0.0
                })
            return members
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

# ============================================================
# 10. COMPARISON TOOL (F9)
# ============================================================

def compare_activities(type_id_1, type_id_2, quantity):
    """
    F9: Compare two activities and show savings
    """
    try:
        with get_db_cursor() as cursor:
            # Get emission factors for both activities
            cursor.execute("""
                SELECT at.type_name, ef.factor_value
                FROM Emission_Factor ef
                JOIN Activity_Type at ON ef.type_id = at.type_id
                WHERE ef.type_id IN (%s, %s)
                ORDER BY ef.effective_date DESC
            """, (type_id_1, type_id_2))
            
            factors = cursor.fetchall()
            if len(factors) < 2:
                return None
            
            factor_dict = {row['type_name']: float(row['factor_value']) for row in factors}
            type_names = list(factor_dict.keys())
            
            emission_1 = quantity * factor_dict[type_names[0]]
            emission_2 = quantity * factor_dict[type_names[1]]
            
            savings = abs(emission_1 - emission_2)
            better_option = type_names[0] if emission_1 < emission_2 else type_names[1]
            
            return {
                'activity_1': type_names[0],
                'emission_1': round(emission_1, 2),
                'activity_2': type_names[1],
                'emission_2': round(emission_2, 2),
                'savings': round(savings, 2),
                'better_option': better_option,
                'message': f"Switching from {type_names[0]} to {type_names[1]} would save you {round(savings, 2)} kg of CO₂"
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# ============================================================
# 11. HISTORICAL TRENDS (F10)
# ============================================================

def get_historical_trends(user_id, weeks=4):
    """
    F10: Get weekly emissions for the past N weeks
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('week', a.activity_date) AS week_start,
                    SUM(a.quantity * ef.factor_value) AS weekly_emission
                FROM Activity a
                JOIN Emission_Factor ef ON a.type_id = ef.type_id
                WHERE a.user_id = %s
                AND a.activity_date >= DATE_TRUNC('week', CURRENT_DATE) - (%s * INTERVAL '1 week')
                GROUP BY DATE_TRUNC('week', a.activity_date)
                ORDER BY week_start ASC
            """, (user_id, weeks))
            
            trends = []
            for row in cursor.fetchall():
                trends.append({
                    'week_start': row['week_start'].strftime('%Y-%m-%d'),
                    'emission_kg': float(row['weekly_emission']) if row['weekly_emission'] else 0.0
                })
            return trends
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

# ============================================================
# 12. DASHBOARD DATA (Combined for main page)
# ============================================================

def get_dashboard_data(user_id):
    """
    Get all data needed for the user dashboard in one call
    """
    try:
        group = get_user_group(user_id)
        weekly_total = calculate_total_emissions(user_id, 'week')
        monthly_total = calculate_total_emissions(user_id, 'month')
        goal_status = get_goal_status(user_id)
        recent_activities = get_user_activities(user_id, start_date=date.today() - timedelta(days=7))
        trends = get_historical_trends(user_id, 4)
        
        return {
            'user_id': user_id,
            'group': group,
            'weekly_total': weekly_total,
            'monthly_total': monthly_total,
            'goal_status': goal_status,
            'recent_activities': recent_activities[:5],  # Last 5 activities
            'historical_trends': trends
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'error': str(e)}

# ============================================================
# 13. CLOSE CONNECTION POOL (Call when app shuts down)
# ============================================================

def close_db_pool():
    """Close all database connections"""
    connection_pool.closeall()

# ============================================================
# END OF database.py
# ============================================================