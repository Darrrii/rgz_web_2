from . import db
from flask_login import UserMixin

# Модель объявления
class advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)

def __repr__(self):
        return f'id:{self.id}, username:{self.username}'

# Модель пользователя
class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    about = db.Column(db.Text)