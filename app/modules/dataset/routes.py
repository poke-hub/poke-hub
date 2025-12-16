import io
import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from zipfile import ZipFile

import requests
from flask import abort, flash, jsonify, make_response, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import FileStorage

from app import db
from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetCommentForm, DataSetForm
from app.modules.dataset.models import DSComment, DSDownloadRecord
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.pokemodel.models import PokeModel
from app.modules.pokemodel.repositories import PokeModelRepository
from app.modules.pokemon_check.check_poke import PokemonSetChecker
from app.modules.shopping_cart.services import ShoppingCartService
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        # ¿Guardar borrador?
        save_as_draft = request.form.get("save_as_draft") in ("1", "true", "True")
        # Si NO es borrador, mantenemos tu validación actual
        if not save_as_draft and not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        if save_as_draft:
            title = request.form.get("title", "").strip()
            if not title:
                return jsonify({"message": "Para guardar como borrador, introduce un título."}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(
                form=form, current_user=current_user, draft_mode=True if save_as_draft else False
            )
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_poke_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        if save_as_draft:
            return (
                jsonify(
                    {
                        "message": "Draft saved",
                        "redirect": f"/dataset/unsynchronized/{dataset.id}/",
                        "dataset_id": dataset.id,
                    }
                ),
                200,
            )

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each poke model (one poke model = one request to Zenodo)
                for poke_model in dataset.poke_models:
                    zenodo_service.upload_file(dataset, deposition_id, poke_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload poke models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 400

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/<int:dataset_id>/edit", methods=["GET", "POST"])
@login_required
def edit_dataset(dataset_id):
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)
    if not dataset:
        abort(404)

    # Solo permitir edición si es draft
    if not dataset.draft_mode:
        abort(400, "Only draft datasets can be edited.")

    form = DataSetForm()

    save_as_draft = request.form.get("save_as_draft") in ("1", "true", "True")
    if save_as_draft:
        title = request.form.get("title", "").strip()
        if not title:
            return render_template(
                "dataset/upload_dataset.html",
                dataset=dataset,
                form=form,
                editing=True,
                error="Para guardar como borrador, introduce un título.",
            )

    # --- Pre-rellenar datos al entrar ---
    if request.method == "GET":
        form.title.data = dataset.ds_meta_data.title
        form.desc.data = dataset.ds_meta_data.description
        form.publication_type.data = (
            dataset.ds_meta_data.publication_type.value if dataset.ds_meta_data.publication_type else None
        )
        form.publication_doi.data = dataset.ds_meta_data.publication_doi
        form.tags.data = dataset.ds_meta_data.tags

    # --- Guardar cambios ---
    if request.method == "POST":

        save_as_draft = request.form.get("save_as_draft", "0") in ("1", "true", "True")

        has_new_fms = any(key.startswith("poke_models-") for key in request.form.keys())
        existing_fm_count = len(dataset.poke_models)

        if not save_as_draft:
            if not has_new_fms and existing_fm_count == 0:
                return render_template(
                    "dataset/upload_dataset.html",
                    dataset=dataset,
                    form=form,
                    editing=True,
                    error="You must add at least one POKE model before uploading the dataset.",
                )

        if not save_as_draft and has_new_fms:
            if not form.validate_on_submit():
                return render_template(
                    "dataset/upload_dataset.html", dataset=dataset, form=form, editing=True, error="Invalid form data."
                )

        if not save_as_draft and not has_new_fms:
            title = (form.title.data or "").strip()
            desc = (form.desc.data or "").strip()
            if len(title) < 3 or len(desc) < 3:
                return render_template(
                    "dataset/upload_dataset.html",
                    dataset=dataset,
                    form=form,
                    editing=True,
                    error="Title and description must have at least 3 characters.",
                )

        pub_type = form.publication_type.data or "none"

        try:
            # Actualizar los metadatos del dataset
            dataset_service.update_dsmetadata(
                dataset.ds_meta_data_id,
                title=form.title.data,
                description=form.desc.data,
                publication_type=pub_type,
                publication_doi=form.publication_doi.data,
                tags=form.tags.data,
            )

            dataset_service.append_feature_models_from_form(dataset, form, current_user)

            # Actualizar el dataset (por ejemplo, mantenerlo en modo borrador)
            dataset_service.update(dataset.id, draft_mode=save_as_draft)

            if not save_as_draft:
                dataset_service.move_poke_models(dataset)

            msg = "Draft updated successfully!"
            logger.info(msg)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"message": msg, "id": dataset.id}), 200

            return redirect(url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id))

        except Exception as exc:
            logger.exception(f"Error editing draft dataset {dataset.id}: {exc}")
            return render_template(
                "dataset/upload_dataset.html", dataset=dataset, form=form, editing=True, error=str(exc)
            )

    # Renderizar la misma plantilla del upload, pero en modo edición
    return render_template("dataset/upload_dataset.html", form=form, dataset=dataset, editing=True)


