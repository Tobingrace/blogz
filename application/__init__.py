'''Importing needed modules'''
###################################################################
### Imports for Initialization and configuration ##################
###################################################################
import os
from flask import (
    Flask, render_template, request, flash, redirect, url_for,
    session, logging, g, jsonify)
from flask_babel import Babel, lazy_gettext
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from .momentjs import momentjs
from flask_openid import OpenID
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
###################################################################
### Imports for Searching Posts ###################################
###################################################################
from whoosh.filedb.filestore import FileStorage
from whoosh.fields import Schema, TEXT, ID
from config import WHOOSH_BASE
###################################################################
### Imports for Google  ###########################################
###################################################################
import urllib
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from flask_oauthlib.client import OAuth
###################################################################
### Imports End ###################################################
###################################################################


# Initialize app, create an instance of app.
# Then specifying variable configurations available
app = Flask(__name__.split('.')[0], instance_relative_config=True)

# Load the default configuration from config.py
app.config.from_object('config')

# Configuring indexing and text file for searching
search_is_new = False
if not os.path.exists(WHOOSH_BASE):
    os.mkdir(WHOOSH_BASE)
    search_is_new = True
search_storage = FileStorage(WHOOSH_BASE)
search_ix = None
if search_is_new:
    schema = Schema(id=ID(stored=True), content=TEXT(), title=TEXT())
    search_ix = search_storage.create_index(schema)
else:
    search_ix = search_storage.open_index()

# Configuring use of momentjs for datetime.utc() 
app.jinja_env.globals['momentjs'] = momentjs

# Configure route for static files
app.static_folder = 'static'

# Configure Path for Basedir
basedir = os.path.abspath(os.path.dirname(__file__))

'''
# Check to see if it already has the URL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:build-a-blog@localhost:3306/build-a-blog'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# Configure SQLAlchemy for debugging
app.config['SQLALCHEMY_ECHO'] = True
'''
# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Bcrypt
flask_bycrypt = Bcrypt(app)
BYCRYPT_LOG_ROUNDS = 15

# Initialize LoginManger
login_manager = LoginManager()
login_manager.init_app(app)

# Configure LoginManager and OpenID
login_manager.login_view = 'login'
login_manager.login_message = lazy_gettext('Please log in to access this page.')
babel = Babel(app)

# Initialize Cache
# cache = Cache(app)

class CustomJSONEncoder(JSONEncoder):
    """This class adds support for lazy translation texts to Flask's
    JSON encoder. This is necessary when flashing translated texts."""
    def default(self, obj):
        from speaklater import is_lazy_string
        if is_lazy_string(obj):
            try:
                return unicode(obj)  # python 2
            except NameError:
                return str(obj)  # python 3
        return super(CustomJSONEncoder, self).default(obj)

app.json_encoder = CustomJSONEncoder


# google OAuth
oauth = OAuth(app)

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)
###############################
# End configuration ###########
###############################


from application import views, models, forms


if __name__ == "__main__":
    app.run()
