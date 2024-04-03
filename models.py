from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(16), unique=True, nullable=False)
    pass_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(48), nullable=False)
    stream = db.Column(db.String(50))
    is_librarian = db.Column(db.Boolean, default=False)
    books_issued = db.Column(db.Integer, nullable=False, default=0)

class Section(db.Model):
    section_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.String(200))
    date_created = db.Column(db.Date, nullable=False)

    books = db.relationship('Book', backref='section', lazy=True, cascade='all, delete-orphan') #This creates a relationship between the two tables itself using the section_id which is the foreign key in Book. Now, we don't have to give specific SQL query to select all the books from Book table where section_id in both tables is matching.
    #backref helps in getting the name of section of the book. If we try to get section.books, we will get all the books in the section and when we try to get book.section we will get complete section object in that case too.
    #lazy just optimizes our work. It restricts the code to fetch all the books of all the sections all the time. Instead, it only works when we call it explicityly.

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    author = db.Column(db.String, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.section_id'), nullable=False)
    content = db.Column(db.String, nullable=False)
    image = db.Column(db.String)
    pages = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String, nullable=False)
    issue_num = db.Column(db.Integer, nullable=False, default=0)

class Requests(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    is_issued = db.Column(db.Boolean, nullable=True)
    is_returned = db.Column(db.Boolean, nullable=True)
    issue_date = db.Column(db.Date)
    return_date = db.Column(db.Date)

    req_users = db.relationship('User', backref='requests', lazy=True)
    req_books = db.relationship('Book', backref='books', lazy=True)

with app.app_context():
    db.create_all()

    # If librarian is not there, it will create the librarian
    librarian = User.query.filter_by(is_librarian=True).first()
    if not librarian:
        password_hash = generate_password_hash('Admin')
        librarian = User(user_name='Admin', pass_hash=password_hash, name='Admin', is_librarian=True)
        db.session.add(librarian)
        db.session.commit()