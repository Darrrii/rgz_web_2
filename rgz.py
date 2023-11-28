from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///advertisements.db'
db = SQLAlchemy(app)

# Модель объявления
class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), nullable=False)

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    about = db.Column(db.Text)

# Роут для получения списка объявлений
@app.route('/advertisements', methods=['GET'])
def get_advertisements():
    advertisements = Advertisement.query.all()
    return jsonify([{'topic': ad.topic, 'text': ad.text, 'author': ad.author} for ad in advertisements]), 200

# Роут для создания объявления
@app.route('/advertisements', methods=['POST'])
def create_advertisement():
    topic = request.json['topic']
    text = request.json['text']
    author = request.json['author']
    advertisement = Advertisement(topic=topic, text=text, author=author)
    db.session.add(advertisement)
    db.session.commit()
    return jsonify({'message': 'Advertisement created successfully'}), 201

# Роут для редактирования объявления
@app.route('/advertisements/<int:advertisement_id>', methods=['PUT'])
def edit_advertisement(advertisement_id):
    advertisement = Advertisement.query.get(advertisement_id)
    if advertisement:
        advertisement.topic = request.json['topic']
        advertisement.text = request.json['text']
        db.session.commit()
        return jsonify({'message': 'Advertisement edited successfully'}), 200
    return jsonify({'message': 'Advertisement not found'}), 404

# Роут для удаления объявления
@app.route('/advertisements/<int:advertisement_id>', methods=['DELETE'])
def delete_advertisement(advertisement_id):
    advertisement = Advertisement.query.get(advertisement_id)
    if advertisement:
        db.session.delete(advertisement)
        db.session.commit()
        return jsonify({'message': 'Advertisement deleted successfully'}), 200
    return jsonify({'message': 'Advertisement not found'}), 404

# Роут для регистрации пользователя
@app.route('/register', methods=['POST'])
def register_user():
    username = request.json['username']
    password = request.json['password']
    name = request.json['name']
    avatar = request.json['avatar']
    email = request.json['email']
    about = request.json.get('about', '')
    user = User(username=username, password=password, name=name, avatar=avatar, email=email, about=about)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# Роут для удаления пользователя (только для администратора)
@app.route('/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    admin_username = request.headers.get('username')
    admin_password = request.headers.get('password')
    if admin_username == 'admin' and admin_password == 'admin':
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'message': 'Unauthorized'}), 401

if __name__ == '__main__':
    db.create_all()
    app.run()