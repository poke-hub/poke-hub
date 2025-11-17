import os
import random
import sys

from locust import HttpUser, between, task

from app import create_app
from app.modules.hubfile.models import Hubfile
from core.environment.host import get_host_for_locust_testing

# --- Configuración para acceder a la aplicación Flask ---
# Añade el directorio raíz del proyecto al path para poder importar los módulos de la app
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)


# ---------------------------------------------------------


def get_all_file_ids():
    """
    Obtiene todos los IDs de Hubfile directamente desde la base de datos.
    """
    app = create_app()
    with app.app_context():
        try:
            ids = [hubfile.id for hubfile in Hubfile.query.with_entities(Hubfile.id).all()]
            print(f"Obtenidos {len(ids)} IDs desde la base de datos para el test de carga.")
            return ids
        except Exception as e:
            print(f"Error al conectar con la base de datos para obtener los IDs: {e}")
            return []


# Obtenemos los IDs una sola vez cuando se carga el script de Locust
AVAILABLE_FILE_IDS = get_all_file_ids()


class PokemonCheckUser(HttpUser):
    """
    Define el comportamiento del usuario para las pruebas de carga del módulo pokemon_check.
    """

    wait_time = between(5, 9)  # Tiempo de espera entre 5 y 9 segundos
    host = get_host_for_locust_testing()

    @task
    def check_pokemon_set(self):
        """
        Simula la petición a la API para validar un set de Pokémon.
        Utiliza un ID de archivo aleatorio de la lista obtenida al inicio.
        """
        if AVAILABLE_FILE_IDS:
            file_id = random.choice(AVAILABLE_FILE_IDS)
            self.client.get(f"/pokemon_check/check_poke/{file_id}", name="/pokemon_check/check_poke/[id]")
