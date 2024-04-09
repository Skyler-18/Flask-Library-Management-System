from app import app
from models import Section, Book
from flask_restful import Resource, Api

api = Api(app)

class SectionResource(Resource):
    def get(self):
        sections = Section.query.all()
        res = {'sections': {}}
        for section in sections:
            res['sections'][section.section_id] = [section.title, len(section.books)]

        return res
    
class BookResource(Resource):
    def get(self):
        books = Book.query.all()
        res = {'books': {}}
        for book in books:
            res['books'][book.book_id] = [book.title, book.author, book.language, book.pages]

        return res
    
api.add_resource(SectionResource, '/api/sections')
api.add_resource(BookResource, '/api/books')