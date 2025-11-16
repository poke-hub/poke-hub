from flask import jsonify, render_template, request

from app.modules.explore import explore_bp
from app.modules.explore.services import ExploreService
from app.modules.elasticsearch.services import ElasticsearchService


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        service = ExploreService()
        # Resultados de búsqueda
        query = request.args.get("query", "")
        # Cargar autores y etiquetas para los filtros
        authors = service.get_all_authors()
        tags = service.get_all_tags()

        return render_template("explore/index.html", query=query, authors=authors, tags=tags)

    if request.method == "POST":
        criteria = request.get_json()
        
        # Extraemos los parámetros que el servicio de Elasticsearch sí entiende
        query = criteria.get("query", "")
        sorting = criteria.get("sorting", "created_at")
        desc_str = criteria.get("desc", "true")
        desc = desc_str.lower() == "true"

        es_service = ElasticsearchService()
        es_results = es_service.search(query=query, sorting=sorting, desc=desc)

        # Extraemos los documentos de la respuesta de Elasticsearch
        hits = [hit['_source'] for hit in es_results['hits']['hits']]
        return jsonify(hits)
