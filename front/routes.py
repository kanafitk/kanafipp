import os
import json
import sqlite3
import uuid
import html
from datetime import datetime
import requests
from flask import render_template, request, redirect, url_for, session, flash, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from . import front_bp
from product import INITIAL_PRODUCTS
from config import DB_PATH

DATABASE = DB_PATH
categories_list = ["Electronics", "Fashion", "Furniture", "Accessories", "Gaming"]

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@front_bp.get("/")
def home():
    featured = INITIAL_PRODUCTS[:4]
    return render_template("front/index.html", featured_products=featured)

@front_bp.get("/products")
def products():
    return render_template("front/products.html", products=INITIAL_PRODUCTS)

@front_bp.get("/product/<int:product_id>")
def product(product_id):
    product_obj = next((p for p in INITIAL_PRODUCTS if p["id"] == product_id), None)
    if product_obj is None:
        flash("Product not found.", "error")
        return redirect(url_for('front.products'))
    return render_template("front/product.html", product=product_obj)

@front_bp.route('/categories')
def categories():
    return render_template("front/category.html", categories=categories_list, products=INITIAL_PRODUCTS)

@front_bp.get("/cart")
def cart():
    try:
        cart_cookie = json.loads(request.cookies.get('cart', '{}'))
    except Exception:
        cart_cookie = {}
        
    cart_items = []
    subtotal = 0.0
    for pid_str, qty in cart_cookie.items():
        try:
            pid = int(pid_str)
            qty = int(qty)
        except ValueError:
            continue
        product_obj = next((p for p in INITIAL_PRODUCTS if p["id"] == pid), None)
        if product_obj:
            cart_items.append({"product": product_obj, "quantity": qty})
            subtotal += product_obj["price"] * qty
            
    return render_template("front/cart.html", cart_items=cart_items, subtotal=subtotal)

@front_bp.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product_obj = next((p for p in INITIAL_PRODUCTS if p["id"] == product_id), None)
    if not product_obj:
        flash("Product not found.", "error")
        return redirect(url_for('front.products'))
        
    try:
        cart_cookie = json.loads(request.cookies.get('cart', '{}'))
    except Exception:
        cart_cookie = {}
        
    try:
        quantity = int(request.form.get("quantity", 1))
        if quantity <= 0:
            quantity = 1
    except ValueError:
        quantity = 1
        
    pid_str = str(product_id)
    cart_cookie[pid_str] = cart_cookie.get(pid_str, 0) + quantity
    
    resp = make_response(redirect(url_for('front.cart')))
    resp.set_cookie('cart', json.dumps(cart_cookie), max_age=30*24*60*60, httponly=True)
    flash(f"Added {product_obj['name']} to cart.", "success")
    return resp

@front_bp.post("/cart/update")
def update_cart():
    product_id = request.form.get("product_id")
    action = request.form.get("action")
    
    if not product_id or not action:
        return redirect(url_for('front.cart'))
        
    try:
        cart_cookie = json.loads(request.cookies.get('cart', '{}'))
    except Exception:
        cart_cookie = {}
        
    pid_str = str(product_id)
    if pid_str in cart_cookie:
        if action == 'increase':
            cart_cookie[pid_str] = int(cart_cookie[pid_str]) + 1
        elif action == 'decrease':
            new_qty = int(cart_cookie[pid_str]) - 1
            if new_qty <= 0:
                cart_cookie.pop(pid_str)
            else:
                cart_cookie[pid_str] = new_qty
        elif action == 'remove':
            cart_cookie.pop(pid_str)
            
    resp = make_response(redirect(url_for('front.cart')))
    resp.set_cookie('cart', json.dumps(cart_cookie), max_age=30*24*60*60, httponly=True)
    return resp

