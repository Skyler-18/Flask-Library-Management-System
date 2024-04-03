from flask import render_template, request, redirect, url_for, flash, session, make_response
from app import app
from models import db, User, Section, Book
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os


def authentication(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please Login To Continue")
            return redirect(url_for('student_login'))
    return check

def lib_check(func):
    @wraps(func)
    def check(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please Login To Continue")
            return redirect(url_for('lib_login'))
        
        user = User.query.get(session['user_id'])

        if not user.is_librarian:
            flash("You Are Not Authorized To Access This Page")
            return redirect(url_for('lib_dashboard'))
        return func(*args, **kwargs)
    return check


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('lib_dashboard'))
    else:
        return render_template('index.html')


@app.route('/librarian-login')
def lib_login():
    return render_template('lib_login.html')

@app.route('/librarian-login', methods=['POST'])
def lib_login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please Fill Out The Required Fields")
        return redirect(url_for('lib_login'))

    user = User.query.filter_by(user_name=username).first()
    if not user:
        flash("Username Is Not Correct")
        return redirect(url_for('lib_login'))
    
    if not check_password_hash(user.pass_hash, password):
        flash("Incorrect Password")
        return redirect(url_for('lib_login'))

    if not user.is_librarian:
        flash("You Are Not A Librarian. If You Are A Student, Login Through Student Login")
        return redirect(url_for('student_login'))
    
    session['user_id'] = user.user_id
    flash('Login Successful')
    return redirect(url_for('lib_dashboard'))


@app.route('/librarian/dashboard')
@lib_check
def lib_dashboard():
    return render_template('lib_dashboard.html')


@app.route('/librarian/profile')
@lib_check
def lib_profile():
    user = User.query.get(session['user_id'])
    # Checking if user_id is present in cookies i.e. whether user has an account or not
    # Checking is done with authentication decorator
    return render_template('lib_profile.html')

@app.route('/logout')
@authentication
def logout():
    user = User.query.get(session['user_id'])
    session.pop('user_id')
    if user.is_librarian:
        return redirect(url_for('lib_login'))
    else:
        return redirect(url_for('student_login'))


@app.route('/librarian/sections')
@lib_check
def lib_sections():
    sections = Section.query.all()
    return render_template('lib_sections.html', sections=sections)


@app.route('/librarian/sections/add')
@lib_check
def add_section():
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%Y-%m-%d")
    return render_template('section/add.html', current_date=formatted_date)

@app.route('/librarian/sections/add', methods=['POST'])
@lib_check
def add_section_post():
    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')

    if not title:
        flash('Please Enter The Title For The Section')
        return redirect(url_for('add_section'))
    
    if len(title) > 10:
        flash('Title Can Contain At-Most 10 Characters')
        return redirect(url_for('add_section'))
    
    if len(description) > 200:
        flash('Description Can Contain At Most 200 Characters')
        return redirect(url_for('add_section'))
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid Date')
        return redirect(url_for('add_section'))
    
    section = Section.query.filter_by(title=title).first()
    if section:
        flash('This Section Already Exists, Choose A Different Name')
        return redirect(url_for('add_section'))
    
    section = Section(title=title, description=description, date_created=date)
    db.session.add(section)
    db.session.commit()

    flash('Section Added Successfully')
    return redirect(url_for('lib_sections'))


@app.route('/librarian/sections/edit/<int:section_id>/')
@lib_check
def edit_section(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    return render_template('section/edit.html', section=section)

@app.route('/librarian/sections/edit/<int:section_id>/', methods=['POST'])
@lib_check
def edit_section_post(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    date = request.form.get('date')

    if not title:
        flash('Please Enter The Title For The Category')
        return redirect(url_for('edit_section', section_id=section_id))
    
    if len(title) > 10:
        flash('Title Can Contain At-Most 10 Characters')
        return redirect(url_for('edit_section', section_id=section_id))
    
    if len(description) > 200:
        flash('Description Can Contain At-Most 200 Characters')
        return redirect(url_for('edit_section', section_id=section_id))
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid Date')
        return redirect(url_for('edit_section', section_id=section_id))
    
    if title != section.title:
        section_title = Section.query.filter_by(title=title).first()
        if section_title:
            flash('This Section Already Exists, Choose A Different Name.')
            return redirect(url_for('edit_section', section_id=section_id))
    
    section.title = title
    section.description = description
    section.date_created = date
    db.session.commit()

    flash('Section Edited Successfully')
    return redirect(url_for('lib_sections'))


@app.route('/librarian/sections/delete/<int:section_id>/')
@lib_check
def delete_section(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    return render_template('section/delete.html', section=section)

@app.route('/librarian/sections/delete/<int:section_id>/', methods=['POST'])
@lib_check
def delete_section_post(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    db.session.delete(section)
    db.session.commit()

    flash('Section Deleted Successfully')
    return redirect(url_for('lib_sections'))


@app.route('/librarian/sections/open/<int:section_id>/')
@lib_check
def open_section(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    books = section.books
    return render_template('lib_books.html', section=section, books=books)


@app.route('/librarian/sections/open/<int:section_id>/add')
@lib_check
def add_book(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    return render_template('book/add.html', section=section)

@app.route('/librarian/sections/open/<int:section_id>/add', methods=['POST'])
@lib_check
def add_book_post(section_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    title = request.form.get('title')
    author = request.form.get('author')
    image = request.form.get('image')
    pages = request.form.get('pages')
    language = request.form.get('language')
    book_pdf = request.files.get('book_pdf')

    if not title:
        flash('Please Enter The Title Of The Book')
        return redirect(url_for('add_book', section_id=section_id))
    
    if not author:
        flash('Please Enter The Authors Of The Book')
        return redirect(url_for('add_book', section_id=section_id))

    if not pages:
        flash('Please Enter The Number Of Pages Of The Book')
        return redirect(url_for('add_book', section_id=section_id))
    
    if not language:
        flash('Please Enter The Language Of The Book')
        return redirect(url_for('add_book', section_id=section_id))
    
    if not book_pdf:
        flash('Please Upload The PDF For The Book')
        return redirect(url_for('add_book', section_id=section_id))
    
    book = Book.query.filter_by(title=title).first()
    if book:
        flash('This Book Already Exists')
        return redirect(url_for('add_book', section_id=section_id))
    
    try:
        pages = int(pages)
    except ValueError:
        flash('Invalid Number Of Pages')
        return redirect(url_for('add_book', section_id=section_id))
    finally:
        if pages < 1:
            flash('Book Should Contain A Minimum Of 1 Page')
            return redirect(url_for('add_book', section_id=section_id))
    
    book_id = len(Book.query.all()) + 1
    final_filename = f"Book_{book_id}.pdf"
    book_pdf.save(os.path.join('book_pdfs', final_filename))
    
    book = Book(title=title, author=author, pages=pages, image=image, language=language, content=final_filename, section=section)
    db.session.add(book)
    db.session.commit()

    flash('Book Added Successfully')
    return redirect(url_for('open_section', section_id=section_id))


@app.route('/librarian/sections/open/<int:section_id>/view/<int:book_id>')
@lib_check
def view_book(section_id, book_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    book = Book.query.get(book_id)
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('open_section', section_id=section_id))

    book_path = "book_pdfs/" + book.content

    book = make_response(open(book_path, 'rb').read())
    book.headers['Content-Type'] = 'application/pdf'
    book.headers['Content-Disposition'] = 'inline; filename=book.pdf'

    return book


@app.route('/librarian/sections/open/<int:section_id>/edit/<int:book_id>')
@lib_check
def edit_book(section_id, book_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    book = Book.query.get(book_id)
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('open_section', section_id=section_id))
    
    return render_template('book/edit.html', section=section, book=book)

@app.route('/librarian/sections/open/<int:section_id>/edit/<int:book_id>', methods=['POST'])
@lib_check
def edit_book_post(section_id, book_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    book = Book.query.get(book_id)
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('open_section', section_id=section_id))
    
    title = request.form.get('title')
    author = request.form.get('author')
    image = request.form.get('image')
    pages = request.form.get('pages')
    language = request.form.get('language')
    book_pdf = request.files.get('book_pdf')

    if not title:
        flash('Please Enter The Title Of The Book')
        return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    
    if not author:
        flash('Please Enter The Authors Of The Book')
        return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))

    if not pages:
        flash('Please Enter The Number Of Pages Of The Book')
        return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    
    if not language:
        flash('Please Enter The Language Of The Book')
        return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    
    if not book_pdf:
        flash('Please Upload The PDF For The Book')
        return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    
    book_title = Book.query.filter_by(title=title).first()
    if title != book.title:
        book_title = Book.query.filter_by(title=title).first()
        if book_title:
            flash('This Book Already Exists')
            return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    
    try:
        pages = int(pages)
    except ValueError:
        flash('Invalid Number Of Pages')
        return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    finally:
        if pages < 1:
            flash('Book Should Contain A Minimum Of 1 Page')
            return redirect(url_for('edit_book', section_id=section_id, book_id=book_id))
    
    book_filename = f"Book_{book_id}.pdf"
    book_pdf.save(os.path.join('book_pdfs', book_filename))
    
    book.title = title
    book.author = author
    book.pages = pages
    book.image = image
    book.language = language
    book.content = book_filename
    db.session.commit()

    flash('Book Edited Successfully')
    return redirect(url_for('open_section', section_id=section_id))


@app.route('/librarian/sections/open/<int:section_id>/delete/<int:book_id>')
@lib_check
def delete_book(section_id, book_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    book = Book.query.get(book_id)
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('open_section', section_id=section_id))
    
    return render_template('book/delete.html', book=book)

@app.route('/librarian/sections/open/<int:section_id>/delete/<int:book_id>', methods=['POST'])
@lib_check
def delete_book_post(section_id, book_id):
    section = Section.query.get(section_id)
    if not section:
        flash('Section Does Not Exist')
        return redirect(url_for('lib_sections'))
    
    book = Book.query.get(book_id)
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('open_section', section_id=section_id))

    db.session.delete(book)
    db.session.commit()

    books_folder = "book_pdfs/"
    book_path = os.path.join(books_folder, book.content)
    if os.path.exists(book_path):
        os.remove(book_path)

    flash('Book Removed Successfully')
    return redirect(url_for('open_section', section_id=section_id))



# ----------------------------STUDENT PORTION----------------------------


@app.route('/student-register')
def register():
    return render_template('student/register.html')

@app.route('/student-register', methods=['POST'])
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
    
    if len(username) > 16:
        flash("Username Can Contain At-Most 16 Characters")
        return redirect(url_for('register'))
    
    if len(name) > 48:
        flash("Name Can Contain At-Most 48 Characters")
        return redirect(url_for('register'))
    
    if len(stream) > 50:
        flash("Stream Can Contain At-Most 50 Characters")
        return redirect(url_for('register'))
    
    user = User.query.filter_by(user_name=username).first()
    if user:
        flash("Username Already exists, Choose Another Username")
        return redirect(url_for('register'))

    password_hash = generate_password_hash(password)
    new_user = User(user_name=username, pass_hash=password_hash, name=name, stream=stream)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('student_login'))


@app.route('/student-login')
def student_login():
    return render_template('student/student_login.html')

@app.route('/student-login', methods=['POST'])
def student_login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please Fill Out The Required Fields")
        return redirect(url_for('student_login'))

    user = User.query.filter_by(user_name=username).first()
    if not user:
        flash("Username Is Not Correct")
        return redirect(url_for('student_login'))
    
    if not check_password_hash(user.pass_hash, password):
        flash("Incorrect Password")
        return redirect(url_for('student_login'))

    if user.is_librarian:
        flash("Please Login Through Librarian Login Page")
        return redirect(url_for('lib_login'))
    
    session['user_id'] = user.user_id
    flash('Login Successful')
    return redirect(url_for('student_dashboard'))

@app.route('/student/dashboard')
@authentication
def student_dashboard():
    return render_template('student/student_dashboard.html')

@app.route('/student/profile')
@authentication
def student_profile():
    return render_template('student/student_profile.html')


@app.route('/student/books')
@authentication
def student_books():
    sections = Section.query.all()
    return render_template('student/student_books.html', sections=sections)

@app.route('/student/books/request/<int:book_id>')
@authentication
def student_request_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        sections = Section.query.all()
        flash('Book Does Not Exist')
        return render_template('student/student_books.html', sections=sections)
    return "Coming soon"