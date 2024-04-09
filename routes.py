from flask import render_template, request, redirect, url_for, flash, session, make_response, send_file
from app import app
from models import db, User, Section, Book, Requests_Active, Issues_Active, Requests_Rejected, Issues_Expired
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import os


def authentication(func):
    @wraps(func)
    def check(*args, **kwargs):
        if not session or 'user_id' not in session:
            flash("Please Login To Continue")
            return redirect(url_for('student_login'))
        
        user = User.query.get(session['user_id'])

        if user.is_librarian:
            flash("Librarian Cannot Access Student Pages")
            return redirect(url_for('lib_dashboard'))
        return func(*args, **kwargs)
    return check

def lib_check(func):
    @wraps(func)
    def check(*args, **kwargs):
        if not session or 'user_id' not in session:
            flash("Please Login To Continue")
            return redirect(url_for('lib_login'))
        
        user = User.query.get(session['user_id'])

        if not user.is_librarian:
            flash("You Are Not Authorized To Access This Page")
            return redirect(url_for('student_dashboard'))
        return func(*args, **kwargs)
    return check


@app.route('/')
def index():
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
    sections_count = db.session.query(Section).count()
    books_count = db.session.query(Book).count()
    requests_count = db.session.query(Requests_Active).count()
    curr_issues_count = db.session.query(Issues_Active).count()
    exp_issues_count = db.session.query(Issues_Expired).count()
    all_issues_count = curr_issues_count + exp_issues_count

    users = User.query.all()
    all_users = list()
    user_issues = list()
    for user in users:
        if not user.is_librarian:
            all_users.append(user.user_name)
            user_issues.append(user.books_issued)

    sections = Section.query.all()
    section_names = list()
    section_books = list()
    for section in sections:
        section_names.append(section.title)
        num_books = len(section.books)
        section_books.append(num_books)

    return render_template('lib_dashboard.html', sections_count=sections_count, books_count=books_count, requests_count=requests_count, curr_issues_count=curr_issues_count, all_issues_count=all_issues_count, all_users=all_users, user_issues=user_issues, section_names=section_names, section_books=section_books)


@app.route('/librarian/profile')
@lib_check
def lib_profile():
    user = User.query.get(session['user_id'])
    # Checking if user_id is present in cookies i.e. whether user has an account or not
    # Checking is done with authentication decorator
    return render_template('lib_profile.html', user=user)

@app.route('/librarian/profile/edit')
@lib_check
def lib_profile_edit():
    user = User.query.get(session['user_id'])
    return render_template('lib_profile_edit.html', user=user)

@app.route('/librarian/profile/edit', methods=['POST'])
@lib_check
def lib_profile_edit_post():
    user = User.query.get(session['user_id'])

    username = request.form.get('username')
    curr_password = request.form.get('curr_password')
    new_password = request.form.get('new_password')

    if not username or not curr_password:
        flash("Username And Current Password Cannot Be Empty")
        return redirect(url_for('lib_profile_edit'))
    
    if username != user.user_name:
        user_check = User.query.filter_by(user_name=username).first()
        if user_check:
            flash("User Already Exists, Choose Another Username")
            return redirect(url_for('lib_profile_edit'))
        
    if len(username) > 16:
        flash("Username Can Contain At-Most 16 Characters")
        return redirect(url_for('lib_profile_edit'))
        
    if not check_password_hash(user.pass_hash, curr_password):
        flash("Incorrect Current Password")
        return redirect(url_for('lib_profile_edit'))

    if new_password:
        password_hash = generate_password_hash(new_password)
        user.pass_hash=password_hash

    user.user_name=username
    db.session.commit()

    flash('Profile Edited Successfully')
    return redirect(url_for('lib_profile'))

@app.route('/logout')
def logout():
    if session:
        user = User.query.get(session['user_id'])
        session.pop('user_id')
        if user.is_librarian:
            return redirect(url_for('lib_login'))
        else:
            return redirect(url_for('student_login'))
    else:
        return redirect(url_for('index'))

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

    for book in section.books:
        books_folder = "book_pdfs/"
        book_path = os.path.join(books_folder, book.content)
        if os.path.exists(book_path):
            os.remove(book_path)

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
    final_filename = f"Book_{book_id}_{title}.pdf"
    if not os.path.exists('book_pdfs'):
        os.makedirs('book_pdfs')
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
    
    book_filename = f"Book_{book_id}_{title}.pdf"
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


@app.route('/librarian/active-requests')
@lib_check
def active_requests():
    all_entries = Requests_Active.query.all()
    entries = list()
    for entry in all_entries:
        book = Book.query.filter_by(book_id=entry.book_id).first()
        user = User.query.filter_by(user_id=entry.user_id).first()
        entries.append((book.title, user.user_name))
    return render_template('lib_active_requests.html', entries=entries)

