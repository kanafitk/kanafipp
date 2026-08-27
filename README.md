# LuxeShop - Flask E-Commerce Web Application

A modular Flask web application structured into clear Blueprints (`admin`, `api`, `front`), models, and local picture storage.

## Project Directory Structure

```text
pp-pp/
├── .venv/                  # Virtual environment
├── admin/                  # Admin panel blueprint & routes
│   ├── __init__.py
│   └── routes.py
├── api/                    # RESTful API endpoints blueprint
│   ├── __init__.py
│   └── routes.py
├── front/                  # Customer storefront blueprint & routes
│   ├── __init__.py
│   └── routes.py
├── instance/               # Instance data (SQLite database)
│   └── shop.db
├── migrations/             # Flask-Migrate / Alembic migrations
├── models/                 # SQLAlchemy database models
│   ├── __init__.py
│   ├── user.py
│   └── product.py
├── static/                 # Static files (CSS, JS, upload folder)
│   ├── css/
│   │   └── style.css
│   └── uploads/            # Picture storage folder for uploaded images
├── templates/              # HTML templates
│   ├── adminPage/          # Admin templates
│   └── front/              # Storefront templates
├── .gitignore              # Git ignore rules
├── app.py                  # Main Flask application entry point
├── config.py               # Application configuration
├── extensions.py           # Flask extensions (db, migrate)
├── product.py              # Product helpers & picture upload handler
├── README.md               # Project documentation
└── requirements.txt        # Python package dependencies
```

---

## Picture Upload & Storage Folder

- Uploaded pictures are automatically saved to `static/uploads/`.
- Images can be uploaded via product forms in the admin dashboard or REST APIs.
- Uploaded files generate a unique filename to avoid overwriting, and are stored with relative path `/static/uploads/<filename>`.

---

## How to Run

1. Activate your virtual environment:
   ```bash
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```bash
   python app.py
   ```
4. Access the web application in your browser at `http://127.0.0.1:5000`.
