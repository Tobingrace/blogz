import os
import re
from application import app
from application import db
from flask_babel import lazy_gettext
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import datetime
###############################
# End Imports for SQLAlchemy ##
###############################


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:build-a-blog@localhost:3306/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_MIGRATE_REPO'] = os.path.join(basedir, 'db_repository')
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
db = SQLAlchemy(app)
WHOOSH_BASE = os.path.join(basedir, 'search.db')


# database reference and generation classes

############################

import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask_whooshalchemy as whooshalchemy

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.user_id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.user_id'))
)


class User(db.Model, UserMixin):
    __searchable__ = ['username']
    user_id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(40))
    last = db.Column(db.String(40))
    username = db.Column(db.String(40), index=True, unique=True)
    password = db.Column(db.String(250))
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(1000))
    avatar_link = db.Column(db.String(200))
    profile_background = db.Column(db.String(200))
    status = db.Column(db.String(50))
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == user_id),
                               secondaryjoin=(followers.c.followed_id == user_id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')



    @staticmethod
    def make_valid_username(username):
        return re.sub('[^a-zA-Z0-9_\.]', '', username)

    @staticmethod
    def make_unique_username(username):
        if User.query.filter_by(username=username).first() is None:
            return username
        version = 2
        while True:
            new_username = username + str(version)
            if User.query.filter_by(username=new_username).first() is None:
                break
            version += 1
        return new_username

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
            return str(self.user_id)
    
    '''
    def get_id(self):
        return unicode(self.session_token)
    '''

    '''
    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
            (md5(self.email.encode('utf-8')).hexdigest(), size)
    '''

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.user_id).count() > 0

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.user_id).order_by(
                    Post.timestamp.desc())

    def __repr__(self):  # pragma: no cover
        return '<User %r>' % (self.username)

# Enable whooshee to allow indexes and searching on the site
class Post(db.Model):
    __searchable__ = ['title'], ['content']

    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text(50))
    content = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    def __repr__(self):  # pragma: no cover
        return '<Post %r>' % (self.content)

    if enable_search:
        whooshalchemy.whoosh_index(app, Post, User)

if __name__ == "__main__":
    app.run(debug=True)

