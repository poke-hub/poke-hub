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
from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
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

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

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
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


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
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".poke"):
        return jsonify({"message": "No valid file"}), 400

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

                if not norm.lower().endswith(".uvl"):
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

                if not norm.lower().endswith(".uvl"):
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

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)


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
