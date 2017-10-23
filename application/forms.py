from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, Form
from wtforms.widgets import TextInput
from wtforms.validators import DataRequired, Length, EqualTo
from .models import User


###############################
# Begin Forms #################
###############################
# Creating custom forms for use in the application
class CustomTextInput(TextInput):
    def __init__(self, error_class=u'has_errors'):
        super(CustomTextInput, self).__init__()
        self.error_class = error_class

    def __call__(self, field, **kwargs):
        if field.errors:
            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
            kwargs['class'] = u'%s %s' % (self.error_class, c)
        return super(CustomTextInput, self).__call__(field, **kwargs)


class RegistrationForm(FlaskForm):
    first = StringField('First', [Length(min=4, max=25)], widget=CustomTextInput())
    last = StringField('Last', [Length(min=4, max=25)])
    username = StringField('Username', [Length(min=4, max=25)])
    email = StringField('Email Address', [Length(min=6, max=35)])
    password = PasswordField('Password', 
    [
        DataRequired(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


class LoginForm(FlaskForm):
    username = StringField('Username', [Length(min=4, max=25)])
    password = PasswordField('Password', [DataRequired()])
    remember_me = BooleanField('remember_me')


class PostForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    content = TextAreaField('content', validators=[DataRequired()])


class SearchForm(FlaskForm):
    search = StringField('search', validators=[DataRequired()])


class EditForm(FlaskForm):
    username = StringField('username', validators=[Length(min=10, max=140)])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])
    avatar_link = StringField('Profile Image')
###############################
# End Forms ###################
###############################

