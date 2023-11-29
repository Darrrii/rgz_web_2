from flask import Flask, redirect, url_for, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy
from Db import db
from Db.models import users, advertisement

from flask_login import LoginManager

app = Flask(__name__)

app.secret_key = "123"
user_db="daria_rgz"
host_ip="127.0.0.1"
host_port="5432"
database_name='rgz_base'  
password='123'

app.config['SQLALCHEMY_DATABASE_URI']= f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQALCHEMY_TRACK_MODIFICATIONS']= False

db.init_app(app)
