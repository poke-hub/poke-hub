import os
import tempfile

import pytest

from app.modules.pokemodel.models import FMMetaData, FMMetrics, PokeModel, parse_poke


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_fm_meta_data_get_all_tags():

    metadata = FMMetaData(tags="tag1,tag2,tag3")
    tags = metadata.get_all_tags()
    assert tags == {"tag1", "tag2", "tag3"}, "The tags extracted do not match the expected set."

    metadata_empty = FMMetaData(tags="")
    tags_empty = metadata_empty.get_all_tags()
    assert tags_empty == set(), "The tags extracted from an empty string should be an empty set."


def _write_temp_file(contents: str) -> str:
    fd, path = tempfile.mkstemp(text=True)
    with os.fdopen(fd, "w") as f:
        f.write(contents)
    return path


def test_parse_poke_with_item_and_all_fields():
    content = """Charizard @ Choice Scarf
Ability: Blaze
Tera Type: Fire
EVs: 252 Atk/4 Def/252 Spe
IVs: 31 Atk/31 Def/31 Spe
- Flamethrower
- Dragon Claw
- Earthquake
- Roost
"""
    path = _write_temp_file(content)
    try:
        pokemon = parse_poke(path)
        assert pokemon.name == "Charizard"
        assert pokemon.item == "Choice Scarf"
        assert pokemon.ability == "Blaze"
        assert pokemon.tera_type == "Fire"
        assert pokemon.evs.get("Atk") == 252
        assert pokemon.evs.get("Def") == 4
        assert pokemon.evs.get("Spe") == 252
        assert pokemon.ivs.get("Atk") == 31
        assert "Flamethrower" in pokemon.moves
        assert len(pokemon.moves) == 4
    finally:
        os.remove(path)


def test_parse_poke_without_item_and_with_empty_lines():
    content = """Squirtle

Ability: Torrent

- Water Gun
- Tackle

"""
    path = _write_temp_file(content)
    try:
        pokemon = parse_poke(path)
        assert pokemon.name == "Squirtle"
        assert pokemon.item == ""
        assert pokemon.ability == "Torrent"
        assert pokemon.moves == ["Water Gun", "Tackle"]
        assert pokemon.evs == {}
        assert pokemon.ivs == {}
    finally:
        os.remove(path)


def test_repr_methods():
    pm = PokeModel()
    pm.id = 7
    assert repr(pm) == "PokeModel<7>"

    fm = FMMetaData()
    fm.title = "My Feature Model"
    assert repr(fm) == "FMMetaData<My Feature Model"

    metrics = FMMetrics()
    metrics.solver = "sat_solver"
    metrics.not_solver = "not_sat"
    assert "solver=sat_solver" in repr(metrics)


def test_parse_poke_case_insensitive_keys():
    content = """Pikachu
ability: Static
tera type: Electric
EVs: 4 SpA
- Thunderbolt
"""
    path = _write_temp_file(content)
    try:
        pokemon = parse_poke(path)
        assert pokemon.name == "Pikachu"
        assert pokemon.ability.lower() == "static"
        assert pokemon.tera_type.lower() == "electric"
        assert pokemon.evs.get("SpA") == 4
        assert pokemon.moves == ["Thunderbolt"]
    finally:
        os.remove(path)


def test_parse_poke_malformed_evs_raises():
    content = """Bulbasaur
EVs: 252Atk/4 Def
- Vine Whip
"""
    path = _write_temp_file(content)
    try:
        with pytest.raises(ValueError):
            _ = parse_poke(path)
    finally:
        os.remove(path)


def test_parse_poke_empty_file_raises_indexerror():
    content = """
"""
    path = _write_temp_file(content)
    try:
        with pytest.raises(IndexError):
            _ = parse_poke(path)
    finally:
        os.remove(path)


def test_parse_poke_missing_optional_fields_defaults():
    content = """Eevee
- Tackle
"""
    path = _write_temp_file(content)
    try:
        pokemon = parse_poke(path)
        assert pokemon.name == "Eevee"
        assert pokemon.item == ""
        assert pokemon.ability == ""
        assert pokemon.tera_type == ""
        assert pokemon.evs == {}
        assert pokemon.ivs == {}
        assert pokemon.moves == ["Tackle"]
    finally:
        os.remove(path)


def test_parse_poke_moves_whitespace_handling():
    content = """Snorlax
Ability: Immunity
    -  Body Slam
    - Sleep Talk
"""
    path = _write_temp_file(content)
    try:
        pokemon = parse_poke(path)
        assert pokemon.moves == ["Body Slam", "Sleep Talk"]
    finally:
        os.remove(path)


def test_parse_poke_file_not_found_raises():
    fake_path = "/tmp/non_existent_file_abcdefgh.txt"
    with pytest.raises(FileNotFoundError):
        _ = parse_poke(fake_path)


def test_parse_poke_malformed_ivs_raises_valueerror():
    content = """Gengar
IVs: 31SpA/31 Spe
- Shadow Ball
"""
    path = _write_temp_file(content)
    try:
        with pytest.raises(ValueError):
            _ = parse_poke(path)
    finally:
        os.remove(path)


def test_get_pokemon_delegates_to_parse_poke(monkeypatch, test_client):
    pm = PokeModel()

    class DS:
        pass

    ds = DS()
    ds.user_id = 11
    pm.__dict__["data_set"] = ds
    pm.data_set_id = 5

    called = {}

    def fake_parse(path):
        called["path"] = path
        return "parsed"

    monkeypatch.setattr("app.modules.pokemodel.models.parse_poke", fake_parse)

    with test_client.application.app_context():
        test_client.application.root_path = "/srv/app/myapp"
        res = pm.get_pokemon()

    parent = os.path.dirname("/srv/app/myapp")
    expected = os.path.join(parent, f"uploads/user_{ds.user_id}/dataset_{pm.data_set_id}/")
    assert called.get("path") == expected
    assert res == "parsed"
