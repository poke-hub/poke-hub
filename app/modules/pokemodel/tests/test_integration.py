import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.pokemodel.models import PokeModel, FMMetaData
from app.modules.pokemodel.services import PokeModelService
import os
from pathlib import Path


@pytest.fixture(scope="module")
def pokemodel_seed(test_client):
    """Prepare a template for the pokemodel index and create minimal dataset/fm/pm if needed."""
    template_dir = Path.cwd() / "app" / "modules" / "pokemodel" / "templates" / "poke_model"
    template_dir.mkdir(parents=True, exist_ok=True)
    tpl_file = template_dir / "index.html"
    created_tpl = False
    if not tpl_file.exists():
        tpl_file.write_text("""{% extends 'base_template.html' %}
{% block title %}PokeModel index{% endblock %}
{% block content %}PokeModel index page{% endblock %}
""")
        created_tpl = True

    with test_client.application.app_context():
        dataset = DataSet.query.get(8)
        if dataset is None:
            meta = DSMetaData(
                deposition_id=12345,
                title="Dataset de pruebas",
                description="Descripción mínima",
                publication_type=PublicationType.NONE,
            )
            db.session.add(meta)
            db.session.flush()

            user = User.query.first()
            if user is None:
                user = User(username="tester", email="tester@example.com")
                db.session.add(user)
                db.session.flush()

            dataset = DataSet(
                id=8,
                user_id=user.id,
                ds_meta_data_id=meta.id,
            )
            db.session.add(dataset)
            db.session.commit()

        fm = FMMetaData(
            poke_filename="test.poke",
            title="FM de prueba",
            description="desc",
            publication_type=PublicationType.NONE,
        )
        db.session.add(fm)
        db.session.flush()

        pm = PokeModel(data_set_id=dataset.id, fm_meta_data_id=fm.id)
        db.session.add(pm)
        db.session.commit()

    yield

    if created_tpl:
        try:
            tpl_file.unlink()
        except Exception:
            pass


def test_pokemodel_index_returns_200(test_client, monkeypatch):
    import app.modules.pokemodel.routes as routes

    monkeypatch.setattr(routes, "render_template", lambda name: "PokeModel index page")

    resp = test_client.get("/poke_model")
    assert resp.status_code == 200
    assert "PokeModel index page" in resp.data.decode("utf-8")


def test_pokemodel_scripts_served(test_client):
    resp = test_client.get("/pokemodel/scripts.js")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    assert "console.log" in text


def test_poke_model_service_counts(test_client, pokemodel_seed):
    with test_client.application.app_context():
        svc = PokeModelService()
        count = svc.count_poke_models()
        assert count >= 1
