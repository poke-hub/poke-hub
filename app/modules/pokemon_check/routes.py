import logging

from flask import jsonify

from app.modules.hubfile.services import HubfileService
from app.modules.pokemon_check import pokemon_check_bp
from app.modules.pokemon_check.check_poke import PokemonSetChecker

logger = logging.getLogger(__name__)


@pokemon_check_bp.route("/pokemon_check/check_poke/<int:file_id>", methods=["GET"])
def check_poke(file_id):
    """
    Valida un archivo .poke
    Comprueba si la sintaxis del set de Pokémon es válida.
    """
    try:
        hubfile = HubfileService().get_by_id(file_id)
        if not hubfile:
            return jsonify({"errors": ["El archivo no existe."]}), 404

        file_path = hubfile.get_path()

        # 2. LEEMOS EL CONTENIDO DEL ARCHIVO
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Error leyendo el archivo {file_id}: {e}")
            return jsonify({"errors": [f"No se pudo leer el archivo: {e}"]}), 500

        # 3. UTILIZAMOS EL NUEVO PARSER
        parser = PokemonSetChecker(file_content)

        if not parser.is_valid():
            # Si hay errores, los devolvemos
            logger.warning(f"El archivo {file_id} es inválido: {parser.get_errors()}")
            return jsonify({"errors": parser.get_errors()}), 400

        # Si es válido, devolvemos un JSON con los datos parseados
        return jsonify({"message": "Valid Model", "data": parser.get_parsed_data()}), 200

    except Exception as e:
        logger.error(f"Excepción en check_poke para file_id {file_id}: {e}")
        return jsonify({"errors": [str(e)]}), 500
