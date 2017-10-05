from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_wtf import Form
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, BooleanField, validators
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
import cgi

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:build-a-blog@localhost:3306/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    username = db.Column(db.String(30))
    password = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
       
    def __init__(self, first_name, last_name, username, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

class Blog_Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_name = db.Column(db.String(120))
    post_body = db.Column(db.Text)
    
    # TODO: add a ratings column to the Movie table

    def __init__(self, post_name, post_body):
        self.post_name = post_name
        self.post_body = post_body

    def __repr__(self):
        return '<Blog_Post %r>' % self.name


class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

class TestForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            flash('You are now registered and can log in', 'success')
            redirect(url_for('index'))
        else:
            flash('Please correct the issues below', 'danger')
            return render_template('register.html', form=form)
    
    return render_template('register.html', form=form)

@app.route('/test', methods=['GET', 'POST'])
def test():
    form = TestForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            flash('You are now registered and can log in', 'success')
            redirect(url_for('index'))
        else:
            flash('Please correct the issues below', 'danger')
            return render_template('test.html', form=form)
    
    return render_template('test.html', form=form)

if __name__ == "__main__":
    app.secret_key = "secretkey"
    app.run(debug=True)
