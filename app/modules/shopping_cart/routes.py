from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.modules.auth.services import AuthenticationService
from app.modules.hubfile.services import HubfileService
from app.modules.shopping_cart import shopping_cart_bp
from app.modules.shopping_cart.services import ShoppingCartService


@shopping_cart_bp.route("/shopping_cart", methods=["GET"])
@login_required
def index():
    auth_service = AuthenticationService()
    shopping_cart_service = ShoppingCartService()

    user = auth_service.get_authenticated_user()
    shopping_cart = shopping_cart_service.get_cart_by_user(user)

    return render_template("shopping_cart/index.html", shopping_cart=shopping_cart)


@shopping_cart_bp.route("/add_to_cart/<int:hubfile_id>", methods=["GET"])
@login_required
def add_to_cart(hubfile_id):
    auth_service = AuthenticationService()
    shopping_cart_service = ShoppingCartService()
    hubfile_service = HubfileService()

    user = auth_service.get_authenticated_user()
    shopping_cart = shopping_cart_service.get_cart_by_user(user)

    hubfile = hubfile_service.get_by_id(hubfile_id)
    if not hubfile:
        flash("File not found.", "danger")
        return redirect(url_for("explore.index"))

    if shopping_cart_service.add_item_to_cart(shopping_cart, hubfile):
        flash(f"'{hubfile.name}' has been added to your cart.", "success")

    return redirect(request.referrer or url_for("explore.index"))


@shopping_cart_bp.route("/remove_from_cart/<int:hubfile_id>", methods=["GET"])
@login_required
def remove_from_cart(hubfile_id):
    auth_service = AuthenticationService()
    shopping_cart_service = ShoppingCartService()
    hubfile_service = HubfileService()

    user = auth_service.get_authenticated_user()
    shopping_cart = shopping_cart_service.get_cart_by_user(user)

    hubfile = hubfile_service.get_by_id(hubfile_id)
    if not hubfile:
        flash("File not found.", "danger")
        return redirect(url_for("shopping_cart.index"))

    if shopping_cart_service.remove_item_from_cart(shopping_cart, hubfile):
        flash(f"'{hubfile.name}' has been removed from your cart.", "success")

    return redirect(url_for("shopping_cart.index"))


@shopping_cart_bp.route("/clear_cart", methods=["GET"])
@login_required
def clear_cart():
    auth_service = AuthenticationService()
    shopping_cart_service = ShoppingCartService()

    user = auth_service.get_authenticated_user()
    shopping_cart = shopping_cart_service.get_cart_by_user(user)

    if shopping_cart:
        shopping_cart_service.clear_cart(shopping_cart)
        flash("Your shopping cart has been cleared.", "success")

    return redirect(url_for("shopping_cart.index"))