@app.route('/librarian/view/student-profile/<string:username>')
@lib_check
def view_student_profile(username):
    user = User.query.filter_by(user_name=username).first()
    if not user:
        flash("Student Does Not Exist")
        return redirect(url_for('active_requests'))
    
    return render_template('lib_view_student.html', user=user)

@app.route('/librarian/view/book/<string:title>')
@lib_check
def view_book_details(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('active_requests'))
    
    return render_template('lib_view_book.html', book=book)

@app.route('/librarian/grant-book/<string:username>/<string:title>')
@lib_check
def grant_book(username, title):
    user = User.query.filter_by(user_name=username).first()
    book = Book.query.filter_by(title=title).first()
    curr_date = datetime.now().date()
    # formatted_curr_date = curr_date.strftime("%Y-%m-%d")
    return_date = curr_date + timedelta(days=0)
    # formatted_return_date = return_date.strftime("%Y-%m-%d")
    issue = Issues_Active(user_id=user.user_id, book_id=book.book_id, issue_date=curr_date, end_date=return_date)

    user.books_issued = user.books_issued + 1
    book.issue_num = book.issue_num + 1
    db.session.add(issue)
    # db.session.commit()

    entry = Requests_Active.query.filter_by(user_id=user.user_id, book_id=book.book_id).first()
    db.session.delete(entry)
    db.session.commit()

    flash('Book Granted Successfully')
    return redirect(url_for('active_requests'))

@app.route('/librarian/reject-request/<string:username>/<string:title>')
@lib_check
def reject_request(username, title):
    user = User.query.filter_by(user_name=username).first()
    book = Book.query.filter_by(title=title).first()
    curr_date = datetime.now().date()
    # formatted_curr_date = curr_date.strftime("%Y-%m-%d")
    request = Requests_Rejected(user_id=user.user_id, book_id=book.book_id, date_rejected=curr_date)
    db.session.add(request)
    # db.session.commit()

    entry = Requests_Active.query.filter_by(user_id=user.user_id, book_id=book.book_id).first()
    db.session.delete(entry)
    db.session.commit()

    flash('Book Request Rejected')
    return redirect(url_for('active_requests'))


@app.route('/librarian/active-issues')
@lib_check
def active_issues():
    all_issues = Issues_Active.query.all()
    issues = list()
    for issue in all_issues:
        book = Book.query.filter_by(book_id=issue.book_id).first()
        user = User.query.filter_by(user_id=issue.user_id).first()
        issues.append((book.title, user.user_name, issue.issue_date, issue.end_date))

    return render_template('lib_active_issues.html', issues=issues)

@app.route('/librarian/revoke-book/<string:username>/<string:title>')
@lib_check
def revoke_book(username, title):
    user = User.query.filter_by(user_name=username).first()
    book = Book.query.filter_by(title=title).first()
    
    issue_details = Issues_Active.query.filter_by(user_id=user.user_id, book_id=book.book_id).first()
    curr_date = datetime.now().date()

    expired = Issues_Expired(user_id=user.user_id, book_id=book.book_id, issue_date=issue_details.issue_date, returned_date=curr_date, cause='Librarian')
    db.session.add(expired)
    db.session.delete(issue_details)
    db.session.commit()

    flash('Book Revoked Successfully')
    return redirect(url_for('active_issues'))





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
    user = User.query.get(session['user_id'])
    sections_count = db.session.query(Section).count()
    books_count = db.session.query(Book).count()
    requests_count = db.session.query(Requests_Active).filter_by(user_id=user.user_id).count()
    curr_issues_count = db.session.query(Issues_Active).filter_by(user_id=user.user_id).count()
    exp_issues_count = db.session.query(Issues_Expired).filter_by(user_id=user.user_id).count()

    sections = Section.query.all()
    section_issues = dict()
    for section in sections:
        count = 0
        curr_issues = Issues_Active.query.filter_by(user_id=user.user_id).all()
        for curr_issue in curr_issues:
            for book in section.books:
                if curr_issue.book_id==book.book_id:
                    count += 1

        exp_issues = Issues_Expired.query.filter_by(user_id=user.user_id).all()
        for exp_issue in exp_issues:
            for book in section.books:
                if exp_issue.book_id==book.book_id:
                    count += 1

        section_issues[section.title] = count
        
    sections = Section.query.all()
    section_names = list()
    section_books = list()
    for section in sections:
        section_names.append(section.title)
        num_books = len(section.books)
        section_books.append(num_books)

    books_downloaded = user.books_downloaded

    return render_template('student/student_dashboard.html', sections_count=sections_count, books_count=books_count, requests_count=requests_count, curr_issues_count=curr_issues_count, exp_issues_count=exp_issues_count, section_titles=list(section_issues.keys()), count_issues=list(section_issues.values()), section_names=section_names, section_books=section_books, books_downloaded=books_downloaded)


