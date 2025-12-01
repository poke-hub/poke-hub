import pytest
from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.hubfile.models import Hubfile
from app.modules.pokemodel.models import PokeModel, FMMetaData
from app.modules.shopping_cart.models import ShoppingCart
from app.modules.shopping_cart.repositories import ShoppingCartRepository


@pytest.fixture(scope="module")
def shopping_cart_integration_seed(test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()

        ds_meta = DSMetaData(title="Integration Test DS", description="Desc prueba", publication_type=PublicationType.NONE)
        db.session.add(ds_meta)
        db.session.flush()

        dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)
        db.session.flush()

        fm_meta = FMMetaData(
            poke_filename="integration.poke",
            title="Integration FM",
            description="Desc FM",
            publication_type=PublicationType.NONE,
            tags="tag1,tag2"
        )
        db.session.add(fm_meta)
        db.session.flush()

        pm = PokeModel(data_set_id=dataset.id, fm_meta_data_id=fm_meta.id)
        db.session.add(pm)
        db.session.flush()

        hubfile = Hubfile(name="integration_file.txt", checksum="abc123456", size=123, poke_model_id=pm.id)
        db.session.add(hubfile)
        db.session.commit()

        cart_repo = ShoppingCartRepository()
        if not cart_repo.find_by_user_id(user.id):
            cart_repo.create(user_id=user.id)

    yield


def login(client, email, password):
    return client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)


def test_shopping_cart_full_flow(test_client, shopping_cart_integration_seed):
    """
    Test a complete user flow:
    1. Login
    2. Check empty cart
    3. Add item
    4. Verify item in cart
    5. Download cart
    6. Remove item
    7. Verify empty cart
    """
    login(test_client, "test@example.com", "test1234")

    with test_client.application.app_context():
        hubfile = Hubfile.query.filter_by(name="integration_file.txt").first()
        hubfile_id = hubfile.id
        
        import os
        dataset = DataSet.query.get(hubfile.poke_model.data_set_id)
        file_path = os.path.join(
            os.getenv("WORKING_DIR", ""),
            "uploads",
            f"user_{dataset.user_id}",
            f"dataset_{dataset.id}",
            hubfile.name,
        )
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("dummy content")

    resp = test_client.get("/shopping_cart")
    assert resp.status_code == 200

    resp = test_client.get(f"/add_to_cart/{hubfile_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert "added to your cart" in resp.data.decode("utf-8")

    resp = test_client.get("/shopping_cart")
    assert resp.status_code == 200
    assert "integration_file.txt" in resp.data.decode("utf-8")

    resp = test_client.get("/shopping_cart/download")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"

    resp = test_client.get(f"/remove_from_cart/{hubfile_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert "removed from your cart" in resp.data.decode("utf-8")

    resp = test_client.get("/shopping_cart")
    assert resp.status_code == 200
    assert "integration_file.txt" not in resp.data.decode("utf-8")


def test_clear_cart_flow(test_client, shopping_cart_integration_seed):
    """
    Test clearing the cart:
    1. Login
    2. Add item
    3. Clear cart
    4. Verify empty
    """
    login(test_client, "test@example.com", "test1234")

    with test_client.application.app_context():
        hubfile = Hubfile.query.filter_by(name="integration_file.txt").first()
        hubfile_id = hubfile.id

    test_client.get(f"/add_to_cart/{hubfile_id}", follow_redirects=True)

    resp = test_client.get("/clear_cart", follow_redirects=True)
    assert resp.status_code == 200
    assert "cart has been cleared" in resp.data.decode("utf-8")

    resp = test_client.get("/shopping_cart")
    assert "integration_file.txt" not in resp.data.decode("utf-8")
