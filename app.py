import os
import sqlite3
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from config import Config, DB_PATH
from extensions import db, migrate

# Import Blueprints
from admin import admin_bp
from api import api_bp
from front import front_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask extensions
db.init_app(app)
migrate.init_app(app, db)

# Ensure upload directory exists for storing uploaded pictures
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register Blueprints
app.register_blueprint(front_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

# Build error handler to resolve url_for('home') or url_for('admin_login') seamlessly across blueprints
def handle_url_build_error(error, endpoint, values):
    for bp in ('front', 'admin', 'api'):
        bp_endpoint = f"{bp}.{endpoint}"
        if bp_endpoint in app.view_functions:
            return url_for(bp_endpoint, **values)
    raise error

app.url_build_error_handlers.append(handle_url_build_error)

# Legacy route aliases for backward compatibility
@app.route('/admin_login')
def legacy_admin_login():
    return redirect(url_for('admin.admin_login'))

DATABASE = DB_PATH

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                reset_token TEXT,
                role TEXT DEFAULT 'User',
                status TEXT DEFAULT 'Active',
                image TEXT DEFAULT '',
                created_at TEXT
            )
        ''')
        for col, definition in [
            ('role',       "TEXT DEFAULT 'User'"),
            ('status',     "TEXT DEFAULT 'Active'"),
            ('image',      "TEXT DEFAULT ''"),
            ('created_at', "TEXT"),
        ]:
            try:
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
            except Exception:
                pass
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                zip TEXT,
                payment_method TEXT,
                total REAL,
                items TEXT,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                name TEXT,
                price REAL,
                quantity INTEGER,
                image TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        ''')
        conn.commit()

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)