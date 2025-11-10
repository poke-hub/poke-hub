import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
from app.modules.shopping_cart.models import ShoppingCart
from app.modules.shopping_cart.repositories import ShoppingCartItemRepository, ShoppingCartRepository
from app.modules.shopping_cart.services import ShoppingCartService


@pytest.fixture(scope="module")
def test_client(test_client):

    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()

        ds_meta = DSMetaData(title="Test DS", description="Desc prueba", publication_type=PublicationType.NONE)
        db.session.add(ds_meta)
        db.session.commit()

        dataset = DataSet(user_id=user.id, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)
        db.session.commit()

        fm = FeatureModel(data_set_id=dataset.id)
        db.session.add(fm)
        db.session.commit()

        hubfile = Hubfile(name="file1", checksum="abc123", size=123, feature_model_id=fm.id)
        db.session.add(hubfile)
        db.session.commit()

        cart_repo = ShoppingCartRepository()
        cart_repo.create(user_id=user.id)

    yield test_client


def test_get_cart_by_user(test_client):
    """Verifica que se recupera el carrito asociado al usuario"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        svc = ShoppingCartService()
        cart = svc.get_cart_by_user(user)
        assert cart is not None
        assert cart.user_id == user.id


def test_add_and_remove_item_from_cart(test_client):
    """Prueba añadir un ítem (una sola vez) y eliminarlo correctamente"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        cart = ShoppingCart.query.filter_by(user_id=user.id).first()
        hubfile = Hubfile.query.first()

        svc = ShoppingCartService()
        item_repo = ShoppingCartItemRepository()

        items_before = item_repo.get_all_by_cart_id(cart.id)
        assert items_before == []

        new_item = svc.add_item_to_cart(cart, hubfile)
        assert new_item is not None

        duplicate = svc.add_item_to_cart(cart, hubfile)
        assert duplicate is None

        removed = svc.remove_item_from_cart(cart, hubfile)
        assert removed is True

        removed_again = svc.remove_item_from_cart(cart, hubfile)
        assert removed_again is False


def test_clear_cart_removes_all_items(test_client):
    """Verifica que clear_cart elimina todos los ítems del carrito"""
    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        cart = ShoppingCart.query.filter_by(user_id=user.id).first()
        fm = FeatureModel.query.first()

        hubfile1 = Hubfile.query.first()
        hubfile2 = Hubfile(name="file2", checksum="def456", size=456, feature_model_id=fm.id)
        db.session.add(hubfile2)
        db.session.commit()

        svc = ShoppingCartService()
        item_repo = ShoppingCartItemRepository()

        svc.add_item_to_cart(cart, hubfile1)
        svc.add_item_to_cart(cart, hubfile2)

        items = item_repo.get_all_by_cart_id(cart.id)
        assert len(items) == 2

        svc.clear_cart(cart)

        items_after = item_repo.get_all_by_cart_id(cart.id)
        assert items_after == []


def test_shopping_cart_index_requires_login(test_client):
    """Acceder a la vista del carrito sin sesión debe redirigir al login."""
    response = test_client.get("/shopping_cart")
    assert response.status_code == 302
    assert "/login" in response.location


def test_add_to_cart_requires_login(test_client):
    """Intentar añadir al carrito sin sesión debe redirigir al login."""
    response = test_client.get("/add_to_cart/1")
    assert response.status_code == 302
    assert "/login" in response.location


def test_remove_from_cart_requires_login(test_client):
    """Intentar eliminar del carrito sin sesión debe redirigir al login."""
    response = test_client.get("/remove_from_cart/1")
    assert response.status_code == 302
    assert "/login" in response.location


def test_clear_cart_requires_login(test_client):
    """Intentar limpiar el carrito sin sesión debe redirigir al login."""
    response = test_client.get("/clear_cart")
    assert response.status_code == 302
    assert "/login" in response.location
