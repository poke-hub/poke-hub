import io
import json
import os
from pathlib import Path

import pytest
from flask import Flask

from app.modules.fakenodo.routes import fakenodo_bp

@pytest.fixture
def app(tmp_path, monkeypatch):
    """
    Crea una instancia de la app Flask para pruebas y parchea
    DB_PATH y STORAGE para usar un directorio temporal (tmp_path).
    Esto asegura que cada prueba esté aislada y no deje basura.
    """
    app = Flask(__name__)
    app.config['TESTING'] = True

    storage_dir = tmp_path / "fakenodo_storage"
    storage_dir.mkdir()
    db_file = tmp_path / "fakenodo_db.json"

    import sys
    target_module = sys.modules[fakenodo_bp.import_name]

    monkeypatch.setattr(target_module, 'DB_PATH', str(db_file))
    monkeypatch.setattr(target_module, 'STORAGE', str(storage_dir))
    
    app.extensions['fakenodo_storage_path'] = str(storage_dir)

    os.makedirs(storage_dir, exist_ok=True)

    app.register_blueprint(fakenodo_bp, url_prefix='/api')

    yield app
    

@pytest.fixture
def client(app):
    """Crea un cliente de pruebas de Flask."""
    return app.test_client()


def test_create_deposition(client):
    """Prueba la creación de una nueva deposición."""
    metadata = {"title": "Mi primer dataset de prueba"}
    
    response = client.post("/api/deposit/depositions", json={"metadata": metadata})
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["metadata"]["title"] == "Mi primer dataset de prueba"
    assert data["published"] is False
    assert data["files"] == []
    assert data["version"] == 1

def test_list_depositions(client):
    """Prueba que se listen las deposiciones creadas."""
    client.post("/api/deposit/depositions", json={"metadata": {"title": "Dep 1"}})
    client.post("/api/deposit/depositions", json={"metadata": {"title": "Dep 2"}})
    
    response = client.get("/api/deposit/depositions")
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[0]["metadata"]["title"] == "Dep 1"

def test_get_deposition(client):
    """Prueba que se pueda obtener una deposición específica."""
    rv = client.post("/api/deposit/depositions", json={"metadata": {"title": "Dep 1"}})
    dep_id = rv.get_json()["id"]
    
    response = client.get(f"/api/deposit/depositions/{dep_id}")
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == dep_id
    assert data["metadata"]["title"] == "Dep 1"

def test_get_deposition_not_found(client):
    """Prueba el error 404 si la deposición no existe."""
    response = client.get("/api/deposit/depositions/999")
    assert response.status_code == 404

def test_upload_file(client, app):
    """Prueba la subida de un archivo a una deposición."""
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]
    
    fake_file_content = b"Este es el contenido del poke-file"
    fake_file = (io.BytesIO(fake_file_content), "modelo.poke")
    
    response = client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={"file": fake_file},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "modelo.poke"
    assert data["size"] == len(fake_file_content)

    rv_dep = client.get(f"/api/deposit/depositions/{dep_id}")
    dep_data = rv_dep.get_json()
    assert len(dep_data["files"]) == 1
    assert dep_data["files"][0]["name"] == "modelo.poke"

    storage_path = Path(app.extensions['fakenodo_storage_path']) 
    expected_file = storage_path / str(dep_id) / "modelo.poke"
    assert expected_file.exists()
    assert expected_file.read_bytes() == fake_file_content

def test_upload_file_dep_not_found(client):
    """Prueba subir un archivo a una deposición inexistente."""
    fake_file = (io.BytesIO(b"content"), "test.txt")
    response = client.post(
        "/api/deposit/depositions/999/files",
        data={"file": fake_file},
        content_type='multipart/form-data'
    )
    assert response.status_code == 404

def test_upload_file_no_file_attached(client):
    """Prueba la ruta de subida sin adjuntar un archivo."""
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]
    
    response = client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={}, 
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "No file"

def test_publish_deposition_new(client):
    """Prueba la publicación de una nueva deposición."""
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]
    client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={"file": (io.BytesIO(b"content"), "file.txt")},
        content_type='multipart/form-data'
    )
    
    response = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    
    assert response.status_code == 202
    data = response.get_json()
    assert data["id"] == dep_id
    assert data["version"] == 1
    assert data["doi"] == f"10.9999/fakenodo.{dep_id}.v1"
    
    rv_dep = client.get(f"/api/deposit/depositions/{dep_id}")
    dep_data = rv_dep.get_json()
    assert dep_data["published"] is True
    assert dep_data["version"] == 1
    assert dep_data["last_published_files_checksum"] is not None

def test_publish_deposition_no_changes(client):
    """Prueba que republicar sin cambios no crea una versión nueva."""
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]
    client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={"file": (io.BytesIO(b"content"), "file.txt")},
        content_type='multipart/form-data'
    )
    client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    
    response = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    
    assert response.status_code == 200 
    data = response.get_json()
    assert data["version"] == 1

def test_publish_deposition_new_version(client):
    """Prueba que publicar con nuevos archivos crea una v2."""
    rv = client.post("/api/deposit/depositions", json={})
    dep_id = rv.get_json()["id"]
    client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={"file": (io.BytesIO(b"content v1"), "file.txt")},
        content_type='multipart/form-data'
    )
    client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    
    client.post(
        f"/api/deposit/depositions/{dep_id}/files",
        data={"file": (io.BytesIO(b"content v2"), "file2.txt")},
        content_type='multipart/form-data'
    )
    response = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    
    assert response.status_code == 202
    data = response.get_json()
    assert data["version"] == 2 
    assert data["doi"] == f"10.9999/fakenodo.{dep_id}.v2"
    
    rv_dep = client.get(f"/api/deposit/depositions/{dep_id}")
    dep_data = rv_dep.get_json()
    assert dep_data["version"] == 2