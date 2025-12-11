import io

import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage

from app.modules.fakenodo.routes import fakenodo_bp, upload_file


@pytest.fixture
def app():
    """
    Crea una instancia de la app Flask para pruebas.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(fakenodo_bp, url_prefix="/api")
    yield app


@pytest.fixture
def client(app):
    """Crea un cliente de pruebas de Flask."""
    return app.test_client()


def test_create_deposition(client):
    """
    Prueba que la creación de una deposición devuelva un 201.
    """
    metadata = {"title": "Mi primer dataset de prueba"}

    response = client.post("/api/deposit/depositions", json={"metadata": metadata})

    assert response.status_code == 201
    data = response.get_json()

    assert "id" in data


def test_upload_file(app):
    """
    Prueba la subida de un archivo.
    """
    dep_id = 987654

    fake_file_content = b"Este es el contenido del poke-file"
    fake_filename = "modelo.poke"

    fake_file_storage = FileStorage(
        stream=io.BytesIO(fake_file_content), filename=fake_filename, name="file", content_type="text/plain"
    )

    files_arg = {"file": fake_file_storage}

    with app.test_request_context():
        response_data, status_code = upload_file(dep_id, data={}, files=files_arg)

    assert status_code == 201
    assert response_data["key"] == "file"


def test_upload_file_no_file_attached(app):
    """
    Prueba la ruta de subida sin adjuntar un archivo (simulando los argumentos).
    """
    dep_id = 987654

    files_arg = {}

    with app.test_request_context():
        response_data, status_code = upload_file(dep_id, data={}, files=files_arg)

    assert status_code == 400
    assert response_data.get_json()["error"] == "No se encontró ningún archivo"


def test_publish_deposition_flow(client):
    """
    Prueba el flujo completo de creación y publicación.
    """
    rv_create = client.post("/api/deposit/depositions", json={"metadata": {"title": "Test"}})
    assert rv_create.status_code == 201
    dep_id = rv_create.get_json()["id"]
    response = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")

    assert response.status_code == 202
    data = response.get_json()
    assert data["id"] == dep_id
    assert "doi" in data
    assert data["doi"] == f"10.9999/fakenodo.{dep_id}.v1"
