import json
from datetime import datetime

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData


@pytest.fixture(scope="module")
def database_seed(test_client):
    with test_client.application.app_context():
        author1 = Author.query.get(1)
        author2 = Author.query.get(2)
        if author1 is None:
            author1 = Author(id=1, name="Author 1")
            db.session.add(author1)
        if author2 is None:
            author2 = Author(id=2, name="Author 2")
            db.session.add(author2)
        user = User.query.get(3)
        if user is None:
            user = User(id=3, email="tester@example.com", password="test1234", created_at=datetime.utcnow())
            db.session.add(user)
        db.session.flush()
        ds_meta_data1 = DSMetaData(
            id=33333,
            title="Dataset Alpha",
            description="A test dataset",
            publication_type=PublicationType.BOOK,
            tags="Fighting",
            dataset_doi="10.1234/alpha",
            authors=[author1],
        )
        db.session.add(ds_meta_data1)
        ds_meta_data2 = DSMetaData(
            id=33337,
            title="Dataset Beta",
            description="Another test dataset",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            tags="Fighting",
            dataset_doi="10.1234/beta",
            authors=[author2],
        )
        db.session.add(ds_meta_data2)
        db.session.flush()
        fm_meta_data1 = FMMetaData(
            id=33334,
            poke_filename="pokefile.poke",
            title="Test FM",
            description="A test FM",
            publication_type=PublicationType.JOURNAL_ARTICLE,
            tags="Competitive",
            authors=[author1],
        )
        db.session.add(fm_meta_data1)
        fm_meta_data2 = FMMetaData(
            id=33338,
            poke_filename="pokefile2.poke",
            title="Test FM 2",
            description="Another test FM",
            publication_type=PublicationType.BOOK,
            tags="Randomlocke",
            authors=[author2],
        )
        db.session.add(fm_meta_data2)
        db.session.flush()
        dataset1 = DataSet(id=33336, ds_meta_data_id=33333, user_id=user.id)
        db.session.add(dataset1)
        dataset2 = DataSet(id=33340, ds_meta_data_id=33337, user_id=user.id)
        db.session.add(dataset2)
        db.session.flush()
        fm1 = FeatureModel(id=33335, fm_meta_data_id=33334, data_set_id=33336)
        db.session.add(fm1)
        fm2 = FeatureModel(id=33339, fm_meta_data_id=33338, data_set_id=33340)
        db.session.add(fm2)
        db.session.flush()

        db.session.commit()


def test_get_explore_page(test_client, database_seed):
    # Test Get

    # WHEN
    response = test_client.get("/explore")

    # VERIFY
    assert response.status_code == 200
    assert b"Explore" in response.data
    assert b"Filter by authors" in response.data
    assert b"Filter by tags" in response.data
    assert b"Author 1" in response.data
    assert b"Author 2" in response.data
    assert b"Fighting" in response.data
    assert b"Competitive" in response.data


# Test Post
@pytest.mark.parametrize(
    "post_data, expected_status, expected_len, expected_title",
    [
        (
            {
                "query": "",
                "sorting": "newest",
                "publication_type": "any",
                "authors_filter": "any",
                "tags_filter": "any",
            },
            200,
            2,
            None,  # Test 1: Sin filtros, debe devolver 2 datasets
        ),
        (
            {
                "query": "Alpha",
                "sorting": "newest",
                "publication_type": "any",
                "authors_filter": "any",
                "tags_filter": "any",
            },
            200,
            1,
            "Dataset Alpha",  # Test 2: Filtrar por query "Alpha"
        ),
        (
            {"query": "", "sorting": "newest", "publication_type": "any", "authors_filter": "2", "tags_filter": "any"},
            200,
            1,
            "Dataset Beta",  # Test 3: Filtrar por Author ID 2
        ),
        (
            {
                "query": "",
                "sorting": "newest",
                "publication_type": "any",
                "authors_filter": "any",
                "tags_filter": "Fighting",
            },
            200,
            2,
            None,  # Test 4: Filtrar por Tag 'Fighting'
        ),
        (
            {
                "query": "",
                "sorting": "newest",
                "publication_type": "book",
                "authors_filter": "any",
                "tags_filter": "any",
            },
            200,
            1,
            "Dataset Alpha",  # Test 5: Filtrar por Publication Type 'book'
        ),
        (
            {
                "query": "",
                "sorting": "newest",
                "publication_type": "any",
                "authors_filter": "1",
                "tags_filter": "Randomlocke",
            },
            200,
            0,
            None,  # Test 6: Filtro cruzado imposible (Author 1 + Randomlocke), debe devolver 0
        ),
        (
            {
                "query": "Beta",
                "sorting": "newest",
                "publication_type": "any",
                "authors_filter": "2",
                "tags_filter": "any",
            },
            200,
            1,
            "Dataset Beta",  # Test 7: Filtro combinado (Query + Author)
        ),
    ],
)
def test_post_explore_filter(test_client, database_seed, post_data, expected_status, expected_len, expected_title):
    # WHEN
    response = test_client.post("/explore", data=json.dumps(post_data), content_type="application/json")

    # VERIFY
    assert response.status_code == expected_status
    assert response.content_type == "application/json"

    response_data = json.loads(response.data)
    assert len(response_data) == expected_len

    if expected_title:
        assert response_data[0]["title"] == expected_title
