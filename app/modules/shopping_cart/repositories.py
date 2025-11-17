from typing import Optional

from app.modules.shopping_cart.models import ShoppingCart, ShoppingCartItem
from core.repositories.BaseRepository import BaseRepository


class ShoppingCartRepository(BaseRepository):
    def __init__(self):
        super().__init__(ShoppingCart)

    def find_by_user_id(self, user_id: int) -> Optional[ShoppingCart]:
        return self.model.query.filter_by(user_id=user_id).first()


class ShoppingCartItemRepository(BaseRepository):
    def __init__(self):
        super().__init__(ShoppingCartItem)

    def find_by_cart_and_file(self, cart_id: int, file_id: int) -> Optional[ShoppingCartItem]:
        return self.model.query.filter_by(shopping_cart_id=cart_id, file_id=file_id).first()

    def get_all_by_cart_id(self, cart_id: int):
        """
        Retrieves all items associated with a given cart ID.
        """
        return self.model.query.filter_by(shopping_cart_id=cart_id).all()
