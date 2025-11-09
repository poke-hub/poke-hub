import pytest

from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app import db
from app.modules.auth.models import User

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
        assert actualizado.download_count == inicial + num_descargas, (
            f"download_count esperado {inicial + num_descargas}, obtenido {actualizado.download_count}"
        )
    
    