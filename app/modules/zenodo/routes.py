import os
from flask import render_template
from flask_login import current_user

from app.modules.zenodo import zenodo_bp
from app.modules.zenodo.services import ZenodoService
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from core.configuration.configuration import uploads_folder_name


@zenodo_bp.route("/zenodo", methods=["GET"])
def index():
    return render_template("zenodo/index.html")


@zenodo_bp.route("/zenodo/test", methods=["GET"])
def zenodo_test() -> dict:
    service = ZenodoService()
    return service.test_full_connection()


@zenodo_bp.route("/zenodo/test-publish", methods=["GET"])
def zenodo_test_publish():
    """
    Un endpoint de prueba de integración que prueba el flujo de publicación completo.
    """
    service = ZenodoService()

    # --- Simular datos (Mock data) ---
    class MockAuthor:
        name = "Test Author"
        affiliation = "Test Affiliation"
        orcid = "0000-0000-0000-0001"

    # ESTA ES LA PARTE QUE CAMBIA:
    class MockPublicationType:
        """Un objeto falso que simula tener un atributo .value"""
        value = "dataset"

    class MockMetaData:
        title = "Mi Publicación de Prueba"
        publication_type = MockPublicationType() # <-- Ahora usamos el objeto falso
        description = "Descripción de prueba"
        authors = [MockAuthor()]
        tags = "test, fakenodo"
        uvl_filename = "test_file.txt" # Usaremos este nombre

    class MockDataSet:
        id = 999 
        ds_meta_data = MockMetaData()

    class MockFeatureModel:
        fm_meta_data = MockMetaData()

    class MockUser:
        id = 1 # Usamos 1 para no depender de si has iniciado sesión

    dataset = MockDataSet()
    fm = MockFeatureModel()
    user = MockUser()

    # --- Crear el fichero de prueba (como en test_full_connection) ---
    user_folder = os.path.join(uploads_folder_name(), f"user_{str(user.id)}")
    dataset_folder = os.path.join(user_folder, f"dataset_{dataset.id}")
    os.makedirs(dataset_folder, exist_ok=True)
    file_path = os.path.join(dataset_folder, fm.fm_meta_data.uvl_filename)

    with open(file_path, "w") as f:
        f.write("Este es el fichero UVL de prueba.")

    try:
        # --- 1. Crear Deposición ---
        deposition_data = service.create_new_deposition(dataset)
        dep_id = deposition_data["id"]

        # --- 2. Subir Fichero ---
        service.upload_file(dataset, dep_id, fm, user=user)

        # --- 3. Publicar (La prueba real) ---
        publish_data = service.publish_deposition(dep_id)

        # --- 4. Publicar de nuevo (Prueba de lógica de 'no-cambios') ---
        publish_data_again = service.publish_deposition(dep_id)

        # Limpieza
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "success": True,
            "primera_publicacion (ficheros nuevos)": publish_data,
            "segunda_publicacion (mismos ficheros)": publish_data_again
        }

    except Exception as e:
        # Limpieza en caso de error
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"success": False, "error": str(e)}, 500