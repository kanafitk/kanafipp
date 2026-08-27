import sqlite3
from datetime import datetime
from flask import request, jsonify
from werkzeug.security import generate_password_hash
from . import api_bp
from product import INITIAL_PRODUCTS, save_picture
from config import DB_PATH

DATABASE = DB_PATH

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# User REST API
@api_bp.route('/users', methods=['GET'])
def get_users():
    conn = get_db()
    users = conn.execute('SELECT id, first_name, last_name, email, role, status, image, created_at FROM users ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@api_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json(silent=True) or request.form
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name') or '').strip()
    email      = (data.get('email') or '').strip().lower()
    password   = (data.get('password') or '').strip()
    role       = data.get('role', 'User')
    status     = data.get('status', 'Active')

    file = request.files.get('image_file') or request.files.get('image')
    uploaded_path = save_picture(file) if file else None
    image = uploaded_path if uploaded_path else (data.get('image') or '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    password_hash = generate_password_hash(password)
    created_at    = datetime.now().strftime('%Y-%m-%d')

    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            '''INSERT INTO users (email, password_hash, first_name, last_name, role, status, image, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (email, password_hash, first_name, last_name, role, status, image, created_at)
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'id': new_id, 'email': email, 'first_name': first_name,
                        'last_name': last_name, 'role': role, 'status': status,
                        'image': image, 'created_at': created_at}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'An account with this email already exists'}), 409

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(silent=True) or request.form
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name') or '').strip()
    email      = (data.get('email') or '').strip().lower()
    role       = data.get('role', 'User')
    status     = data.get('status', 'Active')

    file = request.files.get('image_file') or request.files.get('image')
    uploaded_path = save_picture(file) if file else None
    image = uploaded_path if uploaded_path else (data.get('image') or '').strip()

    conn = get_db()
    conn.execute(
        '''UPDATE users SET first_name=?, last_name=?, email=?, role=?, status=?, image=?
           WHERE id=?''',
        (first_name, last_name, email, role, status, image, user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'id': user_id, 'email': email, 'first_name': first_name,
                    'last_name': last_name, 'role': role, 'status': status, 'image': image})

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted'}), 200

# Products API
@api_bp.route('/products', methods=['GET'])
def get_products():
    return jsonify(INITIAL_PRODUCTS)

# Image upload API endpoint
@api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files and 'image' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files.get('file') or request.files.get('image')
    uploaded_path = save_picture(file)
    if uploaded_path:
        return jsonify({'url': uploaded_path, 'message': 'Image uploaded successfully'}), 200
    return jsonify({'error': 'Invalid image file or format'}), 400
