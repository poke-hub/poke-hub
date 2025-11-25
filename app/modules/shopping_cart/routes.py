import os
import tempfile
from zipfile import ZipFile

from flask import flash, make_response, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet
from app.modules.hubfile.services import HubfileService
from app.modules.pokemodel.models import PokeModel
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


@shopping_cart_bp.route("/shopping_cart/download", methods=["GET"])
@login_required
def download_cart():
    shopping_cart_service = ShoppingCartService()
    shopping_cart = shopping_cart_service.get_cart_by_user(current_user)

    if not shopping_cart or not shopping_cart.items:
        flash("Your shopping cart is empty.", "warning")
        return redirect(url_for("shopping_cart.index"))

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "poke_hub_cart.zip")

    with ZipFile(zip_path, "w") as zipf:
        for item in shopping_cart.items:
            hubfile = item.file
            poke_model = PokeModel.query.get(hubfile.poke_model_id)
            if not poke_model:
                continue

            dataset = DataSet.query.get(poke_model.data_set_id)
            if not dataset:
                continue

            file_path = os.path.join(
                os.getenv("WORKING_DIR", ""),
                "uploads",
                f"user_{dataset.user_id}",
                f"dataset_{dataset.id}",
                hubfile.name,
            )

            if os.path.exists(file_path):
                zipf.write(file_path, arcname=hubfile.name)

    resp = make_response(
        send_from_directory(temp_dir, "poke_hub_cart.zip", as_attachment=True, mimetype="application/zip")
    )

    # Aquí podrías añadir lógica para registrar la descarga si fuese necesario.

    return resp
