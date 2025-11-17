from app.modules.auth.models import User
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.services import HubfileService
from app.modules.shopping_cart.models import ShoppingCart, ShoppingCartItem
from app.modules.shopping_cart.repositories import ShoppingCartItemRepository, ShoppingCartRepository
from core.services.BaseService import BaseService


class ShoppingCartService(BaseService):
    def __init__(self):
        super().__init__(ShoppingCartRepository())
        self.hubfile_service = HubfileService()
        self.shopping_cart_item_repository = ShoppingCartItemRepository()

    def get_cart_by_user(self, user: User) -> ShoppingCart:
        """
        Retrieves the shopping cart for a given user. If it doesn't exist, it creates one.
        """
        shopping_cart = self.repository.find_by_user_id(user.id)
        return shopping_cart

    def add_item_to_cart(self, shopping_cart: ShoppingCart, hubfile: Hubfile) -> ShoppingCartItem | None:
        """
        Adds a hubfile to the shopping cart if it's not already there.
        Returns the new item, or None if it already existed.
        """
        item_exists = self.shopping_cart_item_repository.find_by_cart_and_file(shopping_cart.id, hubfile.id)

        if not item_exists:
            new_item = self.shopping_cart_item_repository.create(shopping_cart_id=shopping_cart.id, file_id=hubfile.id)
            return new_item

        return None

    def remove_item_from_cart(self, shopping_cart: ShoppingCart, hubfile: Hubfile) -> bool:
        """
        Removes a hubfile from the shopping cart.
        Returns True if the item was found and removed, False otherwise.
        """
        item_to_remove = self.shopping_cart_item_repository.find_by_cart_and_file(shopping_cart.id, hubfile.id)

        if item_to_remove:
            self.shopping_cart_item_repository.delete(item_to_remove.id)
            return True

        return False

    def clear_cart(self, shopping_cart: ShoppingCart):
        """
        Removes all items from the given shopping cart.
        """
        all_items = self.shopping_cart_item_repository.get_all_by_cart_id(shopping_cart.id)
        for item in all_items:
            self.shopping_cart_item_repository.delete(item.id)
        return True


class ShoppingCartItemService(BaseService):
    def __init__(self):
        super().__init__(ShoppingCartItemRepository())
