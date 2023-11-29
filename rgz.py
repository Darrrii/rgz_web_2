from flask import Blueprint, render_template, request, redirect, session, Flask, jsonify
from Db import db
from Db.models import users, advertisement
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, current_user
import psycopg2
from flask_restful import Resource, Api

app = Flask(__name__)
app.secret_key="123"

def dbConnect():
    conn=psycopg2.connect( host="127.0.0.1",port="5433", database= "rgz_base", user='daria_rgz', password='123')
    return conn

def dbClose(cursor, connection):
    cursor.close()
    connection.close()


@app.route('/index')
def index():
    advertisement = advertisement.query.all()
    return render_template('index.html', advertisement=advertisement)

@app.route('/register')
def register():
    if request.method =="GET":
        return render_template("register.html")
    errors=''
    username_form= request.form.get("username")
    password_form= request.form.get("password")

    if username_form=='' or password_form =='':
        errors='Пожалуйста, заполните все поля'
        return render_template('register.html', errors=errors)

    isUserExists=users.query.filter_by(username= username_form).first()

    if isUserExists is not None:
        errors='Пользователь с данным именем уже существует'
        return render_template("register.html", errors=errors)

    if len(password_form)<5:
        errors='Придумайте более сложный пароль'
        return render_template("register.html", errors=errors)

    hashedPswd= generate_password_hash(password_form, method='pbkdf2')
    newUser=users(username=username_form, password=hashedPswd)

    db.session.add(newUser)
    db.session.commit()

    return render_template('register.html')

@app.route('/login')
def login():
    if request.method =="GET":
        return render_template("login.html")
    
    errors=''
    username_form= request.form.get("username")
    password_form= request.form.get("password")

    if username_form =='' or password_form == '':
        errors= 'Пожалуйста, заполните все поля'
        return render_template("login.html", errors=errors)

    my_user= users.query.filter_by(username=username_form).first()

    if my_user is None:
        errors='Такой пользователь уже существует'
        return render_template('login.html',errors=errors)
    
    if not check_password_hash(my_user.password, password_form):
        errors='Введен неправильный пароль'
        return render_template('login.html', errors=errors)

    if my_user is not None:
        if check_password_hash(my_user.password, password_form):
            login_user(my_user, remember=False)
            return redirect("/register")
    return render_template("login.html")


@app.route('/create')
def create():
    return render_template('create.html')

# Роут для получения списка объявлений
@app.route('/advertisement', methods=['GET'])
def get_advertisements():
    advertisement = advertisement.query.all()
    return jsonify([{'topic': ad.topic, 'text': ad.text, 'author': ad.author} for ad in advertisement]), 200

# Роут для создания объявления
@app.route('/advertisement', methods=['POST'])
def create_advertisement():
    topic = request.form.get('topic')
    text = request.form.get('text')
    author = request.form.get('author')
    advertisement = advertisement(topic=topic, text=text, author=author)
    db.session.add(advertisement)
    db.session.commit()
    return jsonify({'message': 'Advertisement created successfully'}), 201

# Роут для редактирования объявления
@app.route('/advertisement/<int:/advertisement_id>', methods=['PUT'])
def edit_advertisement(advertisement_id):
    advertisement = advertisement.query.get(advertisement_id)
    if advertisement:
        advertisement.topic = request.json['topic']
        advertisement.text = request.json['text']
        db.session.commit()
        return jsonify({'message': 'Advertisement edited successfully'}), 200
    return jsonify({'message': 'Advertisement not found'}), 404

# Роут для удаления объявления
@app.route('/advertisement/<int:advertisement_id>', methods=['DELETE'])
def delete_advertisement(advertisement_id):
    advertisement = advertisement.query.get(advertisement_id)
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
    user = users(username=username, password=password, name=name, avatar=avatar, email=email, about=about)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# Роут для удаления пользователя (только для администратора)
@app.route('/users/<string:username>', methods=['DELETE'])
def delete_user(username):
    admin_username = request.headers.get('username')
    admin_password = request.headers.get('password')
    if admin_username == 'admin' and admin_password == 'admin':
        user = users.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'message': 'Unauthorized'}), 401

if __name__ == '__main__':
    db.create_all()
    app.run()