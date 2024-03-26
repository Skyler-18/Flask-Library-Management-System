from app import app
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.sql import func
# from sqlalchemy import DateTime
from werkzeug.security import generate_password_hash


db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(32), unique=True, nullable=False)
    pass_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(50))
    stream = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    books_issued = db.Column(db.Integer, nullable=False, default=0)

class Section(db.Model):
    section_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(500))
    date_created = db.Column(db.Date, nullable=False)

    books = db.relationship('Book', backref='section', lazy=True) #This creates a relationship between the two tables itself using the section_id which is the foreign key in Book. Now, we don't have to give specific SQL query to select all the books from Book table where section_id in both tables is matching.
    #backref helps in getting the name of section of the book. If we try to get section.books, we will get all the books in the section and when we try to get book.section we will get complete section object in that case too.
    #lazy just optimizes our work. It restricts the code to fetch all the books of all the sections all the time. Instead, it only works when we call it explicityly.

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True, nullable=False)
    author = db.Column(db.String(128), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.section_id'), nullable=False)
    content = db.Column(db.String(128))
    image = db.Column(db.String(128))
    rating = db.Column(db.String(128))
    is_issued = db.Column(db.Boolean, nullable=False, default=False)

    # wlists = db.relationship('Waiting_list', backref='books', lazy=True)

class Waitinglist(db.Model):
    wl_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    req_days = db.Column(db.Integer, default=7)

class Approval(db.Model):
    approval_id = db.Column(db.Integer, primary_key=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    # book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    wl_id = db.Column(db.Integer, db.ForeignKey('waitinglist.wl_id'), nullable=False)
    datetime_issued = db.Column(db.DateTime, nullable=False)

with app.app_context():
    db.create_all()

    # If admin is not there, it will create the admin
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash('Admin')
        admin = User(user_name='Admin', pass_hash=password_hash, name='Admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()