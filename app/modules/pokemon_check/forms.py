from flask_wtf import FlaskForm
from wtforms import SubmitField


class PokemonCheckForm(FlaskForm):
    submit = SubmitField("Save pokemon_check")
