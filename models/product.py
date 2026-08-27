from extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    price       = db.Column(db.Float, nullable=False)
    category    = db.Column(db.String(100), nullable=False)
    image       = db.Column(db.String(255), default='')
    quantity    = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, default='')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'category': self.category,
            'image': self.image,
            'img': self.image,
            'quantity': self.quantity,
            'description': self.description
        }
