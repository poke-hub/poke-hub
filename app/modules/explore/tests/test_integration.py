import json
from datetime import datetime

import pytest

from app import db
from app.modules.elasticsearch.services import ElasticsearchService

# Test Get
def test_get_explore_page(test_client):

    # WHEN
    response = test_client.get("/explore")

    # VERIFY ELASTICSEARCH IS UP FOR TESTING
    if response.status_code == 503:
        pytest.skip("Elasticsearch no está disponible (Error 503). Saltando test.")

    # VERIFY INDEX IS READY FOR TESTING
    try:
        es_service = ElasticsearchService()
        if es_service.count_documents() == 0:
            pytest.skip("El índice de Elasticsearch está vacío. Saltando test.")
    except Exception as e:
        pytest.skip(f"Elasticsearch no está disponible (Error: {e}). Saltando test.")

    # VERIFY
    assert response.status_code == 200
    assert b"Explore" in response.data
    assert b"Sort by Date" in response.data
    assert b"Sort by EV count" in response.data
    assert b"Sort by IV count" in response.data
    assert b"Ascending" in response.data
    assert b"Descending" in response.data


# Test Post
@pytest.mark.parametrize(
    "post_data, expected_status, expected_len, expected_title",
    [
        (
            {
                "query": "",
                "sorting": "created_at",
                "desc": "true",
            },
            200,
            4,
            None,  # Test 1: Sin filtros, debe devolver 4 datasets
        ),
        (
            {
                "query": "1",
                "sorting": "created_at",
                "desc": "true",
            },
            200,
            1,
            "Sample dataset 1",  # Test 2: Filtrar por query "1"
        ),
        (
            {
                "query": "tag1",
                "sorting": "created_at",
                "desc": "true",
            },
            200,
            4,
            None,  # Test 3: Buscar Tag 'tag1'
        ),
        (
            {
                "query": "5",
                "sorting": "created_at",
                "desc": "true",
            },
            200,
            1,
            "Sample dataset 1",  # Test 4: Buscar autor 5
        ),
        (
            {
                "query": "alcachofa",
                "sorting": "created_at",
                "desc": "true",
            },
            200,
            0,
            None,  # Test 5: Búsqueda imposible (alcachofa), debe devolver 0
        ),
    ],
)
def test_post_explore_filter(test_client, post_data, expected_status, expected_len, expected_title):
    # WHEN
    response = test_client.post("/explore", data=json.dumps(post_data), content_type="application/json")

    # VERIFY ELASTICSEARCH IS UP FOR TESTING
    if response.status_code == 503:
        pytest.skip("Elasticsearch no está disponible (Error 503). Saltando test.")

    0# VERIFY INDEX IS READY FOR TESTING
    try:
        es_service = ElasticsearchService()
        if es_service.count_documents() == 0:
            pytest.skip("El índice de Elasticsearch está vacío. Saltando test.")
    except Exception as e:
        pytest.skip(f"Elasticsearch no está disponible (Error: {e}). Saltando test.")

    # VERIFY
    assert response.status_code == expected_status
    assert response.content_type == "application/json"

    response_data = json.loads(response.data)
    assert len(response_data) == expected_len

    if expected_title:
        assert response_data[0]["title"] == expected_title