@front_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    try:
        cart_cookie = json.loads(request.cookies.get('cart', '{}'))
    except Exception:
        cart_cookie = {}
        
    cart_items = []
    subtotal = 0.0
    for pid_str, qty in cart_cookie.items():
        try:
            pid = int(pid_str)
            qty = int(qty)
        except ValueError:
            continue
        product_obj = next((p for p in INITIAL_PRODUCTS if p["id"] == pid), None)
        if product_obj:
            cart_items.append({"product": product_obj, "quantity": qty})
            subtotal += product_obj["price"] * qty
            
    if not cart_items:
        flash("Your cart is empty. Cannot checkout.", "error")
        return redirect(url_for('front.cart'))
        
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        address = request.form.get("address")
        city = request.form.get("city")
        zip_code = request.form.get("zip")
        payment_method = request.form.get("payment", "Credit Card")
        
        user_id = session.get("user_id")
        created_at = datetime.now().strftime("%B %d, %Y %I:%M %p")
        
        serialized_items = []
        for item in cart_items:
            serialized_items.append({
                "id": item["product"]["id"],
                "name": item["product"]["name"],
                "price": item["product"]["price"],
                "quantity": item["quantity"],
                "img": item["product"]["img"]
            })
            
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, first_name, last_name, email, address, city, zip, payment_method, total, items, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, first_name, last_name, email, address, city, zip_code, payment_method, subtotal, json.dumps(serialized_items), created_at
        ))
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        first_name_esc = html.escape(first_name or "")
        last_name_esc = html.escape(last_name or "")
        email_esc = html.escape(email or "")
        address_esc = html.escape(address or "")
        city_esc = html.escape(city or "")
        zip_code_esc = html.escape(zip_code or "")
        payment_method_esc = html.escape(payment_method or "")
        
        msg_lines = [
            "🔔 <b>NEW ORDER RECEIVED</b> 🔔",
            f"Order Ref: #ORD-{order_id + 10000}",
            f"Date: {created_at}",
            "---------------------------------------",
            "<b>Customer Info:</b>",
            f"Name: {first_name_esc} {last_name_esc}",
            f"Email: {email_esc}",
            f"Shipping: {address_esc}, {city_esc}, {zip_code_esc}",
            f"Payment: {payment_method_esc}",
            "---------------------------------------",
            "<b>Items Ordered:</b>",
        ]
        for item in cart_items:
            item_name_esc = html.escape(item['product']['name'])
            item_sub = item["product"]["price"] * item["quantity"]
            msg_lines.append(f"• {item_name_esc} x{item['quantity']} - ${item_sub:.2f}")
            
        msg_lines.extend([
            "---------------------------------------",
            f"<b>Grand Total: ${subtotal:.2f}</b>",
            "---------------------------------------",
            "🚀 <i>Status: Preparing for dispatch</i>"
        ])
        
        telegram_message = "\n".join(msg_lines)
        telegram_success = False
        if bot_token and chat_id and bot_token != "YOUR_TELEGRAM_BOT_TOKEN" and chat_id != "YOUR_TELEGRAM_CHAT_ID":
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {"chat_id": chat_id, "text": telegram_message, "parse_mode": "HTML"}
                r = requests.post(url, json=payload, timeout=8)
                if r.status_code == 200:
                    telegram_success = True
            except Exception as e:
                current_app.logger.error(f"Failed to send Telegram notification: {e}")
        
        if not telegram_success:
            flash("Order placed! (Note: Telegram notification skipped - bot not configured)", "success")
        else:
            flash("Order placed successfully! Telegram bot has been notified.", "success")
            
        session['last_order'] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "address": address,
            "city": city,
            "zip": zip_code,
            "payment_method": payment_method,
            "total": subtotal
        }
        
        resp = make_response(redirect(url_for('front.checkout_success')))
        resp.delete_cookie('cart')
        return resp
        
    return render_template("front/checkout.html", cart_items=cart_items, subtotal=subtotal)

@front_bp.get("/checkout/success")
def checkout_success():
    order = session.get('last_order')
    if not order:
        return redirect(url_for('front.home'))
    return render_template("front/checkout_success.html", order=order)

@front_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")
        current_app.logger.info(f"Contact Form Submission: From={name} <{email}>, Subject={subject}, Message={message}")
        flash("Thank you for contacting us! We will get back to you shortly.", "success")
        return redirect(url_for('front.contact'))
    return render_template("front/contact.html")

@front_bp.route("/register", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Email and Password are required.", "error")
            return redirect(url_for('front.create_user'))
            
        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO users (email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (email, hashed_password, first_name, last_name))
            conn.commit()
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for('front.login'))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
            return redirect(url_for('front.create_user'))
        finally:
            conn.close()
            
    return render_template("front/create-user.html")

@front_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_first_name'] = user['first_name']
            session['user_last_name'] = user['last_name']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            flash("Welcome back!", "success")
            return redirect(url_for('front.account'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('front.login'))
            
    return render_template("front/login.html")

@front_bp.get("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for('front.home'))

@front_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            token = str(uuid.uuid4())
            conn.execute('UPDATE users SET reset_token = ? WHERE id = ?', (token, user['id']))
            conn.commit()
            conn.close()
            reset_url = url_for('front.reset_password', token=token, _external=True)
            flash(f"Password reset link generated! Click here to reset: {reset_url}", "success")
            return redirect(url_for('front.forgot_password'))
        else:
            conn.close()
            flash("If that email address exists in our database, we will send you a reset link.", "success")
            return redirect(url_for('front.forgot_password'))
            
    return render_template("front/forgot-password.html")

@front_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE reset_token = ?', (token,)).fetchone()
    
    if not user:
        conn.close()
        flash("Invalid or expired reset token.", "error")
        return redirect(url_for('front.forgot_password'))
        
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            conn.close()
            flash("Passwords do not match.", "error")
            return redirect(url_for('front.reset_password', token=token))
            
        hashed_password = generate_password_hash(password)
        conn.execute('UPDATE users SET password_hash = ?, reset_token = NULL WHERE id = ?', (hashed_password, user['id']))
        conn.commit()
        conn.close()
        
        flash("Password has been reset successfully! Please sign in.", "success")
        return redirect(url_for('front.login'))
        
    conn.close()
    return render_template("front/reset-password.html", token=token)

@front_bp.get("/account")
def account():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please sign in to access your account.", "error")
        return redirect(url_for('front.login'))
        
    conn = get_db()
    orders_rows = conn.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    
    orders = []
    for row in orders_rows:
        order_dict = dict(row)
        try:
            order_dict['items_list'] = json.loads(order_dict['items'])
        except Exception:
            order_dict['items_list'] = []
        orders.append(order_dict)
        
    return render_template("front/account.html", orders=orders)

@front_bp.get("/about")
def about():
    return render_template("front/share/about.html")
