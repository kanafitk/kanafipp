import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

INITIAL_PRODUCTS = [
    {"id": 1, "name": "Wireless Headphones", "price": 89.99, "category": "Electronics", "img": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=600&auto=format&fit=crop", "quantity": 25, "description": "Premium wireless over-ear headphones with noise cancellation and 30h battery life."},
    {"id": 2, "name": "Smart Watch", "price": 199.99, "category": "Electronics", "img": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?q=80&w=600&auto=format&fit=crop", "quantity": 15, "description": "Feature-rich smartwatch with health monitoring, GPS, and 7-day battery."},
    {"id": 3, "name": "Leather Jacket", "price": 120.00, "category": "Fashion", "img": "https://images.unsplash.com/photo-1551028719-00167b16eac5?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?q=80&w=600&auto=format&fit=crop", "quantity": 8, "description": "Classic genuine leather jacket with a slim fit and premium stitching."},
    {"id": 4, "name": "Gaming Chair", "price": 250.00, "category": "Gaming", "img": "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?q=80&w=600&auto=format&fit=crop", "quantity": 5, "description": "Ergonomic gaming chair with lumbar support, adjustable armrests, and reclining backrest."},
    {"id": 5, "name": "Modern Sofa", "price": 450.00, "category": "Furniture", "img": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=600&auto=format&fit=crop", "quantity": 3, "description": "Contemporary 3-seater sofa with premium fabric upholstery and solid wood legs."},
    {"id": 6, "name": "Mechanical Keyboard", "price": 75.50, "category": "Gaming", "img": "https://images.unsplash.com/photo-1595225476474-87563907a212?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1595225476474-87563907a212?q=80&w=600&auto=format&fit=crop", "quantity": 20, "description": "TKL mechanical keyboard with Cherry MX switches and customizable RGB backlight."},
    {"id": 7, "name": "Sunglasses", "price": 45.00, "category": "Accessories", "img": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=600&auto=format&fit=crop", "quantity": 30, "description": "Polarized UV400 sunglasses with a lightweight titanium frame and scratch-resistant lenses."},
    {"id": 8, "name": "Minimalist Desk", "price": 320.00, "category": "Furniture", "img": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?q=80&w=600&auto=format&fit=crop", "image": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?q=80&w=600&auto=format&fit=crop", "quantity": 6, "description": "Clean-line solid oak writing desk with cable management and spacious work surface."}
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(file_storage):
    """
    Saves an uploaded image file into the static/uploads folder.
    Returns the relative URL path to the stored picture.
    """
    if not file_storage or file_storage.filename == '':
        return None

    if file_storage and allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        # Generate unique filename to avoid overwriting existing files
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        upload_dir = current_app.config.get(
            'UPLOAD_FOLDER',
            os.path.join(current_app.root_path, 'static', 'uploads')
        )
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_filename)
        file_storage.save(file_path)

        # Return web accessible path relative to static
        return f"/static/uploads/{unique_filename}"

    return None