@dataset_bp.route("/dataset/<int:dataset_id>/featuremodel/<int:fm_id>/delete", methods=["POST"])
@login_required
def delete_existing_feature_model(dataset_id, fm_id):
    # 1) Cargar dataset y comprobar que es del usuario + está en draft
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)
    if not dataset:
        abort(404, description="Dataset not found or not owned by current user")
    if not dataset.draft_mode:
        abort(400, description="Only draft datasets can be edited")

    # 2) Cargar PokeModel y verificar que pertenece al dataset
    fm_repo = PokeModelRepository()
    fm: PokeModel = fm_repo.get_or_404(fm_id)
    if fm.data_set_id != dataset.id:
        abort(403, description="PokeModel does not belong to this dataset")

    # 3) Borrar ficheros físicos en uploads/user_{uid}/dataset_{did}/

    working_dir = os.getenv("WORKING_DIR", "")
    uploads_dir = os.path.join(
        working_dir,
        "uploads",
        f"user_{dataset.user_id}",
        f"dataset_{dataset.id}",
    )
    try:
        for file in list(fm.files):  # Hubfile
            file_path = os.path.join(uploads_dir, file.name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    # si falla el remove físico, seguimos (el cascade borrará en DB)
                    pass

        fm_repo.delete(fm_id)
        return jsonify({"ok": True, "message": "Feature model deleted"}), 200
    except Exception as exc:
        logger.exception(f"Error deleting feature model {fm_id} from dataset {dataset_id}: {exc}")
        return jsonify({"ok": False, "message": "Error deleting feature model"}), 500


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file: FileStorage = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".poke"):
        return jsonify({"message": "No valid file"}), 400

    # Read content and validate format before saving
    try:
        file_content = file.read().decode("utf-8")
        file.seek(0)  # IMPORTANT: Reset stream so file.save() can read it later
        checker = PokemonSetChecker(file_content)
        if not checker.is_valid():
            return jsonify({"message": "Invalid .poke file format", "errors": checker.get_errors()}), 400
    except Exception as e:
        return jsonify({"message": f"Error reading or validating file: {e}"}), 500

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "Poke uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


# Upload zip
@dataset_bp.route("/dataset/zip/upload", methods=["POST"])
@login_required
def upload_zip():
    temp_folder = current_user.temp_folder()

    # Validate file
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".zip"):
        return jsonify({"message": "No valid zip"}), 400

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    saved, ignored = [], []

    try:
        with ZipFile(file.stream) as zf:
            for member in zf.infolist():
                name = member.filename

                if member.is_dir():
                    continue

                norm = os.path.normpath(name).replace("\\", "/")

                if norm.startswith("../") or norm.startswith("/"):
                    ignored.append(name)
                    continue

                if not norm.lower().endswith(".poke"):
                    ignored.append(name)
                    continue

                base_filename = os.path.basename(norm)

                base, ext = os.path.splitext(base_filename)
                candidate = base_filename
                dest_path = os.path.join(temp_folder, candidate)
                i = 1
                while os.path.exists(dest_path):
                    candidate = f"{base} ({i}){ext}"
                    dest_path = os.path.join(temp_folder, candidate)
                    i += 1

                with zf.open(member, "r") as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                saved.append(candidate)

    except Exception as e:
        logger.exception("Error while processing ZIP")
        return jsonify({"message": f"Error processing ZIP: {e}"}), 400

    return jsonify({"message": "ZIP processed", "saved": saved, "ignored": ignored}), 200


# Import from GitHub
@dataset_bp.route("/dataset/github/import", methods=["POST"])
@login_required
def import_from_github():

    payload = request.get_json(silent=True) or {}
    repo_url = (payload.get("repo_url") or "").strip()
    branch = (payload.get("branch") or "main").strip()
    subdir = (payload.get("subdir") or "").strip().strip("/")

    if not repo_url:
        return jsonify({"message": "repo_url is required"}), 400

    try:
        parsed = urlparse(repo_url)
        if "github.com" not in parsed.netloc.lower():
            return jsonify({"message": "Only GitHub URLs are supported"}), 400
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            return jsonify({"message": "Invalid GitHub repo URL"}), 400
        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
    except Exception:
        return jsonify({"message": "Invalid GitHub repo URL"}), 400

    archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"

    # ZIP Download
    try:
        resp = requests.get(archive_url, timeout=60)
        if resp.status_code != 200:
            return jsonify({"message": f"GitHub returned {resp.status_code}"}), 400
        zip_bytes = io.BytesIO(resp.content)
    except Exception as e:
        logger.exception("Error downloading GitHub archive")
        return jsonify({"message": f"Error downloading archive: {e}"}), 400

    temp_folder = current_user.temp_folder()
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    saved, ignored = [], []

    try:
        with ZipFile(zip_bytes) as zf:
            prefix = ""
            try:
                first = zf.namelist()[0]
                root = first.split("/")[0] if "/" in first else ""
                if subdir:
                    prefix = f"{root}/{subdir}/"
                else:
                    prefix = f"{root}/" if root else ""
            except Exception:
                prefix = f"{subdir}/" if subdir else ""

            for member in zf.infolist():
                name = member.filename

                if member.is_dir():
                    continue

                if prefix and not name.startswith(prefix):
                    continue

                norm = os.path.normpath(name).replace("\\", "/")
                if norm.startswith("../") or norm.startswith("/"):
                    ignored.append(name)
                    continue

                if not norm.lower().endswith(".poke"):
                    ignored.append(name)
                    continue

                base_filename = os.path.basename(norm)

                base, ext = os.path.splitext(base_filename)
                candidate = base_filename
                dest_path = os.path.join(temp_folder, candidate)
                i = 1
                while os.path.exists(dest_path):
                    candidate = f"{base} ({i}){ext}"
                    dest_path = os.path.join(temp_folder, candidate)
                    i += 1

                with zf.open(member, "r") as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                saved.append(candidate)

    except Exception as e:
        logger.exception("Error processing GitHub ZIP")
        return jsonify({"message": f"Error processing GitHub ZIP: {e}"}), 400

    return jsonify({"message": "GitHub import completed", "saved": saved, "ignored": ignored}), 200


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    dataset_service.increment_download_count(dataset_id)

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Preparar form y comentarios
    form = DataSetCommentForm()
    comments = dataset.comments

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            dataset=dataset,
            comments=comments,
            form=form,
        )
    )
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    form = DataSetCommentForm()
    comments = dataset.comments

    return render_template(
        "dataset/view_dataset.html",
        dataset=dataset,
        comments=comments,
        form=form,
    )


