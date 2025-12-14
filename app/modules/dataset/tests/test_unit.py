import io
import os
import shutil
import uuid
import zipfile
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from zipfile import ZipFile

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.conftest import login, logout
from app.modules.dataset.models import Author, DataSet, DSComment, DSMetaData, PublicationType
from app.modules.dataset.services import DataSetService, SizeService
from app.modules.pokemodel.models import FMMetaData, PokeModel, Pokemon
from app.modules.profile.models import UserProfile


class DummyDS:
    def __init__(self, id, title, user):
        self.id = id

        class Meta:
            pass

        self.ds_meta_data = Mock()
        self.ds_meta_data.title = title
        self.user = user

    def get_pokehub_doi(self):
        return f"http://localhost/doi/10.1234/ds.{self.id}"

    def get_file_total_size_for_human(self):
        return "1.00 MB"


def test_trending_by_views_delegates_to_repository():
    svc = DataSetService()
    # mock repository.trending_by_views
    expected = [(DummyDS(1, "T1", Mock()), 10), (DummyDS(2, "T2", Mock()), 7)]
    svc.repository = Mock()
    svc.repository.trending_by_views.return_value = expected

    res = svc.trending_by_views(limit=3, days=30)

    svc.repository.trending_by_views.assert_called_once_with(limit=3, days=30)
    assert res == expected


def test_trending_by_downloads_delegates_to_repository():
    svc = DataSetService()
    expected = [(DummyDS(5, "D1", Mock()), 4)]
    svc.repository = Mock()
    svc.repository.trending_by_downloads.return_value = expected

    res = svc.trending_by_downloads(limit=1, days=7)

    svc.repository.trending_by_downloads.assert_called_once_with(limit=1, days=7)
    assert res == expected


@pytest.mark.parametrize(
    "size,expected",
    [
        (10, "10 bytes"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1024**2, "1.0 MB"),
        (3 * 1024**2 + 512, f"{round((3*1024**2 + 512)/(1024**2), 2)} MB"),
        (5 * 1024**3, "5.0 GB"),
    ],
)
def test_size_service_human_readable(size, expected):
    s = SizeService()
    res = s.get_human_readable_size(size)
    # for MB/GB rounding differences, assert startswith for MB/GB
    if "MB" in expected or "GB" in expected:
        assert expected.split()[1] in res
    else:
        assert res == expected


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():

        user = User(email="user@example.com", password="test1234")
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(user_id=user.id, name="Nombre", surname="Apellido")
        db.session.add(profile)
        db.session.commit()

        meta_draft = DSMetaData(
            title="Draft dataset", description="Un dataset en modo borrador.", publication_type=PublicationType.OTHER
        )
        meta_final = DSMetaData(
            title="Published dataset", description="Un dataset publicado.", publication_type=PublicationType.OTHER
        )
        db.session.add_all([meta_draft, meta_final])
        db.session.commit()

        draft_dataset = DataSet(user_id=user.id, ds_meta_data_id=meta_draft.id, draft_mode=True)
        final_dataset = DataSet(user_id=user.id, ds_meta_data_id=meta_final.id, draft_mode=False)
        db.session.add_all([draft_dataset, final_dataset])
        db.session.commit()

    yield test_client


# Test 1: crear dataset en modo draft. Successfull.
def test_create_dataset_draft_success(test_client):

    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsucessful"

    data = {
        "save_as_draft": "true",
        "title": "test",
        "desc": "test",
        "publication_type": "test",
    }

    response = test_client.post("/dataset/upload", data=data)
    assert response.status_code == 200, "Expected 200."
    json_data = response.get_json()

    assert json_data["message"] == "Draft saved", "Confirmation message is not the one expected."
    assert "dataset_id" in json_data, "Dataset ID not found."

    with test_client.application.app_context():
        dataset = DataSet.query.get(json_data["dataset_id"])
        assert dataset is not None, "Dataset was not sucessfuly stored in DB."
        assert dataset.draft_mode is True, "Dataset was not sucessfuly stored as draft."

    logout(test_client)


# Test 1: crear dataset en modo draft sin titulo. Unsuccessfull.


