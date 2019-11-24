from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError               #InputRequired -> for preventing user from submitting form with empty field. Length -> for validating the length of password entered. EqualTo -> for comparing lengths of two different fields.
from passlib.hash import pbkdf2_sha256
import psycopg2

from models import User

def invalid_credentials(form, field):
    """username and password checker"""
    username_entered = form.username.data
    password_entered = field.data

    #Check username is valid

    #After hours of debugging, and scouring the internet for fixes, I finally realize that a simple try except will solve it.(BUT I DOUBT IT DOES IT EFFICIENTLY.)
    #CAN IMAGINE THE OVERHEAD IT ADDS TO THE ALREADY SLOW PROCESS.
    #The following try except block solves the 'sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) SSL SYSCALL error: EOF detected' error. 

    while True:
        try:
            user_object1 = User.query.filter_by(username=username_entered).first()
            break
        except psycopg2.OperationalError:
            pass

    if user_object1 is None:
        raise ValidationError("Username or password is incorrect!")
    elif not pbkdf2_sha256.verify(password_entered, user_object1.hashed_pswd):
        raise ValidationError("Username or password is incorrect!")



class RegistrationForm(FlaskForm): 
    
    """Registration Form"""
    username = StringField('username_label', validators=[InputRequired(message="Username Required"), Length(min=4, max=25, message="Username must be between 4 and 25 characters.")])                                #the parameter is the label of the HTML element to be rendered.
    password = PasswordField('password_label', validators=[InputRequired(message="Password Required"), Length(min=4, max=25, message="Password must be between 4 and 25 characters.")])
    confirm_password = PasswordField('confirm_password_label', validators=[InputRequired(message="Username Required"), EqualTo('password', message="Passwords must match")])
    submit_button = SubmitField("Sign Up")

    def validate_username(self, username):                                      #compulsorily to be named thus. will automatically validate. There is no such restriction for a validation function defined outside the class.
        while True:
            try:
                user_object2 = User.query.filter_by(username=username.data).first()
                break
            except psycopg2.OperationalError:
                pass

        if user_object2:
            raise ValidationError("Username already exists. Select a different username.")


class LoginForm(FlaskForm):

    """Login Form"""
    username = StringField('username_label', validators=[InputRequired(message="Username required.")])
    password = PasswordField('password_label', validators=[InputRequired(message="Password required."), invalid_credentials])
    submit_button = SubmitField("Login")