@dataset_bp.route("/dataset/<int:dataset_id>/stats", methods=["GET"])
def dataset_stats(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    total_files = dataset.get_files_count()
    total_size_human = dataset.get_file_total_size_for_human()
    view_count = dataset_service.get_view_count(dataset_id)
    download_count = dataset.download_count
    created_at = dataset.created_at

    return render_template(
        "dataset/stats_dataset.html",
        dataset=dataset,
        total_files=total_files,
        total_size_human=total_size_human,
        view_count=view_count,
        download_count=download_count,
        created_at=created_at,
    )


@dataset_bp.route("/dataset/create_from_cart", methods=["POST"])
@login_required
def create_dataset_from_cart():
    title = request.form.get("title")
    description = request.form.get("desc")

    if not title or not description:
        flash("Title and description are required.", "danger")
        return redirect(url_for("shopping_cart.index"))

    cart_service = ShoppingCartService()
    shopping_cart = cart_service.get_cart_by_user(current_user)

    if not shopping_cart or not shopping_cart.items:
        flash("Your shopping cart is empty.", "warning")
        return redirect(url_for("shopping_cart.index"))

    dataset_service = DataSetService()
    try:
        new_dataset = dataset_service.create_from_cart(
            user_id=current_user.id, form_data=request.form, shopping_cart=shopping_cart
        )

        flash("Dataset created successfully from your cart!", "success")
        return redirect(url_for("dataset.get_unsynchronized_dataset", dataset_id=new_dataset.id))

    except Exception as e:
        flash(f"Error creating dataset: {str(e)}", "danger")
        return redirect(url_for("shopping_cart.index"))


@dataset_bp.route("/dataset/<int:dataset_id>/comment", methods=["POST"])
@login_required
def add_dataset_comment(dataset_id):
    # usamos el servicio como en el resto del módulo
    dataset = dataset_service.get_or_404(dataset_id)
    form = DataSetCommentForm()

    if not form.validate_on_submit():
        flash("Invalid comment.", "danger")
        # Redirigimos de nuevo a la vista del dataset
        if dataset.ds_meta_data.dataset_doi:
            # si tiene DOI público
            return redirect(url_for("dataset.subdomain_index", doi=dataset.ds_meta_data.dataset_doi))
        else:
            # si es un dataset local/unsynchronized
            return redirect(url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id))

    comment = DSComment(
        dataset_id=dataset.id,
        user_id=current_user.id,
        content=form.content.data.strip(),
    )

    db.session.add(comment)
    db.session.commit()

    flash("Comment added successfully.", "success")

    # misma lógica de redirección que arriba
    if dataset.ds_meta_data.dataset_doi:
        return redirect(url_for("dataset.subdomain_index", doi=dataset.ds_meta_data.dataset_doi))
    else:
        return redirect(url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id))


@dataset_bp.route("/dataset/<int:dataset_id>/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_dataset_comment(dataset_id, comment_id):
    dataset = dataset_service.get_or_404(dataset_id)
    comment = DSComment.query.get_or_404(comment_id)

    # Verificar que el comentario pertenece a este dataset
    if comment.dataset_id != dataset.id:
        abort(404)

    # Solo puede eliminar el autor del comentario o el dueño del dataset
    if comment.user_id != current_user.id and dataset.user_id != current_user.id:
        flash("You don't have permission to delete this comment.", "danger")
        if dataset.ds_meta_data.dataset_doi:
            return redirect(url_for("dataset.subdomain_index", doi=dataset.ds_meta_data.dataset_doi))
        else:
            return redirect(url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id))

    # Eliminar el comentario
    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted successfully.", "success")

    # Redirigir según el tipo de dataset
    if dataset.ds_meta_data.dataset_doi:
        return redirect(url_for("dataset.subdomain_index", doi=dataset.ds_meta_data.dataset_doi))
    else:
        return redirect(url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id))
