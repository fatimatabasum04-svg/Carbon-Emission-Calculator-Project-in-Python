# app.py - Main Flask Application for Carbon Tracker

from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
import database as db

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this_12345'

# ============================================================
# HOME ROUTE
# ============================================================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        weekly_goal = float(request.form['weekly_goal'])
        
        success, message, user_id = db.register_user(full_name, email, password, weekly_goal)
        
        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('home'))
        else:
            flash(message, 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    success, message, user_data = db.login_user(email, password)
    
    if success:
        session['user_id'] = user_data['user_id']
        session['user_name'] = user_data['full_name']
        flash(f'Welcome back, {user_data["full_name"]}!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash(message, 'danger')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ============================================================
# DASHBOARD ROUTE
# ============================================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('home'))
    
    dashboard_data = db.get_dashboard_data(session['user_id'])
    leaderboard = db.get_group_leaderboard()
    
    return render_template('dashboard.html', 
                         data=dashboard_data, 
                         leaderboard=leaderboard)

# ============================================================
# GROUP MANAGEMENT ROUTES
# ============================================================

@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        group_name = request.form['group_name']
        group_code = request.form['group_code']
        
        success, message, group_id = db.create_group(group_name, group_code, session['user_id'])
        
        if success:
            flash(message, 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')
    
    return render_template('create_group.html')

@app.route('/join_group', methods=['POST'])
def join_group():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    group_code = request.form['group_code']
    success, message = db.join_group(group_code, session['user_id'])
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dashboard'))

@app.route('/leave_group')
def leave_group():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    success, message = db.leave_group(session['user_id'])
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dashboard'))

# ============================================================
# GOAL MANAGEMENT ROUTE
# ============================================================

@app.route('/set_goal', methods=['POST'])
def set_goal():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    weekly_goal = float(request.form['weekly_goal'])
    success, message = db.set_weekly_goal(session['user_id'], weekly_goal)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dashboard'))

# ============================================================
# ACTIVITY MANAGEMENT ROUTES
# ============================================================

@app.route('/add_activity', methods=['GET', 'POST'])
def add_activity():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    activity_types = db.get_activity_types()
    
    if request.method == 'POST':
        type_id = int(request.form['type_id'])
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
        activity_date = datetime.strptime(request.form['activity_date'], '%Y-%m-%d').date()
        
        success, message, emission = db.add_activity(
            session['user_id'], type_id, quantity, unit, activity_date
        )
        
        if success:
            flash(f'{message} Emission: {emission} kg CO₂', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'danger')
    
    return render_template('add_activity.html', activity_types=activity_types)

@app.route('/delete_activity/<int:activity_id>')
def delete_activity(activity_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    success, message = db.delete_activity(activity_id, session['user_id'])
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('dashboard'))

# ============================================================
# LEADERBOARD ROUTE
# ============================================================

@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    leaderboard_data = db.get_group_leaderboard()
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

# ============================================================
# COMPARISON TOOL ROUTE
# ============================================================

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    activity_types = db.get_activity_types()
    comparison_result = None
    
    if request.method == 'POST':
        type_id_1 = int(request.form['type_id_1'])
        type_id_2 = int(request.form['type_id_2'])
        quantity = float(request.form['quantity'])
        
        comparison_result = db.compare_activities(type_id_1, type_id_2, quantity)
    
    return render_template('compare.html', 
                         activity_types=activity_types,
                         result=comparison_result)

# ============================================================
# RUN THE APPLICATION
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)