def test_create_dataset_draft_unsuccessful_no_title(test_client):

    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccesful."

    data = {
        "save_as_draft": "true",
        "title": "",
        "desc": "test",
        "publication_type": "test",
    }

    response = test_client.post("/dataset/upload", data=data)
    assert response.status_code == 400, "Expected 400. Cause: missing title"
    json_data = response.get_json()

    assert "introduce un título" in json_data["message"].lower(), "Missing error title message."

    logout(test_client)


# Test 3: editar dataset en modo draft. Successfull.
def test_edit_draft_dataset_allowed(test_client):

    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsucessful."

    with test_client.application.app_context():
        draft = DataSet.query.filter_by(draft_mode=True).first()
        assert draft is not None, "Dataset not found"

    data = {
        "save_as_draft": "true",
        "title": "test3",
        "desc": "test3",
        "publication_type": "test3",
    }

    response = test_client.post(f"/dataset/{draft.id}/edit", data=data)
    assert response.status_code in (200, 302), f"Expected 200 or 302, got{response.status_code}"
    assert b"Draft updated successfully" in response.data or b"redirect" in response.data

    logout(test_client)


# Test 4: editar dataset publicado. Unsuccessfull.
def test_edit_non_draft_dataset_forbidden(test_client):

    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsucessful."

    with test_client.application.app_context():
        non_draft = DataSet.query.filter_by(draft_mode=False).first()
        assert non_draft is not None, "Dataset not found."

    data = {
        "save_as_draft": "true",
        "title": "test4",
        "desc": "test4",
        "publication_type": "test4",
    }

    response = test_client.post(f"/dataset/{non_draft.id}/edit", data=data)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert b"Bad Request" in response.data or b"400" in response.data

    logout(test_client)


# Test 5: acceder formulario de edición de dataset en draft. Successful.
def test_get_edit_draft_dataset_page(test_client):

    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login sucessful."

    with test_client.application.app_context():
        draft = DataSet.query.filter_by(draft_mode=True).first()
        assert draft is not None, "Draft dataset not found"

    response = test_client.get(f"/dataset/{draft.id}/edit")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert b"Edit" in response.data or b"upload_dataset" in response.data

    logout(test_client)


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_ds_meta_data_get_all_tags():

    metadata = DSMetaData(tags="tag1,tag2,tag3")
    DataSet(ds_meta_data=metadata)
    tags = metadata.get_all_tags()
    assert tags == {"tag1", "tag2", "tag3"}, "The tags extracted do not match the expected set."

    fm_meta_data = FMMetaData(tags="tag3,tag5")
    fm_meta_data2 = FMMetaData(tags="tag4")
    fm1 = PokeModel(fm_meta_data=fm_meta_data)
    fm2 = PokeModel(fm_meta_data=fm_meta_data2)
    metadata_complex = DSMetaData(tags="tag1 , tag2")
    DataSet(poke_models=[fm1, fm2], ds_meta_data=metadata_complex)
    tags_complex = metadata_complex.get_all_tags()
    assert tags_complex == {
        "tag1",
        "tag2",
        "tag3",
        "tag4",
        "tag5",
    }, "The tags extracted with spaces do not match the expected set."

    metadata_empty = DSMetaData(tags="")
    DataSet(ds_meta_data=metadata_empty)
    tags_empty = metadata_empty.get_all_tags()
    assert tags_empty == set(), "The tags extracted from an empty string should be an empty set."


def test_ds_meta_data_get_all_authors():

    author1 = Author(name="author1")
    author2 = Author(name="author2")
    metadata = DSMetaData(authors=[author1, author2])
    DataSet(ds_meta_data=metadata)
    authors = metadata.get_all_authors()
    assert authors == {author1, author2}, "The authors extracted do not match the expected set."

    author3 = Author(name="author3")
    author4 = Author(name="author4")
    fm_meta_data = FMMetaData(authors=[author1, author2])
    fm_meta_data2 = FMMetaData(authors=[author3])
    fm1 = PokeModel(fm_meta_data=fm_meta_data)
    fm2 = PokeModel(fm_meta_data=fm_meta_data2)
    metadata_complex = DSMetaData(authors=[author1, author4])
    DataSet(poke_models=[fm1, fm2], ds_meta_data=metadata_complex)
    authors_complex = metadata_complex.get_all_authors()
    assert authors_complex == {
        author1,
        author2,
        author3,
        author4,
    }, "The authors extracted with spaces do not match the expected set."

    metadata_empty = DSMetaData(authors=[])
    DataSet(ds_meta_data=metadata_empty)
    authors_empty = metadata_empty.get_all_authors()
    assert authors_empty == set(), "The authors extracted from an empty list should be an empty set."


