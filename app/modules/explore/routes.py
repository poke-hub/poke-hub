from flask import jsonify, render_template, request

from app.modules.explore import explore_bp
from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        service = ExploreService()
        # Resultados de búsqueda
        query = request.args.get("query", "")
        form = ExploreForm()
        # Cargar autores y etiquetas para los filtros
        authors = service.get_all_authors()
        tags = service.get_all_tags()

        return render_template("explore/index.html", form=form, query=query, authors=authors, tags=tags)

    if request.method == "POST":
        criteria = request.get_json()
        datasets = ExploreService().filter(**criteria)
        return jsonify([dataset.to_dict() for dataset in datasets])
