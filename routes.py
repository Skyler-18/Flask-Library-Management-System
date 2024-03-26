from flask import render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

def authentication(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for('login'))
    return check

@app.route('/index')
@authentication
def index():
    # Checking if user_id is present in cookies i.e. whether user has an account or not
    # Checking is done with authentication decorator
    return "Yet to come"        

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm-password')
    name = request.form.get('name')
    stream = request.form.get('stream')
    
    if not username or not password or not confirm_password:
        flash("Please fill out the required fields")
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash("Password does not match with Confirm Password")
        return redirect(url_for('register'))
    
    user = User.query.filter_by(user_name=username).first()

    if user:
        flash("Username already exists. Choose another username.")
        return redirect(url_for('register'))

    password_hash = generate_password_hash(password)

    new_user = User(user_name=username, pass_hash=password_hash, name=name, stream=stream)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please fill out the required fields")
        return redirect(url_for('login'))

    user = User.query.filter_by(user_name=username).first()

    if not user:
        flash("Username does not exist. Register before logging in.")
        return redirect(url_for('login'))
    
    if not check_password_hash(user.pass_hash, password):
        flash("Incorrect Password")
        return redirect(url_for('login'))

    session['user_id'] = user.user_id
    flash('Login Successful')
    return redirect(url_for('index'))

@app.route('/profile')
@authentication
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)