@app.route('/student/profile')
@authentication
def student_profile():
    user = User.query.get(session['user_id'])
    return render_template('student/student_profile.html', user=user)

@app.route('/student/profile/edit')
@authentication
def student_profile_edit():
    user = User.query.get(session['user_id'])
    return render_template('student/student_profile_edit.html', user=user)

@app.route('/student/profile/edit', methods=['POST'])
@authentication
def student_profile_edit_post():
    user = User.query.get(session['user_id'])

    username = request.form.get('username')
    curr_password = request.form.get('curr_password')
    new_password = request.form.get('new_password')
    name = request.form.get('name')
    stream = request.form.get('stream')

    if not username or not curr_password or not name:
        flash("Username, Current Password And Name Cannot Be Empty")
        return redirect(url_for('student_profile_edit'))
    
    if username != user.user_name:
        user_check = User.query.filter_by(user_name=username).first()
        if user_check:
            flash("User Already Exists, Choose Another Username")
            return redirect(url_for('student_profile_edit'))
        
    if len(username) > 16:
        flash("Username Can Contain At-Most 16 Characters")
        return redirect(url_for('student_profile_edit'))
        
    if not check_password_hash(user.pass_hash, curr_password):
        flash("Incorrect Current Password")
        return redirect(url_for('student_profile_edit'))

    if new_password:
        password_hash = generate_password_hash(new_password)
        user.pass_hash=password_hash

    user.user_name = username
    user.name = name
    user.stream = stream
    db.session.commit()

    flash('Profile Edited Successfully')
    return redirect(url_for('student_profile'))


@app.route('/student/books')
@authentication
def student_books():
    sections = Section.query.all()
    user = User.query.get(session['user_id'])
    user_books = Requests_Active.query.filter_by(user_id=user.user_id).all()
    books = list()
    for user_book in user_books:
        books.append(user_book.book_id)

    issues = Issues_Active.query.filter_by(user_id=user.user_id).all()
    books_issued = list()
    for issue in issues:
        books_issued.append(issue.book_id)

    filter_section = request.args.get('section') or ""
    filter_book = request.args.get('book') or ""
    filter_author = request.args.get('author') or ""
    filter_language = request.args.get('language') or ""
    filter_pages = request.args.get('pages') or ""
    filter_issues = request.args.get('issues') or ""

    if filter_section:
        sections = Section.query.filter(Section.title.ilike(f'%{filter_section}%')).all()

    if filter_pages:
        try:
            filter_pages = int(filter_pages)
        except ValueError:
            flash('Enter Valid Number Of Pages')
            return redirect(url_for('student_books'))
        if filter_pages <= 0:
            flash('Enter Valid Number Of Pages')
            return redirect(url_for('student_books'))
    
    if filter_issues:
        try:
            filter_issues = int(filter_issues)
        except ValueError:
            flash('Enter Valid Number Of Issues')
            return redirect(url_for('student_books'))
        if filter_issues < 0:
            flash('Enter Valid Number Of Issues')
            return redirect(url_for('student_books'))

    return render_template('student/student_books.html', sections=sections, books=books, books_issued=books_issued, filter_section=filter_section, filter_book=filter_book, filter_author=filter_author, filter_language=filter_language, filter_pages=filter_pages, filter_issues=filter_issues)

@app.route('/student/books/request/<int:book_id>')
@authentication
def student_request_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('student_books'))
    user = User.query.get(session['user_id'])
    requested_books = Requests_Active.query.filter_by(user_id=user.user_id).all()
    check = False
    for requested_book in requested_books:
        if requested_book.book_id == book_id:
            check = True
            break
    issued_books = Issues_Active.query.filter_by(user_id=user.user_id).all()
    count = len(requested_books) + len(issued_books)
    return render_template('student/student_request_book.html', book=book, count=count, check=check)

@app.route('/student/my-requests')
@authentication
def my_requests():
    user = User.query.get(session['user_id'])
    entries = Requests_Active.query.filter_by(user_id=user.user_id).all()
    books = list()
    book_ids = list()
    for entry in entries:
        book = Book.query.filter_by(book_id=entry.book_id).first()
        books.append(book.title)
        book_ids.append(book.book_id)

    requests = Requests_Rejected.query.filter_by(user_id=user.user_id).order_by(Requests_Rejected.rr_id.desc()).limit(5).all()
    rejects = list()
    for request in requests:
        book = Book.query.filter_by(book_id=request.book_id).first()
        details = (book.title, request.date_rejected)
        rejects.append(details)

    return render_template('student/my_requests.html', books=books, rejects=rejects, book_ids=book_ids)

