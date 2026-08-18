import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cashly-secret-key-3982471047-xyz'
    
    # Use SQLite by default, but support MySQL or other databases via environment variables
    # E.g., mysql+pymysql://user:password@localhost/cashly
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cashly.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
