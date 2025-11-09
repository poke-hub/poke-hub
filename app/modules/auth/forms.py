from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    surname = StringField("Surname", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("Password", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class TwoFactorLoginForm(FlaskForm):
    """Segundo paso del login (2FA)."""

    token = StringField("Code:", validators=[DataRequired(), Length(min=6, max=10)])
    submit = SubmitField("Verify")