def test_ds_meta_data_has_tag():

    metadata = DSMetaData(tags="tag1,tag3")
    fm_meta_data = FMMetaData(tags="tag2,tag3")
    fm = PokeModel(fm_meta_data=fm_meta_data)
    DataSet(poke_models=[fm], ds_meta_data=metadata)

    assert metadata.has_tag("tag1") is True, "The tag 'tag1' should be found."
    assert metadata.has_tag("tag2") is True, "The tag 'tag2' should be found."
    assert metadata.has_tag("tag4") is False, "The tag 'tag4' should not be found."


def test_ds_meta_data_has_author():

    author1 = Author(id=1, name="author1")
    author2 = Author(id=2, name="author2")
    author3 = Author(id=3, name="author3")
    Author(id=4, name="author4")
    metadata = DSMetaData(authors=[author1, author3])
    fm_meta_data = FMMetaData(authors=[author2, author3])
    fm = PokeModel(fm_meta_data=fm_meta_data)
    DataSet(poke_models=[fm], ds_meta_data=metadata)

    assert metadata.has_author(1) is True, "The author 'author1' should be found."
    assert metadata.has_author(2) is True, "The author 'author2' should be found."
    assert metadata.has_author(4) is False, "The author 'author4' should not be found."


def test_dataset_to_indexed():
    author1 = Author(id=1, name="author1")
    author2 = Author(id=2, name="author2")
    author3 = Author(id=3, name="author3")
    fm_meta_data = FMMetaData(tags="tag1,tag2", authors=[author1, author3])
    fm_meta_data2 = FMMetaData()
    pokemon1 = Pokemon()
    pokemon1.name = "Pikachu"
    pokemon1.ability = "Lanzar rayos"
    pokemon1.evs = {"Fernando Alonso": 33, "Antony": 7}
    pokemon1.ivs = {"Uva": 3}
    pokemon1.moves = ["Impactrueno", "Rayo", "Trueno", "Chispa"]
    pokemon2 = Pokemon()
    pokemon2.name = "Charizard"
    pokemon2.ability = "Mar Llamas"
    pokemon2.evs = {"Purple": 6}
    pokemon2.ivs = {"Tesla": 9}
    pokemon2.moves = ["Llamarada", "Vuelo", "Giga Impacto", "Ascuas"]
    fm1 = MagicMock(spec=PokeModel)
    fm1.fm_meta_data = fm_meta_data
    fm1.get_pokemon = MagicMock(return_value=pokemon1)
    fm1.get_total_evs = MagicMock(return_value=40)
    fm1.get_total_ivs = MagicMock(return_value=3)
    fm2 = MagicMock(spec=PokeModel)
    fm2.fm_meta_data = fm_meta_data2
    fm2.get_pokemon = MagicMock(return_value=pokemon2)
    fm2.get_total_evs = MagicMock(return_value=6)
    fm2.get_total_ivs = MagicMock(return_value=9)
    metadata = DSMetaData(
        title="Test Dataset",
        description="A dataset for testing.",
        tags="tag2,tag3",
        authors=[author2, author3],
        dataset_doi="doi_de_prueba",
    )
    dataset = DataSet(created_at=datetime.fromisoformat("2025-11-30T16:15:23"), ds_meta_data=metadata)
    dataset.__dict__["poke_models"] = [fm1, fm2]

    with patch.object(PokeModel, "get_pokemon", return_value=[pokemon1, pokemon2]):
        indexed = dataset.to_indexed()

    assert indexed["title"] == "Test Dataset", "Title does not match."
    assert indexed["description"] == "A dataset for testing.", "Description does not match."
    assert "tag1" in indexed["tags"] and "tag2" in indexed["tags"] and "tag3" in indexed["tags"], "Tags do not match."
    assert (
        "author1" in indexed["authors"] and "author2" in indexed["authors"] and "author3" in indexed["authors"]
    ), "Authors do not match."
    assert indexed["created_at"] == "2025-11-30T16:15:23", "Creation date does not match."
    assert "Pikachu" in indexed["pokemons"] and "Charizard" in indexed["pokemons"], "Pokemons do not match."
    assert "Lanzar rayos" in indexed["abilities"] and "Mar Llamas" in indexed["abilities"], "Abilities do not match."
    assert indexed["max_ev_count"] == 40, "Max EV count does not match."
    assert indexed["max_iv_count"] == 9, "Max IV count does not match."
    assert set(indexed["moves"]) == {
        "Impactrueno",
        "Llamarada",
        "Ascuas",
        "Trueno",
        "Rayo",
        "Vuelo",
        "Giga Impacto",
        "Chispa",
    }, "Moves do not match."
    assert indexed["doi"] == "doi_de_prueba", "DOI does not match."


