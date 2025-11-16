import logging
import time

from flask import Blueprint, jsonify, request

fakenodo_bp = Blueprint("fakenodo_api", __name__)
logger = logging.getLogger(__name__)


@fakenodo_bp.route("/deposit/depositions", methods=["POST"])
def create_deposition():
    """
    Simula la creación de una deposición.
    Devuelve un ID inventado (basado en el tiempo actual).
    """
    # Usamos el timestamp como ID único y falso
    fake_id = int(time.time())

    # Obtenemos los metadatos solo para simular que los usamos

    logger.info(f"[FAKENODO] Creando deposición falsa. Título: -> ID: {fake_id}")

    # Devolvemos la estructura que ZenodoService espera pero pq
    response_data = {
        "id": fake_id
    }

    return jsonify(response_data), 201  # 201 = Created


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>/files", methods=["POST"])
def upload_file(dep_id):
    """
    Simula la subida de un archivo.
    No guarda el archivo, solo comprueba que venga uno y devuelve éxito.
    """
    if "file" not in request.files:
        logger.error(f"[FAKENODO] Intento de subida a {dep_id} sin archivo.")
        return jsonify({"error": "No se encontró ningún archivo"}), 400

    # Obtenemos el nombre del archivo solo para el log
    filename = request.files["file"].filename
    logger.info(f"[FAKENODO] Recibido (e ignorado) archivo '{filename}' para deposición {dep_id}")

    # Devolvemos una respuesta de éxito genérica
    response_data = {
        "key": filename
    }

    return jsonify(response_data), 201  # 201 = Created


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>/actions/publish", methods=["POST"])
def publish_deposition(dep_id):
    """
    Simula la publicación.
    Inventa un DOI usando el ID de la deposición.
    """
    # Inventamos un DOI que se vea realista
    fake_doi = f"10.9999/fakenodo.{dep_id}.v1"

    logger.info(f"[FAKENODO] Publicando deposición {dep_id}. Asignando DOI: {fake_doi}")

    # Devolvemos la estructura que ZenodoService espera
    response_data = {"id": dep_id, "doi": fake_doi, "state": "done", "submitted": True}

    # 202 (Accepted) es lo que devuelve Zenodo cuando la publicación es exitosa
    return jsonify(response_data), 202
