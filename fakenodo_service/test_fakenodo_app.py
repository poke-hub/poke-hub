import pytest
import os
import json
from app import app as fakenodo_app  # Importa tu app

# 'Fixture' de Pytest: configura un cliente de prueba para tu app
@pytest.fixture
def client():
    # Configura la app para pruebas
    fakenodo_app.config["TESTING"] = True
    # Define paths temporales para la DB y el storage
    db_path = "test_fakenodo_db.json"
    storage_path = "test_fakenodo_storage"
    
    os.environ["WORKING_DIR"] = "." # Asegura que app.py usa los paths correctos
    
    # Sobreescribe las variables de la app para que use paths de test
    fakenodo_app.config["DB_PATH"] = db_path
    fakenodo_app.config["STORAGE"] = storage_path

    with fakenodo_app.test_client() as client:
        yield client # Entrega el cliente al test

    # Limpieza: borra los ficheros de prueba después
    if os.path.exists(db_path):
        os.remove(db_path)
    # Aquí podrías añadir limpieza de la carpeta storage si fuese necesario
    # import shutil; shutil.rmtree(storage_path)


# --- Tests ---

def test_create_deposition(client):
    """Prueba la creación de una deposición."""
    response = client.post("/api/deposit/depositions", json={"metadata": {"title": "Test"}})
    data = response.get_json()
    
    assert response.status_code == 201
    assert data["metadata"]["title"] == "Test"
    assert data["published"] == False

def test_publish_logic(client):
    """Prueba la lógica de versionado y DOI (la más importante)."""
    
    response_create = client.post("/api/deposit/depositions", json={})
    dep_id = response_create.get_json()["id"]
    
    # --- Publicación 1 (Versión 1) ---
    response_pub1 = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    data_pub1 = response_pub1.get_json()
    
    assert response_pub1.status_code == 202
    assert data_pub1["version"] == 1
    assert data_pub1["doi"] == f"10.9999/fakenodo.{dep_id}.v1"

    # --- Publicación 2 (Sin cambios de ficheros -> Metadatos) ---
    response_pub2 = client.post(f"/api/deposit/depositions/{dep_id}/actions/publish")
    data_pub2 = response_pub2.get_json()
    
    assert response_pub2.status_code == 200 # Devuelve 200 OK, no 202
    assert data_pub2["version"] == 1        # Misma versión
    assert data_pub2["doi"] == f"10.9999/fakenodo.{dep_id}.v1" # Mismo DOI