# app/modules/zenodo/services.py

import logging
import os

# import requests  # F401 - No se usa, ya que llamamos a fakenodo directamente
from dotenv import load_dotenv

from app.modules.dataset.models import DataSet
from app.modules.fakenodo.routes import create_deposition, publish_deposition, upload_file
from app.modules.pokemodel.models import PokeModel
from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class ZenodoService(BaseService):

    def get_zenodo_url(self):
        fake_url = os.getenv("FAKENODO_URL")

        if not fake_url:
            raise ValueError("FAKENODO_URL no está definida. No se puede iniciar el ZenodoService.")
        logger.info(f"ZenodoService está usando FAKENODO en: {fake_url}")
        return fake_url.rstrip("/")

    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_API_URL = self.get_zenodo_url()  # Llama al "interruptor"
        self.headers = {"Content-Type": "application/json"}
        self.params = {}

    def create_new_deposition(self, dataset: DataSet) -> dict:
        # metadata = {
        #     "title": dataset.ds_meta_data.title,
        # }
        # data = {"metadata": metadata}  # F841 - Esta variable no se usaba
        response_json, status_code = create_deposition()
        # response = requests.post(self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers)
        if status_code != 201:
            error_message = f"Failed to create deposition. Error details: {response_json}"
            raise Exception(error_message)
        return response_json

    def upload_file(self, dataset: DataSet, deposition_id: int, poke_model: PokeModel, user=None) -> dict:
        poke_filename = poke_model.fm_meta_data.poke_filename
        data = {"name": poke_filename}

        user_id = user.id

        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", poke_filename)
        files = {"file": open(file_path, "rb")}

        # publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response_json, status_code = upload_file(deposition_id, data, files)
        # response = requests.post(publish_url, params=self.params, data=data, files=files)
        files["file"].close()  # Cierra el archivo después de usarlo

        if status_code != 201:
            error_message = f"Failed to upload files. Error details: {response_json()}"
            raise Exception(error_message)
        return response_json

    def publish_deposition(self, deposition_id: int) -> dict:
        response_json, status_code = publish_deposition(deposition_id)
        if status_code not in [202, 200]:
            raise Exception("Failed to publish deposition")
        return response_json
