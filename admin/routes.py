from flask import render_template, request, redirect, url_for, session, flash, jsonify
from . import admin_bp
from product import INITIAL_PRODUCTS, save_picture
from models import User
from extensions import db
from werkzeug.security import generate_password_hash
from sqlalchemy import text


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Successfully logged in as Admin', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('adminPage/login.html', error='Invalid admin credentials')
    return render_template('adminPage/login.html')


@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    total_orders = db.session.execute(text('SELECT COUNT(*) FROM orders')).scalar() or 0
    total_revenue = db.session.execute(text('SELECT SUM(total) FROM orders')).scalar() or 0
    total_users = User.query.count()

    total_products = len(INITIAL_PRODUCTS)
    recent_orders = []

    return render_template(
        'adminPage/dashboard.html',
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_users=total_users,
        total_products=total_products,
        recent_orders=recent_orders
    )


@admin_bp.route('/products')
def products_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    return render_template('adminPage/products.html', products=INITIAL_PRODUCTS)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
def add_product_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', 0)
        quantity = request.form.get('quantity', 0)
        description = request.form.get('description', '').strip()

        # Handle uploaded file only
        file = request.files.get('image_file')
        uploaded_path = save_picture(file) if file else None

        if not name or not category:
            flash('Product name and category are required.', 'error')
            return render_template('adminPage/add_product.html')

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            flash('Price and quantity must be valid numbers.', 'error')
            return render_template('adminPage/add_product.html')

        new_id = max((p['id'] for p in INITIAL_PRODUCTS), default=0) + 1
        new_product = {
            'id': new_id,
            'name': name,
            'category': category,
            'price': price,
            'quantity': quantity,
            'description': description,
            'image': uploaded_path,
            'img': uploaded_path
        }

        INITIAL_PRODUCTS.append(new_product)
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products_page'))

    return render_template('adminPage/add_product.html')

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product_page(product_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    product = next((p for p in INITIAL_PRODUCTS if p['id'] == product_id), None)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('admin.products_page'))

    if request.method == 'POST':
        product['name'] = request.form.get('name', '').strip()
        product['category'] = request.form.get('category', '').strip()
        product['price'] = float(request.form.get('price', 0))
        product['quantity'] = int(request.form.get('quantity', 0))
        product['description'] = request.form.get('description', '').strip()

        file = request.files.get('image_file') or request.files.get('image')
        uploaded_path = save_picture(file) if file else None

        if uploaded_path:
            product['image'] = uploaded_path
            product['img'] = uploaded_path

        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products_page'))

    return render_template('adminPage/edit_product.html', product=product)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product_page(product_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    product = next((p for p in INITIAL_PRODUCTS if p['id'] == product_id), None)
    if product:
        INITIAL_PRODUCTS.remove(product)
        flash('Product deleted successfully.', 'success')
    else:
        flash('Product not found.', 'error')
    return redirect(url_for('admin.products_page'))


@admin_bp.route('/users')
def users_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    search_q = request.args.get('q', '').strip()
    role_filter = request.args.get('role', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = User.query

    if search_q:
        query = query.filter(
            (User.first_name.ilike(f'%{search_q}%')) |
            (User.last_name.ilike(f'%{search_q}%')) |
            (User.email.ilike(f'%{search_q}%'))
        )
    if role_filter:
        query = query.filter(User.role == role_filter)
    if status_filter:
        query = query.filter(User.status == status_filter)

    users = query.all()

    total_users = User.query.count()
    active_users = User.query.filter_by(status='Active').count()
    inactive_users = User.query.filter_by(status='Inactive').count()

    return render_template(
        'adminPage/users.html',
        users=users,
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        search_q=search_q,
        role_filter=role_filter,
        status_filter=status_filter
    )


@admin_bp.route('/users/add', methods=['POST'])
def add_user():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    email = request.form.get('email', '').strip()

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('A user with this email already exists.', 'error')
        return redirect(url_for('admin.users_page'))

    default_password = generate_password_hash('DefaultPassword123!')

    # Handle avatar file upload only
    file = request.files.get('image_file')
    uploaded_path = save_picture(file) if file else None

    new_user = User(
        first_name=request.form.get('firstName', '').strip(),
        last_name=request.form.get('lastName', '').strip(),
        email=email,
        image=uploaded_path,  # Saves relative path or None
        role=request.form.get('role', 'User'),
        status=request.form.get('status', 'Active'),
        password_hash=default_password
    )
    db.session.add(new_user)
    db.session.commit()
    flash('User created successfully!', 'success')
    return redirect(url_for('admin.users_page'))


@admin_bp.route('/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    user = User.query.get_or_404(user_id)
    user.first_name = request.form.get('firstName', '').strip()
    user.last_name = request.form.get('lastName', '').strip()
    user.email = request.form.get('email', '').strip()
    user.role = request.form.get('role', 'User')
    user.status = request.form.get('status', 'Active')

    file = request.files.get('image_file') or request.files.get('image')
    uploaded_path = save_picture(file) if file else None

    if uploaded_path:
        user.image = uploaded_path

    db.session.commit()
    flash(f'User "{user.first_name}" updated successfully!', 'success')
    return redirect(url_for('admin.users_page'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.first_name} {user.last_name}" deleted successfully.', 'success')
    return redirect(url_for('admin.users_page'))


@admin_bp.route('/customers')
def customers_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    query = text('''
                 SELECT users.id,
                        users.first_name,
                        users.last_name,
                        users.email,
                        users.status,
                        users.image,
                        users.created_at,
                        COUNT(orders.id)               AS total_orders,
                        COALESCE(SUM(orders.total), 0) AS total_spent
                 FROM users
                          LEFT JOIN orders ON users.id = orders.user_id
                 GROUP BY users.id
                 ORDER BY users.id DESC
                 ''')
    customers = db.session.execute(query).mappings().all()
    return render_template('adminPage/customers.html', customers=customers)


@admin_bp.route('/orders')
def orders_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    orders = db.session.execute(text('SELECT * FROM orders ORDER BY created_at DESC')).mappings().all()
    return render_template('adminPage/orders.html', orders=orders)


@admin_bp.route('/orders/<int:order_id>')
def order_detail_page(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    order = db.session.execute(text('SELECT * FROM orders WHERE id = :id'), {'id': order_id}).mappings().first()
    items = db.session.execute(text('SELECT * FROM order_items WHERE order_id = :id'),
                               {'id': order_id}).mappings().all() if order else []

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin.orders_page'))
    return render_template('adminPage/order_detail.html', order=order, items=items)