@app.route('/student/my-requests/add/<int:book_id>', methods=['POST'])
@authentication
def my_requests_post(book_id):
    user = User.query.get(session['user_id'])
    book = Book.query.filter_by(book_id=book_id).first()

    new_entry = Requests_Active(user_id=user.user_id, book_id=book.book_id)
    db.session.add(new_entry)
    db.session.commit()

    flash('Book Requested Successfully')
    return redirect(url_for('my_requests'))

@app.route('/student/cancel-request/<string:title>')
@authentication
def cancel_request(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('student_books'))
    return render_template('student/cancel_request.html', title=title)

@app.route('/student/cancel-request/<string:title>', methods=['POST'])
@authentication
def cancel_request_post(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash('Book Does Not Exist')
        return redirect(url_for('student_books'))
    entry = Requests_Active.query.filter_by(book_id=book.book_id).first()
    db.session.delete(entry)
    db.session.commit()

    flash('Book Request Cancelled Successfully')
    return redirect(url_for('my_requests'))

@app.route('/student/my-books')
@authentication
def my_books():
    user = User.query.get(session['user_id'])
    issues = Issues_Active.query.filter_by(user_id=user.user_id).all()
    books = list()
    for issue in issues:
        book = Book.query.filter_by(book_id=issue.book_id).first()
        books.append((book.title, issue.issue_date, issue.end_date))

    returns = Issues_Expired.query.filter_by(user_id=user.user_id).order_by(Issues_Expired.ie_id.desc()).limit(5).all()
    expires = list()
    for return_iter in returns:
        book = Book.query.filter_by(book_id=return_iter.book_id).first()
        if return_iter.cause == "Librarian":
            cause = "Revoked by Librarian"
        elif return_iter.cause == "Student":
            cause = "Returned by You"
        elif return_iter.cause == "Automatically":
            cause = "Issue period over"
        expires.append((book.title, return_iter.issue_date, return_iter.returned_date, cause))

    return render_template('student/my_books.html', books=books, expires=expires)

@app.route('/student/read/<string:title>')
@authentication
def read_book(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('my_books'))
    book_path = "book_pdfs/" + book.content

    book = make_response(open(book_path, 'rb').read())
    book.headers['Content-Type'] = 'application/pdf'
    book.headers['Content-Disposition'] = 'inline; filename=book.pdf'

    return book

@app.route('/student/return-book/confirm/<string:title>')
@authentication
def return_book_confirm(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('my_books'))
    return render_template('student/return_book_confirm.html', title=title)

@app.route('/student/return-book/<string:title>')
@authentication
def return_book(title):
    user = User.query.get(session['user_id'])
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('my_books'))

    issue_details = Issues_Active.query.filter_by(user_id=user.user_id, book_id=book.book_id).first()
    curr_date = datetime.now().date()

    expired = Issues_Expired(user_id=user.user_id, book_id=book.book_id, issue_date=issue_details.issue_date, returned_date=curr_date, cause='Student')
    db.session.add(expired)
    db.session.delete(issue_details)
    db.session.commit()

    flash('Book Returned Successfully')
    return redirect(url_for('my_books'))

@app.route('/student/book/download/<string:title>')
@authentication
def download_book(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('my_books'))
    
    pdf_path = f"book_pdfs/{book.content}"
    filename = f"{book.title}.pdf"

    user = User.query.get(session['user_id'])
    user.books_downloaded = user.books_downloaded + 1
    db.session.commit()

    flash("Book Downloaded Successfully")
    return send_file(pdf_path, as_attachment=True, download_name=filename)

@app.route('/student/book/download/payment/<string:title>')
@authentication
def confirm_payment(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('my_books'))

    return render_template('student/confirm_payment.html', book=book)

@app.route('/student/book/download/payment/<string:title>', methods=['POST'])
@authentication
def confirm_payment_post(title):
    user = User.query.get(session['user_id'])
    book = Book.query.filter_by(title=title).first()
    if not book:
        flash("Book Does Not Exist")
        return redirect(url_for('my_books'))

    password = request.form.get('password')

    if not check_password_hash(user.pass_hash, password):
        flash("Incorrect Password")
        return redirect(url_for('confirm_payment', title=title))
    
    return redirect(url_for('download_book', title=title))


def check_issue_expiration():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and not user.is_librarian:
            issue_details = Issues_Active.query.filter_by(user_id=user.user_id).all()
            curr_date = datetime.now().date()

            for issue_detail in issue_details:
                if curr_date > issue_detail.end_date:
                    expired = Issues_Expired(user_id=user.user_id, book_id=issue_detail.book_id, issue_date=issue_detail.issue_date, returned_date=curr_date, cause='Automatically')
                    db.session.add(expired)
                    db.session.delete(issue_detail)
                    db.session.commit()

@authentication
@app.before_request
def run_check_issue_expiration():
    check_issue_expiration()