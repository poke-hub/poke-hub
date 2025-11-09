import os
from flask import render_template
from flask_login import current_user
from app import db

from app.modules.zenodo import zenodo_bp
from app.modules.zenodo.services import ZenodoService
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from core.configuration.configuration import uploads_folder_name
from flask import redirect, url_for, flash
from app.modules.dataset.models import DataSet


@zenodo_bp.route("/zenodo", methods=["GET"])
def index():
    return render_template("zenodo/index.html")


@zenodo_bp.route("/zenodo/test", methods=["GET"])
def zenodo_test() -> dict:
    service = ZenodoService()
    return service.test_full_connection()

@zenodo_bp.route("/zenodo/publish/<int:dataset_id>", methods=["POST"])
def publish_dataset(dataset_id):
    """
    Esta es la ruta que llama el botón "Publish to Zenodo" de la interfaz.
    """
    service = ZenodoService()
    dataset = DataSet.query.get(dataset_id)

    # Bloque IF 1
    if not dataset:
        flash("Dataset no encontrado.", "danger")
        return redirect('/dataset/list')

    # Bloque IF 2
    if not dataset.feature_models:
         flash("No se puede publicar un dataset sin modelos de características.", "warning")
         return redirect('/dataset/list')

    # El bloque TRY empieza aquí, al mismo nivel que los IF
    try:
        # --- 1. Crear Deposición ---
        deposition_data = service.create_new_deposition(dataset)
        dep_id = deposition_data["id"]

        # --- 2. Subir Ficheros ---
        first_fm = dataset.feature_models[0]
        service.upload_file(dataset, dep_id, first_fm, user=dataset.user)

        # --- 3. Publicar ---
        publish_data = service.publish_deposition(dep_id)

        # --- 4. (¡IMPORTANTE!) Guardar el DOI en la BBDD de uvlhub ---
        dataset.ds_meta_data.dataset_doi = publish_data.get("doi")
        dataset.ds_meta_data.deposition_id = dep_id
        db.session.add(dataset)
        db.session.commit()

        flash(f"¡Publicado con éxito en Zenodo! DOI: {publish_data.get('doi')}", "success")

    # El bloque EXCEPT al mismo nivel
    except Exception as e:
        flash(f"Error al publicar en Zenodo: {str(e)}", "danger")

    # El RETURN final al mismo nivel
    return redirect('/dataset/list')