@pytest.fixture
def dataset_service():
    return DataSetService()


def test_extract_pokes_from_zip(dataset_service, tmp_path):
    buf = io.BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("file1.poke", "content1")
        zf.writestr("file2.txt", "should be ignored")
    buf.seek(0)

    saved = dataset_service.extract_pokes_from_zip(buf, tmp_path)
    assert "file1.poke" in saved
    assert not any(f.endswith(".txt") for f in saved)
    assert (tmp_path / "file1.poke").exists()


def test_import_pokes_from_github(dataset_service, tmp_path):
    fake_zip = io.BytesIO()
    with ZipFile(fake_zip, "w") as zf:
        zf.writestr("repo-branch/file1.poke", "content")
    fake_zip.seek(0)

    with patch.object(dataset_service, "fetch_repo_zip", return_value=fake_zip.getvalue()):
        saved = dataset_service.import_pokes_from_github("https://github.com/fake/repo", dest_dir=tmp_path)
        assert "file1.poke" in saved
        assert (tmp_path / "file1.poke").exists()


def test_increment_download_count():
    svc = DataSetService()
    svc.repository = Mock()

    mock_dataset = Mock()
    mock_dataset.download_count = 5
    svc.repository.get_or_404.return_value = mock_dataset

    dataset_id = 42
    svc.increment_download_count(dataset_id)

    svc.repository.get_or_404.assert_called_once_with(dataset_id)
    svc.repository.update.assert_called_once_with(dataset_id, download_count=6)


@pytest.fixture
def feedback_user(test_client):
    """Crea un usuario único para las pruebas de comentarios."""
    unique_email = f"feedback_{uuid.uuid4()}@example.com"
    user = User(email=unique_email, password="password")
    profile = UserProfile(user=user, surname="Feedback", name="User")

    db.session.add(user)
    db.session.add(profile)
    db.session.commit()
    return user


@pytest.fixture
def feedback_dataset(feedback_user):
    """Crea un dataset local (unsynchronized) para el usuario de pruebas."""
    ds_meta = DSMetaData(
        title=f"Feedback Dataset {uuid.uuid4()}",
        description="Dataset for testing comments",
        publication_type=PublicationType.NONE,
        publication_doi="",
        dataset_doi="",  # Sin DOI = Local / Unsynchronized
        tags="test, feedback",
    )
    dataset = DataSet(user_id=feedback_user.id, ds_meta_data=ds_meta)
    db.session.add(dataset)
    db.session.commit()
    return dataset


