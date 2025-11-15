import io

import pytest
from flask import Flask

# Asegúrate de que la importación de tu blueprint sea correcta
from app.modules.fakenodo.routes import fakenodo_bp


@pytest.fixture
def app():
    """
    Crea una instancia de la app Flask para pruebas.
    Ya NO necesita tmp_path ni monkeypatch porque fakenodo es sin estado.
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
    """Prueba que la creación de una deposición devuelva un 201."""
    metadata = {"title": "Mi primer dataset de prueba"}

    response = client.post("/api/deposit/depositions", json={"metadata": metadata})

    assert response.status_code == 201
    data = response.get_json()

    assert "id" in data
    assert data["metadata"]["title"] == "Mi primer dataset de prueba"
    assert data["published"] is False


def test_upload_file(client):
    """
    Prueba la subida de un archivo.
    Ahora solo comprueba el 201, ya no verifica el disco.
    """
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]

    fake_file_content = b"Este es el contenido del poke-file"
    fake_file = (io.BytesIO(fake_file_content), "modelo.poke")

    response = client.post(
        f"/api/deposit/depositions/{dep_id}/files", data={"file": fake_file}, content_type="multipart/form-data"
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["key"] == "modelo.poke"


def test_upload_file_no_file_attached(client):
    """Prueba la ruta de subida sin adjuntar un archivo (esto sigue funcionando)."""
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]

    response = client.post(f"/api/deposit/depositions/{dep_id}/files", data={}, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json()["error"] == "No se encontró ningún archivo"


def test_publish_deposition_flow(client):
    """
    Prueba el flujo completo de creación, subida y publicación.
    Ahora solo comprueba la respuesta final.
    """
    rv_create = client.post("/api/deposit/depositions", json={"metadata": {"title": "Test"}})
    assert rv_create.status_code == 201
    dep_id = rv_create.get_json()["id"]

    rv_upload = client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={"file": (io.BytesIO(b"content"), "file.txt")},
        content_type="multipart/form-data",
    )
    assert rv_upload.status_code == 201

    response = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")

    assert response.status_code == 202
    data = response.get_json()
    assert data["id"] == dep_id
    assert "doi" in data
    assert data["doi"] == f"10.9999/fakenodo.{dep_id}.v1"
