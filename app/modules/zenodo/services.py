# app/modules/zenodo/services.py

import logging
import os

import requests
from dotenv import load_dotenv
from flask_login import current_user

# (Asegúrate de que estas rutas de import sean correctas en tu proyecto)
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class ZenodoService(BaseService):

    def get_zenodo_url(self):
        # --- ESTE ES EL "INTERRUPTOR" ---
        fake = os.getenv("FAKENODO_URL")
        if fake:
            # Si FAKENODO_URL existe, la usamos
            return fake.rstrip("/")

        # Si no, usamos Zenodo real
        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        if FLASK_ENV == "development":
            return os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")
        elif FLASK_ENV == "production":
            return os.getenv("ZENODO_API_URL", "https://zenodo.org/api/deposit/depositions")
        else:
            return os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")

    def get_zenodo_access_token(self):
        return os.getenv("ZENODO_ACCESS_TOKEN")

    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_ACCESS_TOKEN = self.get_zenodo_access_token()
        self.ZENODO_API_URL = self.get_zenodo_url()  # Llama al "interruptor"
        self.headers = {"Content-Type": "application/json"}
        self.params = {"access_token": self.ZENODO_ACCESS_TOKEN}

    # ... (Aquí van TODOS tus otros métodos: test_connection, test_full_connection, etc.) ...

    def create_new_deposition(self, dataset: DataSet) -> dict:
        # ... (Tu lógica original con 'requests.post'...)
        metadata = {
            "title": dataset.ds_meta_data.title,
            # ... (el resto de tus metadatos)
        }
        data = {"metadata": metadata}
        response = requests.post(self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers)
        if response.status_code != 201:
            error_message = f"Failed to create deposition. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None) -> dict:
        poke_filename = feature_model.fm_meta_data.poke_filename
        data = {"name": poke_filename}

        # CORRECCIÓN DE BUG: Asegúrate de que 'user' se maneja bien
        # Si 'user' es None, intenta obtener 'current_user'
        # Pero si esto se llama desde un sitio sin contexto (ej. un test) 'current_user' fallará.
        # Es más seguro pasarlo siempre.
        if user is None:
            user_id = current_user.id
        else:
            user_id = user.id

        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", poke_filename)
        files = {"file": open(file_path, "rb")}

        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(publish_url, params=self.params, data=data, files=files)
        files["file"].close()  # Cierra el archivo después de usarlo

        if response.status_code != 201:
            error_message = f"Failed to upload files. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def publish_deposition(self, deposition_id: int) -> dict:
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/publish"
        response = requests.post(publish_url, params=self.params, headers=self.headers)
        if response.status_code not in [202, 200]:
            raise Exception("Failed to publish deposition")
        return response.json()

    # ... (get_deposition, get_doi, etc. ... van aquí) ...
