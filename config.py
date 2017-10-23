

# -*- coding: utf8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'temporary'
DEBUG = True
SQLALCHEMY_ECHO = False


if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://build-a-blog:build-a-blog@localhost:3306/build-a-blog')
else:
    SQLALCHEMY_DATABASE_URI = os.environ['mysql+pymysql://build-a-blog:build-a-blog@localhost:3306/build-a-blog']

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_RECORD_QUERIES = True
WHOOSH_BASE= os.path.join(basedir, 'search.db')
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = True

# Whoosh does not work on Heroku
WHOOSH_ENABLED = os.environ.get('HEROKU') is None

# slow database query threshold (in seconds)
DATABASE_QUERY_TIMEOUT = 0.5

# administrator list
ADMINS = ['my@email.com']

# pagination
POSTS_PER_PAGE = 10
MAX_SEARCH_RESULTS = 50
