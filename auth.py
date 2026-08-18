from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        monthly_income = request.form.get('monthly_income', 0.0)
        
        # Validations
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
            
        try:
            monthly_income = float(monthly_income)
            if monthly_income < 0:
                flash('Monthly income cannot be negative.', 'danger')
                return render_template('register.html')
        except ValueError:
            flash('Monthly income must be a valid number.', 'danger')
            return render_template('register.html')
            
        # Check if user already exists
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or email already exists.', 'danger')
            return render_template('register.html')
            
        # Hash password and save user
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            monthly_income=monthly_income
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not username_or_email or not password:
            flash('All fields are required.', 'danger')
            return render_template('login.html')
            
        # Look up user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username/email or password.', 'danger')
            return render_template('login.html')
            
        login_user(user, remember=remember)
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
