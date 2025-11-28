import logging
import random

from flask import Blueprint, jsonify  # , request

fakenodo_bp = Blueprint("fakenodo_api", __name__)
logger = logging.getLogger(__name__)


@fakenodo_bp.route("/deposit/depositions", methods=["POST"])
def create_deposition():
    """
    Simula la creación de una deposición.
    Devuelve un ID inventado (basado en el tiempo actual).
    """
    # Usamos el random como ID único y falso
    fake_id = random.randint(100000, 999999)

    # Devolvemos la estructura que ZenodoService espera pero pq
    response_data = {"id": fake_id}

    return response_data, 201  # 201 = Created


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>/files", methods=["POST"])
def upload_file(dep_id, data, files):
    """
    Simula la subida de un archivo.
    No guarda el archivo, solo comprueba que venga uno y devuelve éxito.
    """
    if "file" not in files:
        return jsonify({"error": "No se encontró ningún archivo"}), 400

    # Obtenemos el nombre del archivo solo para el log
    filename = files["file"].name

    # Devolvemos una respuesta de éxito genérica
    response_data = {"key": filename}

    return response_data, 201  # 201 = Created


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>/actions/publish", methods=["POST"])
def publish_deposition(dep_id):
    """
    Simula la publicación.
    Inventa un DOI usando el ID de la deposición.
    """
    # Inventamos un DOI que se vea realista
    fake_doi = f"10.9999/fakenodo.{dep_id}.v1"

    # Devolvemos la estructura que ZenodoService espera
    response_data = {"id": dep_id, "doi": fake_doi, "state": "done", "submitted": True}

    # 202 (Accepted) es lo que devuelve Zenodo cuando la publicación es exitosa
    return response_data, 202
