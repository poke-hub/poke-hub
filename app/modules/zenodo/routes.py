from elasticsearch.exceptions import NotFoundError as ElasticsearchConnectionError
from elasticsearch.exceptions import ApiError as ElasticsearchNewConnectionError
from flask import flash, redirect, render_template

from app import db
from app.modules.dataset.models import DataSet
from app.modules.elasticsearch.services import ElasticsearchService
from app.modules.zenodo import zenodo_bp
from app.modules.zenodo.services import ZenodoService

zenodo_service = ZenodoService()


@zenodo_bp.route("/zenodo", methods=["GET"])
def index():
    return render_template("zenodo/index.html")


@zenodo_bp.route("/zenodo/publish/<int:dataset_id>", methods=["POST"])
def publish_dataset(dataset_id):

    dataset = DataSet.query.get(dataset_id)

    if not dataset.poke_models:
        flash("Dataset no encontrado.", "danger")
        return redirect("/dataset/list")

    if not dataset.poke_models:
        flash("No se puede publicar un dataset sin modelos de características.", "warning")
        return redirect("/dataset/list")

    try:
        if dataset.ds_meta_data and dataset.ds_meta_data.deposition_id:
            dep_id = dataset.ds_meta_data.deposition_id

            flash(f"El dataset ya tiene una deposición (ID: {dep_id}). Intentando actualizar.", "info")
        else:
            deposition_data = zenodo_service.create_new_deposition(dataset)
            dep_id = deposition_data["id"]

        for poke_model in dataset.poke_models:
            zenodo_service.upload_file(dataset, dep_id, poke_model, user=dataset.user)

        publish_data = zenodo_service.publish_deposition(dep_id)

        dataset.ds_meta_data.dataset_doi = publish_data.get("doi")
        dataset.ds_meta_data.deposition_id = dep_id
        db.session.add(dataset.ds_meta_data)
        db.session.commit()

        flash(f"¡Publicado/Actualizado con éxito en Zenodo/Fakenodo! DOI: {publish_data.get('doi')}", "success")

        updated_dataset = DataSet.query.get(dataset_id)

        es_service = ElasticsearchService()
        es_service.index_document(dataset_id, updated_dataset.to_indexed())

    except ElasticsearchConnectionError:
        flash(
            "Elasticsearch service is unavailable. Please contact with your project manager if you need the service.",
            "warning",
        )
    except ValueError:
        flash(
            "Elasticsearch service is unavailable. Please contact with your project manager if you need the service.",
            "warning",
        )
    except ElasticsearchNewConnectionError:
        flash(
            "Elasticsearch service is unavailable. Please contact with your project manager if you need the service.",
            "warning",
        )
    except Exception as e:
        flash(f"Error al publicar en Zenodo/Fakenodo: {str(e)}", "danger")

    return redirect("/dataset/list")
