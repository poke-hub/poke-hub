import re

VALID_TERA_TYPES = {
    "normal", "fire", "water", "grass", "electric", "ice", "fighting",
    "poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
    "dragon", "dark", "steel", "fairy", "stellar"
}
VALID_STATS = {"hp", "atk", "def", "spa", "spd", "spe"}

class PokemonSetChecker:
    
    MAX_EVS = 510
    MAX_MOVES = 4
    
    def __init__(self, text_content: str):
        self.text = text_content
        self.parsed_data = {
            "pokemon": None,
            "item": None,
            "ability": None,
            "tera_type": None,
            "evs": {},
            "ivs": {},
            "moves": [],
        }
        self.errors = []
        self._parse()
        self._validate()

    def _parse(self):
        """Procesa el texto línea por línea para extraer datos."""
        lines = self.text.strip().splitlines()
        if not lines:
            self.errors.append("El archivo está vacío.")
            return

        # --- Parsear Cabecera (Pokémon @ Item) ---
        header_match = re.match(r'^\s*(.*?)(?:\s+@\s+(.*))?$', lines[0].strip(), re.IGNORECASE)
        if header_match:
            self.parsed_data["pokemon"] = header_match.group(1).strip()
            if header_match.group(2):
                self.parsed_data["item"] = header_match.group(2).strip()
        else:
            self.errors.append(f"Formato de cabecera inválido: {lines[0]}")
            return 

        # --- Parsear el resto de líneas ---
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue # Ignorar líneas vacías

            # Regex para líneas de Movimientos
            move_match = re.match(r'^\s*-\s+(.*)$', line)
            if move_match:
                self.parsed_data["moves"].append(move_match.group(1).strip())
                continue

            # Regex para líneas de clave-valor
            kv_match = re.match(r'^\s*([^:]+):\s*(.*)$', line, re.IGNORECASE)
            if kv_match:
                key = kv_match.group(1).strip().lower()
                value = kv_match.group(2).strip()

                if key == "ability":
                    self.parsed_data["ability"] = value
                elif key == "tera type":
                    self.parsed_data["tera_type"] = value
                elif key == "evs":
                    self.parsed_data["evs"] = self._parse_stats(value)
                elif key == "ivs":
                    self.parsed_data["ivs"] = self._parse_stats(value)
                # (Puedes añadir más claves aquí, como "Nature", "Level", etc.)
                continue

    def _parse_stats(self, stat_string: str) -> dict:
        """Parsea un string de stats."""
        stats_dict = {}
        stat_regex = re.compile(r'(\d+)\s+([a-zA-Z]{2,3})', re.IGNORECASE)
        
        matches = stat_regex.findall(stat_string)
        for val, stat_name in matches:
            stat_key = stat_name.lower()
            if stat_key in VALID_STATS:
                stats_dict[stat_key] = int(val)
            else:
                self.errors.append(f"Stat desconocido: '{stat_name}'")
        return stats_dict

    def _validate(self):
        """Comprueba las reglas de negocio sobre los datos parseados."""
        data = self.parsed_data

        # --- Validación de Campos Requeridos ---
        if not data["pokemon"]:
            self.errors.append("No se ha especificado un Pokémon.")
        if not data["ability"]:
            self.errors.append("No se ha especificado una Habilidad.")
        if not data["moves"]:
            self.errors.append("No se ha especificado ningún movimiento.")

        # --- Validación contra Listas Válidas ---
        if data["tera_type"] and data["tera_type"].lower() not in VALID_TERA_TYPES:
            self.errors.append(f"Tera Tipo no válido: {data['tera_type']}")

        # --- Validación de Movimientos ---
        if len(data["moves"]) > self.MAX_MOVES:
            self.errors.append(f"Se especificaron {len(data['moves'])} movimientos. El máximo es {self.MAX_MOVES}.")

        # --- Validación de EVs ---
        total_evs = sum(data["evs"].values())
        if total_evs > self.MAX_EVS:
            self.errors.append(f"La suma total de EVs ({total_evs}) supera el máximo de {self.MAX_EVS}.")
        for stat, val in data["evs"].items():
            if not (0 <= val <= 252):
                self.errors.append(f"Valor de EV inválido para {stat.upper()}: {val}. Debe estar entre 0 y 252.")

        # --- Validación de IVs ---
        for stat, val in data["ivs"].items():
            if not (0 <= val <= 31):
                self.errors.append(f"Valor de IV inválido para {stat.upper()}: {val}. Debe estar entre 0 y 31.")

    def is_valid(self) -> bool:
        """Devuelve True si no se encontraron errores, False en caso contrario."""
        return len(self.errors) == 0

    def get_parsed_data(self) -> dict:
        """Devuelve los datos parseados como un diccionario."""
        return self.parsed_data

    def get_errors(self) -> list:
        """Devuelve la lista de errores de validación."""
        return self.errors
