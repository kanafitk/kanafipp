from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    first_name    = db.Column(db.Text)
    last_name     = db.Column(db.Text)
    reset_token   = db.Column(db.Text)
    role          = db.Column(db.Text, default='User')
    status        = db.Column(db.Text, default='Active')
    image         = db.Column(db.Text, default='')
    created_at    = db.Column(db.Text, default=lambda: datetime.now().strftime('%Y-%m-%d'))

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'status': self.status,
            'image': self.image,
            'created_at': self.created_at
        }