def _make_zip_bytes(files: dict, root_prefix: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            path = os.path.join(root_prefix, name) if root_prefix else name
            zf.writestr(path, content)
    buf.seek(0)
    return buf.read()


def test_upload_zip_saves_and_ignores(test_client):
    # login user created in conftest (test@example.com / test1234)
    rv = test_client.post(
        "/login",
        data={"email": "test@example.com", "password": "test1234"},
        follow_redirects=True,
    )
    assert rv.status_code in (200, 302)

    files = {
        "good1.poke": "content1",
        "good2.POKE": "content2",
        "ignore.txt": "nope",
        "../escape.poke": "bad",
    }

    zip_bytes = _make_zip_bytes(files)

    data = {
        "file": (io.BytesIO(zip_bytes), "test.zip"),
    }

    resp = test_client.post("/dataset/zip/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "saved" in body and "ignored" in body

    # saved should contain only the two poke files (case-insensitive)
    assert any(s.lower().endswith("good1.poke") for s in body["saved"])
    assert any(s.lower().endswith("good2.poke") for s in body["saved"])

    # ignored should include ignore.txt and the traversal entry
    assert any("ignore.txt" in ig for ig in body["ignored"])
    assert any(".." in ig or ig.startswith("/") for ig in body["ignored"])

    # Check files exist in uploads/temp/<user.id>
    # derive path via AuthenticationService
    user = UserRepository().get_by_email("test@example.com")
    temp_folder = AuthenticationService().temp_folder_by_user(user)

    try:
        for saved_name in body["saved"]:
            assert os.path.exists(os.path.join(temp_folder, saved_name))
    finally:
        # cleanup
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)


def test_import_from_github_with_mocked_zip(monkeypatch, test_client):
    # login
    rv = test_client.post(
        "/login",
        data={"email": "test@example.com", "password": "test1234"},
        follow_redirects=True,
    )
    assert rv.status_code in (200, 302)

    # Create a fake repo zip with a root folder and a subdir
    files = {
        "rootdir/path/good.poke": "ok",
        "rootdir/path/readme.md": "md",
        "rootdir/other/ignored.txt": "no",
    }
    zip_bytes = _make_zip_bytes(files)

    class DummyResp:
        status_code = 200

        def __init__(self, content):
            self.content = content

    def fake_get(url, timeout=60):
        return DummyResp(zip_bytes)

    monkeypatch.setattr("requests.get", fake_get)

    payload = {"repo_url": "https://github.com/owner/repo", "branch": "main", "subdir": "path"}
    resp = test_client.post("/dataset/github/import", json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "saved" in body and "ignored" in body
    # only good.poke should be saved
    assert any(s.endswith("good.poke") for s in body["saved"])

    # cleanup temp folder
    user = UserRepository().get_by_email("test@example.com")
    temp_folder = AuthenticationService().temp_folder_by_user(user)
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)


@pytest.fixture
def dataset_with_comment(feedback_user, feedback_dataset):
    """Añade un comentario preexistente al dataset."""
    comment = DSComment(content="Initial test comment", user_id=feedback_user.id, dataset_id=feedback_dataset.id)
    db.session.add(comment)
    db.session.commit()
    return comment


def test_add_comment_success(test_client, feedback_user, feedback_dataset):
    """
    Prueba añadir un comentario interceptando el servicio para que encuentre el dataset.
    """
    login(test_client, feedback_user.email, "password")

    with patch("app.modules.dataset.routes.dataset_service.get_or_404") as mock_get:
        mock_get.return_value = feedback_dataset

        response = test_client.post(
            f"/dataset/{feedback_dataset.id}/comment",
            data={"content": "This is a great dataset!", "submit": "Add comment"},
            follow_redirects=False,
        )
    assert response.status_code == 302
    comment = DSComment.query.filter_by(content="This is a great dataset!").first()
    assert comment is not None
    assert comment.dataset_id == feedback_dataset.id

    logout(test_client)


def test_delete_comment_by_author(test_client, feedback_user, feedback_dataset, dataset_with_comment):
    login(test_client, feedback_user.email, "password")

    with patch("app.modules.dataset.routes.dataset_service.get_or_404") as mock_get:
        mock_get.return_value = feedback_dataset

        response = test_client.post(
            f"/dataset/{feedback_dataset.id}/comment/{dataset_with_comment.id}/delete", follow_redirects=False
        )

    assert response.status_code == 302
    after = DSComment.query.get(dataset_with_comment.id)
    assert after is None
    logout(test_client)


def test_delete_comment_by_dataset_owner(test_client, feedback_user, feedback_dataset):

    other_email = f"other_{uuid.uuid4()}@example.com"
    other_user = User(email=other_email, password="password")
    db.session.add(other_user)
    db.session.commit()
    comment = DSComment(content="Spam", user_id=other_user.id, dataset_id=feedback_dataset.id)
    db.session.add(comment)
    db.session.commit()

    login(test_client, feedback_user.email, "password")

    with patch("app.modules.dataset.routes.dataset_service.get_or_404") as mock_get:
        mock_get.return_value = feedback_dataset

        response = test_client.post(
            f"/dataset/{feedback_dataset.id}/comment/{comment.id}/delete", follow_redirects=False
        )

    assert response.status_code == 302
    after = DSComment.query.get(comment.id)
    assert after is None
    logout(test_client)
