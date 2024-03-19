from app import app

from dotenv import load_dotenv
import os

load_dotenv()  #It only loads the content of .env file in os environment and not in the app
#Below three lines of code load the content of .env file from os environment to the app config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')