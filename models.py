from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(10), unique=True, nullable=False)
    pass_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    stream = db.Column(db.String(25))
    is_librarian = db.Column(db.Boolean, default=False)
    books_issued = db.Column(db.Integer, nullable=False, default=0)
    books_downloaded = db.Column(db.Integer, nullable=False, default=0)

class Section(db.Model):
    section_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(125))
    date_created = db.Column(db.Date, nullable=False)

    books = db.relationship('Book', backref='section', lazy=True, cascade='all, delete-orphan')
    #This creates a relationship between the two tables itself using the section_id which is the foreign key in Book. Now, we don't have to give specific SQL query to select all the books from Book table where section_id in both tables is matching.
    #backref helps in getting the name of section of the book. If we try to get section.books, we will get all the books in the section and when we try to get book.section we will get complete section object in that case too.
    #lazy just optimizes our work. It restricts the code to fetch all the books of all the sections all the time. Instead, it only works when we call it explicityly.

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    author = db.Column(db.String, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.section_id'))
    content = db.Column(db.String, nullable=False)
    image = db.Column(db.String)
    pages = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String, nullable=False)
    issue_num = db.Column(db.Integer, nullable=False, default=0)

    requests_active = db.relationship('Requests_Active', backref='book', lazy=True, cascade='all, delete-orphan')
    issues_active = db.relationship('Issues_Active', backref='book', lazy=True, cascade='all, delete-orphan')
    requests_rejected = db.relationship('Requests_Rejected', backref='book', lazy=True, cascade='all, delete-orphan')
    issues_expired = db.relationship('Issues_Expired', backref='book', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='book', lazy=True, cascade='all, delete-orphan')


class Requests_Active(db.Model):
    ra_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)

class Issues_Active(db.Model):
    ia_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

class Requests_Rejected(db.Model):
    rr_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    date_rejected = db.Column(db.Date, nullable=False)

class Issues_Expired(db.Model):
    ie_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date, nullable=False)
    cause = db.Column(db.String, nullable=False)


class Feedback(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    review = db.Column(db.String, nullable=False)


with app.app_context():
    db.create_all()

    # If librarian is not there, it will create the librarian
    librarian = User.query.filter_by(is_librarian=True).first()
    if not librarian:
        password_hash = generate_password_hash('librarian')
        librarian = User(user_name='librarian', pass_hash=password_hash, name='Librarian', is_librarian=True)
        db.session.add(librarian)
        db.session.commit()