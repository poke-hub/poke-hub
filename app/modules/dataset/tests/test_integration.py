import io
import os
import shutil
import zipfile

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType


@pytest.fixture(scope="module")
def dataset_seed(test_client):
    with test_client.application.app_context():
        ds = DataSet.query.get(8)
        if ds is None:
            meta = DSMetaData(
                deposition_id=12345,
                title="Dataset de pruebas",
                description="Descripción mínima",
                publication_type=PublicationType.NONE,
                dataset_doi="10.1234/dataset8",
            )
            db.session.add(meta)
            db.session.flush()

            user = User.query.first()
            if user is None:
                user = User(username="tester", email="tester@example.com")
                db.session.add(user)
                db.session.flush()

            ds = DataSet(
                id=8,
                user_id=user.id,
                ds_meta_data_id=meta.id,
            )
            db.session.add(ds)
            db.session.commit()
    yield


def test_increment_download_count(test_client, dataset_seed):
    with test_client.application.app_context():
        dataset = DataSet.query.get(8)
        assert dataset is not None, "No se pudo crear/obtener el DataSet id=8"
        inicial = dataset.download_count

    resp = test_client.get("/dataset/download/8")
    assert resp.status_code == 200, "La ruta no devolvió 200"

    with test_client.application.app_context():
        actualizado = DataSet.query.get(8)
        assert actualizado.download_count == inicial + 1, "download_count no se incrementó"


def test_increment_download_count_range(test_client, dataset_seed):
    num_descargas = 3
    with test_client.application.app_context():
        dataset = DataSet.query.get(8)
        assert dataset is not None, "No existe el DataSet id=8"
        inicial = dataset.download_count

    for _ in range(num_descargas):
        resp = test_client.get("/dataset/download/8")
        assert resp.status_code == 200, "La ruta no devolvió 200 en una de las descargas"

    with test_client.application.app_context():
        actualizado = DataSet.query.get(8)
        assert (
            actualizado.download_count == inicial + num_descargas
        ), f"download_count esperado {inicial + num_descargas}, obtenido {actualizado.download_count}"


def test_dataset_stats(test_client, dataset_seed):
    with test_client.application.app_context():
        dataset = DataSet.query.get(8)
        assert dataset is not None, "No se pudo crear/obtener el DataSet id=8"
        initial_download_count = dataset.download_count

    resp = test_client.get("/dataset/8/stats")
    assert resp.status_code == 200, "La ruta stats no devolvió 200"

    html = resp.data.decode("utf-8")
    assert "Dataset de pruebas" in html, "El título del dataset no aparece en stats"
    assert "Downloads" in html or "downloads" in html, "No se muestra información de descargas"
    assert "Views" in html or "views" in html, "No se muestra información de vistas"

    assert str(initial_download_count) in html, f"No aparece el contador de descargas {initial_download_count}"


def _make_zip_bytes(files: dict, root_prefix: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            path = os.path.join(root_prefix, name) if root_prefix else name
            zf.writestr(path, content)
    buf.seek(0)
    return buf.read()


def test_integration_upload_zip_and_github(test_client, monkeypatch):
    # login with default test user created by conftest
    rv = test_client.post(
        "/login",
        data={"email": "test@example.com", "password": "test1234"},
        follow_redirects=False,
    )
    assert rv.status_code in (200, 302)

    # ZIP upload
    files = {
        "a.poke": "content a",
        "b.POKE": "content b",
        "ignore.md": "no",
    }

    zip_bytes = _make_zip_bytes(files)

    data = {"file": (io.BytesIO(zip_bytes), "upload.zip")}
    resp = test_client.post("/dataset/zip/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "saved" in body and len(body["saved"]) >= 1

    # GitHub import (mock requests.get to return a zip)
    repo_files = {"rootdir/path/gh.poke": "ok", "rootdir/other/skip.txt": "no"}
    gh_zip = _make_zip_bytes(repo_files)

    class DummyResp:
        status_code = 200

        def __init__(self, content):
            self.content = content

    def fake_get(url, timeout=60):
        return DummyResp(gh_zip)

    monkeypatch.setattr("requests.get", fake_get)

    payload = {"repo_url": "https://github.com/owner/repo", "branch": "main", "subdir": "path"}
    resp2 = test_client.post("/dataset/github/import", json=payload)
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert "saved" in body2 and any(s.endswith("gh.poke") for s in body2["saved"])

    # verify files written to temp folder for the test user
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        temp_folder = AuthenticationService().temp_folder_by_user(user)

    try:
        for saved in body.get("saved", []) + body2.get("saved", []):
            assert os.path.exists(os.path.join(temp_folder, saved))
    finally:
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
