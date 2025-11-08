import json
from unittest.mock import MagicMock, patch

import pytest

from app.modules.pokemon_check.check_poke import PokemonSetChecker

# --- Tests para PokemonSetChecker ---


def test_valid_pokemon_set():
    content = """
    Glimmora @ Focus Sash
    Ability: Toxic Debris
    Tera Type: Ghost
    EVs: 252 SpA / 4 SpD / 252 Spe
    IVs: 0 Atk
    - Mortal Spin
    - Stealth Rock
    - Power Gem
    - Earth Power
    """
    checker = PokemonSetChecker(content)
    assert checker.is_valid() is True
    assert not checker.get_errors()
    data = checker.get_parsed_data()
    assert data["pokemon"] == "Glimmora"
    assert data["item"] == "Focus Sash"
    assert data["ability"] == "Toxic Debris"
    assert data["tera_type"] == "Ghost"
    assert data["evs"] == {"spa": 252, "spd": 4, "spe": 252}
    assert data["ivs"] == {"atk": 0}
    assert len(data["moves"]) == 4


def test_empty_file():
    checker = PokemonSetChecker("")
    assert checker.is_valid() is False
    assert "El archivo está vacío." in checker.get_errors()


def test_no_item():
    checker = PokemonSetChecker("Pikachu sin objeto")
    assert checker.is_valid() is False
    assert "Formato de cabecera inválido: Pikachu sin objeto" not in checker.get_errors()


def test_too_many_moves():
    content = """
    Pikachu @ Light Ball
    Ability: Static
    - Move 1
    - Move 2
    - Move 3
    - Move 4
    - Move 5
    """
    checker = PokemonSetChecker(content)
    assert checker.is_valid() is False
    assert "Se especificaron 5 movimientos. El máximo es 4." in checker.get_errors()


def test_invalid_tera_type():
    content = "Pikachu @ Item\nAbility: A\nTera Type: Invalid\n- Move"
    checker = PokemonSetChecker(content)
    assert checker.is_valid() is False
    assert "Tera Tipo no válido: Invalid" in checker.get_errors()


def test_total_evs_exceeded():
    content = "Pikachu @ Item\nAbility: A\nEVs: 252 Atk / 252 Def / 8 Spe\n- Move"
    checker = PokemonSetChecker(content)
    assert checker.is_valid() is False
    assert "La suma total de EVs (512) supera el máximo de 510." in checker.get_errors()


def test_stat_ev_exceeded():
    content = "Pikachu @ Item\nAbility: A\nEVs: 300 Atk\n- Move"
    checker = PokemonSetChecker(content)
    assert checker.is_valid() is False
    assert "Valor de EV inválido para ATK: 300. Debe estar entre 0 y 252." in checker.get_errors()


def test_invalid_iv_value():
    content = "Pikachu @ Item\nAbility: A\nIVs: 32 Atk\n- Move"
    checker = PokemonSetChecker(content)
    assert checker.is_valid() is False
    assert "Valor de IV inválido para ATK: 32. Debe estar entre 0 y 31." in checker.get_errors()


def test_missing_required_fields():
    checker = PokemonSetChecker("Pikachu @ Item")
    assert checker.is_valid() is False
    errors = checker.get_errors()
    assert "No se ha especificado una Habilidad." in errors
    assert "No se ha especificado ningún movimiento." in errors


# --- Tests para la ruta /pokemon_check/check_poke/<file_id> ---


@patch("app.modules.pokemon_check.routes.HubfileService")
def test_check_poke_valid_file(mock_hubfile_service, test_client):
    # Mock del Hubfile y su contenido
    mock_hubfile = MagicMock()
    mock_hubfile.get_path.return_value = "dummy/path/poke.txt"
    mock_hubfile_service.return_value.get_by_id.return_value = mock_hubfile

    valid_content = "Pikachu @ Light Ball\nAbility: Static\n- Volt Tackle"

    # Mock de la lectura del archivo
    with patch("builtins.open", MagicMock(read_data=valid_content)) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = valid_content
        response = test_client.get("/pokemon_check/check_poke/1")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["message"] == "Valid Model"
    assert data["data"]["pokemon"] == "Pikachu"


@patch("app.modules.pokemon_check.routes.HubfileService")
def test_check_poke_invalid_file(mock_hubfile_service, test_client):
    mock_hubfile = MagicMock()
    mock_hubfile.get_path.return_value = "dummy/path/poke.txt"
    mock_hubfile_service.return_value.get_by_id.return_value = mock_hubfile

    invalid_content = "Pikachu\nAbility: Static\nEVs: 999 Atk\n- Move"

    with patch("builtins.open", MagicMock(read_data=invalid_content)) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = invalid_content
        response = test_client.get("/pokemon_check/check_poke/1")

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "La suma total de EVs (999) supera el máximo de 510." in data["errors"]


@patch("app.modules.pokemon_check.routes.HubfileService")
def test_check_poke_file_not_found(mock_hubfile_service, test_client):
    mock_hubfile_service.return_value.get_by_id.return_value = None
    response = test_client.get("/pokemon_check/check_poke/999")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "El archivo no existe." in data["errors"]
