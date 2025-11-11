import pytest

from app import db
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.conftest import login, logout


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():

        user= User(email="user@example.com", password="test1234")
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(user_id=user.id, name="Nombre", surname="Apellido")
        db.session.add(profile)
        db.session.commit()

        meta_draft = DSMetaData(
            title="Draft dataset",
            description="Un dataset en modo borrador.",
            publication_type=PublicationType.OTHER
        )
        meta_final = DSMetaData(
            title="Published dataset",
            description="Un dataset publicado.",
            publication_type=PublicationType.OTHER
        )
        db.session.add_all([meta_draft, meta_final])
        db.session.commit()

        draft_dataset = DataSet(
            user_id=user.id,
            ds_meta_data_id=meta_draft.id,
            draft_mode=True
        )
        final_dataset = DataSet(
            user_id=user.id,
            ds_meta_data_id=meta_final.id,
            draft_mode=False
        )
        db.session.add_all([draft_dataset, final_dataset])
        db.session.commit()

    yield test_client


#Test 1: crear dataset en modo draft. Successfull.
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

#Test 1: crear dataset en modo draft sin titulo. Unsuccessfull.
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

    assert "introduce un título" in json_data["message"].lower(), \
        "Missing error title message."

    logout(test_client)


#Test 3: editar dataset en modo draft. Successfull.
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


#Test 4: editar dataset publicado. Unsuccessfull.
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


#Test 5: acceder formulario de edición de dataset en draft. Successful.
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
