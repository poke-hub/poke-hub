import pytest
from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.hubfile.models import Hubfile
from app.modules.pokemodel.models import PokeModel, FMMetaData
from app.modules.shopping_cart.models import ShoppingCart
from app.modules.shopping_cart.services import ShoppingCartService
from app.modules.shopping_cart.repositories import ShoppingCartRepository


@pytest.fixture(scope="module")
def shopping_cart_seed(test_client):
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()

        # Create a dataset and pokemodel and hubfile if they don't exist
        ds_meta = DSMetaData(title="Test DS", description="Desc prueba", publication_type=PublicationType.NONE)
        db.session.add(ds_meta)
        db.session.flush()

        dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)
        db.session.flush()

        fm_meta = FMMetaData(
            poke_filename="test.poke",
            title="Test FM",
            description="Desc FM",
            publication_type=PublicationType.NONE,
            tags="tag1,tag2"
        )
        db.session.add(fm_meta)
        db.session.flush()

        pm = PokeModel(data_set_id=dataset.id, fm_meta_data_id=fm_meta.id)
        db.session.add(pm)
        db.session.flush()

        hubfile = Hubfile(name="file1.txt", checksum="abc12345", size=123, poke_model_id=pm.id)
        db.session.add(hubfile)
        db.session.commit()

        # Ensure cart exists for user
        cart_repo = ShoppingCartRepository()
        if not cart_repo.find_by_user_id(user.id):
            cart_repo.create(user_id=user.id)

    yield


def login(client, email, password):
    return client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def test_shopping_cart_index(test_client, shopping_cart_seed):
    login(test_client, "test@example.com", "test1234")
    resp = test_client.get("/shopping_cart")
    assert resp.status_code == 200


def test_add_to_cart(test_client, shopping_cart_seed):
    login(test_client, "test@example.com", "test1234")
    with test_client.application.app_context():
        hubfile = Hubfile.query.first()
        hubfile_id = hubfile.id

    resp = test_client.get(f"/add_to_cart/{hubfile_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert "added to your cart" in resp.data.decode("utf-8")


def test_remove_from_cart(test_client, shopping_cart_seed):
    login(test_client, "test@example.com", "test1234")
    with test_client.application.app_context():
        hubfile = Hubfile.query.first()
        hubfile_id = hubfile.id

        # Ensure it's in the cart first
        user = User.query.filter_by(email="test@example.com").first()
        svc = ShoppingCartService()
        cart = svc.get_cart_by_user(user)
        svc.add_item_to_cart(cart, hubfile)

    resp = test_client.get(f"/remove_from_cart/{hubfile_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert "removed from your cart" in resp.data.decode("utf-8")


def test_clear_cart(test_client, shopping_cart_seed):
    login(test_client, "test@example.com", "test1234")
    with test_client.application.app_context():
        hubfile = Hubfile.query.first()
        user = User.query.filter_by(email="test@example.com").first()
        svc = ShoppingCartService()
        cart = svc.get_cart_by_user(user)
        svc.add_item_to_cart(cart, hubfile)

    resp = test_client.get("/clear_cart", follow_redirects=True)
    assert resp.status_code == 200
    assert "cart has been cleared" in resp.data.decode("utf-8")


def test_download_cart(test_client, shopping_cart_seed):
    login(test_client, "test@example.com", "test1234")
    with test_client.application.app_context():
        hubfile = Hubfile.query.first()
        user = User.query.filter_by(email="test@example.com").first()
        svc = ShoppingCartService()
        cart = svc.get_cart_by_user(user)
        svc.add_item_to_cart(cart, hubfile)
        db.session.commit()

        # Ensure file exists on disk for download
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

    # Force session cleanup to ensure next request sees committed data
    db.session.remove()

    resp = test_client.get("/shopping_cart/download")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"


def test_get_cart_by_user(test_client, shopping_cart_seed):
    """Verifica que se recupera el carrito asociado al usuario"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        svc = ShoppingCartService()
        cart = svc.get_cart_by_user(user)
        assert cart is not None
        assert cart.user_id == user.id


def test_add_and_remove_item_from_cart_service(test_client, shopping_cart_seed):
    """Prueba añadir un ítem (una sola vez) y eliminarlo correctamente usando el servicio"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        cart = ShoppingCart.query.filter_by(user_id=user.id).first()
        hubfile = Hubfile.query.first()

        svc = ShoppingCartService()

        # Ensure clean state
        svc.clear_cart(cart)

        new_item = svc.add_item_to_cart(cart, hubfile)
        assert new_item is not None

        duplicate = svc.add_item_to_cart(cart, hubfile)
        assert duplicate is None

        removed = svc.remove_item_from_cart(cart, hubfile)
        assert removed is True

        removed_again = svc.remove_item_from_cart(cart, hubfile)
        assert removed_again is False


def test_clear_cart_removes_all_items_service(test_client, shopping_cart_seed):
    """Verifica que clear_cart elimina todos los ítems del carrito usando el servicio"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        cart = ShoppingCart.query.filter_by(user_id=user.id).first()
        fm = PokeModel.query.first()

        hubfile1 = Hubfile.query.first()
        hubfile2 = Hubfile(name="file2", checksum="def456", size=456, poke_model_id=fm.id)
        db.session.add(hubfile2)
        db.session.commit()

        svc = ShoppingCartService()

        svc.add_item_to_cart(cart, hubfile1)
        svc.add_item_to_cart(cart, hubfile2)

        assert len(cart.items) == 2

        svc.clear_cart(cart)

        assert len(cart.items) == 0


def test_shopping_cart_index_requires_login(test_client):
    """Acceder a la vista del carrito sin sesión debe redirigir al login."""
    logout(test_client)
    response = test_client.get("/shopping_cart")
    assert response.status_code == 302
    assert "/login" in response.location


def test_add_to_cart_requires_login(test_client):
    """Intentar añadir al carrito sin sesión debe redirigir al login."""
    logout(test_client)
    response = test_client.get("/add_to_cart/1")
    assert response.status_code == 302
    assert "/login" in response.location


def test_remove_from_cart_requires_login(test_client):
    """Intentar eliminar del carrito sin sesión debe redirigir al login."""
    logout(test_client)
    response = test_client.get("/remove_from_cart/1")
    assert response.status_code == 302
    assert "/login" in response.location


def test_clear_cart_requires_login(test_client):
    """Intentar limpiar el carrito sin sesión debe redirigir al login."""
    logout(test_client)
    response = test_client.get("/clear_cart")
    assert response.status_code == 302
    assert "/login" in response.location
