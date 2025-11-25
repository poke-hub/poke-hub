from flask_wtf import FlaskForm
from wtforms import SubmitField


class PokeModelForm(FlaskForm):
    submit = SubmitField("Save pokemodel")
