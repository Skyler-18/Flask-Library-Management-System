from flask import render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Section
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

def authentication(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please Login To Continue")
            return redirect(url_for('login'))
    return check

def admin_check(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please Login To Continue")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash("You Are Not Authorized To Access This Page")
            return redirect(url_for('lib_dashboard'))
        return func(*args, **kwargs)
    return check

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('lib_dashboard'))
    else:
        return "This will be the main page when the application is opened."        


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
        flash("Please Fill Out The Required Fields")
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash("Password Does Not Match With Confirm Password")
        return redirect(url_for('register'))
    
    user = User.query.filter_by(user_name=username).first()
    if user:
        flash("Username Already exists, Choose Another Username")
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
        flash("Please Fill Out The Required Fields")
        return redirect(url_for('login'))

    user = User.query.filter_by(user_name=username).first()
    if not user:
        flash("Username Is Not Correct")
        return redirect(url_for('login'))
    
    if not check_password_hash(user.pass_hash, password):
        flash("Incorrect Password")
        return redirect(url_for('login'))

    if not user.is_admin:
        flash("You Are Not A Librarian, Not Authorized To Access This Page")
        return redirect(url_for('login'))
    
    session['user_id'] = user.user_id
    flash('Login Successful')
    return redirect(url_for('lib_dashboard'))


@app.route('/librarian/dashboard/profile')
@authentication
def lib_profile():
    user = User.query.get(session['user_id'])
    # Checking if user_id is present in cookies i.e. whether user has an account or not
    # Checking is done with authentication decorator
    return render_template('lib_profile.html')

@app.route('/logout')
@authentication
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))


@app.route('/librarian/dashboard')
@authentication
def lib_dashboard():
    sections = Section.query.all()
    user = User.query.get(session['user_id'])
    return render_template('lib_dashboard.html', username=user.user_name, sections=sections)


@app.route('/librarian/section/add')
@admin_check
def add_category():
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%Y-%m-%d")
    return render_template('category/add.html', current_date=formatted_date)

@app.route('/librarian/section/add', methods=['POST'])
@admin_check
def add_category_post():
    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')

    if not title:
        flash('Please Enter The Title For The Section')
        return redirect(url_for('add_category'))
    
    if len(title) > 10:
        flash('Title Can Contain At-Most 10 Characters')
        return redirect(url_for('add_category'))
    
    if len(description) > 100:
        flash('Descrition Can Contain At Most 100 Characters')
        return redirect(url_for('add_category'))
    
    section = Section.query.filter_by(title=title).first()
    if section:
        flash('This Section Already Exists, Choose A Different Name')
        return redirect(url_for('add_category'))
    
    section = Section(title=title, description=description, date_created=date)
    db.session.add(section)
    db.session.commit()

    flash('Section Added Successfully')
    return redirect(url_for('lib_dashboard'))

@app.route('/librarian/section/edit/<int:id>/')
@admin_check
def edit_category(id):
    section = Section.query.get(id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_dashboard'))
    return render_template('category/edit.html', section=section)

@app.route('/librarian/section/edit/<int:id>/', methods=['POST'])
@admin_check
def edit_category_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_dashboard'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')

    if not title:
        flash('Please Enter The Title For The Category')
        return redirect(url_for('edit_category', id=id))
    
    if len(title) > 10:
        flash('Title Can Contain At-Most 10 Characters')
        return redirect(url_for('edit_category', id=id))
    
    if len(description) > 100:
        flash('Descrition Can Contain At-Most 100 Characters')
        return redirect(url_for('edit_category', id=id))
    
    # section_title = Section.query.filter_by(title=title).first()
    # section_id = Section.query.get(id)
    if title != section.title:
        section_title = Section.query.filter_by(title=title).first()
        if section_title:
            flash('This Section Already Exists, Choose A Different Name.')
            return redirect(url_for('edit_category', id=id))
    
    section.title = title
    section.description = description
    section.date_created = date
    db.session.commit()

    flash('Section Edited Successfully')
    return redirect(url_for('lib_dashboard'))

@app.route('/librarian/section/show/<int:id>/')
@admin_check
def show_category(id):
    return "Show Category form to arrive soon"

@app.route('/librarian/section/delete/<int:id>/')
@admin_check
def delete_category(id):
    section = Section.query.get(id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_dashboard'))
    return render_template('category/delete.html', section=section)

@app.route('/category/delete/<int:id>/', methods=['POST'])
@admin_check
def delete_category_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_dashboard'))
    
    db.session.delete(section)
    db.session.commit()

    flash('Section Deleted Successfully')
    return redirect(url_for('lib_dashboard'))

@app.route('/add/book')
@admin_check
def add_book():
    return "Add Book form to arrive soon"