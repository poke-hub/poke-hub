from flask import render_template

from app.modules.pokemodel import poke_model_bp


@poke_model_bp.route("/poke_model", methods=["GET"])
def index():
    return render_template("poke_model/index.html")
