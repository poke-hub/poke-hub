from app import db


class ShoppingCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    items = db.relationship("ShoppingCartItem", backref="shopping_cart", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"ShoppingCart<{self.id}>"


class ShoppingCartItem(db.Model):
    __table_args__ = (db.UniqueConstraint("shopping_cart_id", "file_id", name="uc_cart_item"),)
    id = db.Column(db.Integer, primary_key=True)
    shopping_cart_id = db.Column(db.Integer, db.ForeignKey("shopping_cart.id", ondelete="CASCADE"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("file.id", ondelete="CASCADE"), nullable=False)
