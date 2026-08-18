import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from config import Config
from models import db, User
from auth import auth_bp
from api import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extension databases
    db.init_app(app)
    
    # Configure Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    
    # --- PAGE ROUTES ---
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))
        
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')
        
    @app.route('/expenses')
    @login_required
    def expenses():
        return render_template('expenses.html')
        
    @app.route('/budgets')
    @login_required
    def budgets():
        return render_template('budgets.html')
        
    @app.route('/goals')
    @login_required
    def goals():
        return render_template('goals.html')
        
    @app.route('/ai-assistant')
    @login_required
    def ai_assistant():
        return render_template('ai_assistant.html')
        
    # Create tables
    with app.app_context():
        db.create_all()
        
    return app

app = create_app()

if __name__ == '__main__':
    # Run development server
    app.run(host='0.0.0.0', port=5000, debug=True)
