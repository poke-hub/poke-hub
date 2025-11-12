import hashlib
import json
import os
import time

from flask import Blueprint, jsonify, request

fakenodo_bp = Blueprint("fakenodo_api", __name__)

DB_PATH = os.path.join(os.getenv("WORKING_DIR", ""), "fakenodo_db.json")
STORAGE = os.path.join(os.getenv("WORKING_DIR", ""), "fakenodo_storage")

def _load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {"next_id": 1, "depositions": {}}


def _save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def _files_checksum(files):
    h = hashlib.sha256()
    for f in sorted(files):
        h.update(f.encode("utf-8"))
    return h.hexdigest()


@fakenodo_bp.route("/deposit/depositions", methods=["POST"])
def create_deposition():
    db = _load_db()
    dep_id = db["next_id"]
    db["next_id"] += 1
    data = request.get_json() or {}
    deposition = {
        "id": dep_id,
        "metadata": data.get("metadata", {}),
        "files": [],
        "created": time.time(),
        "published": False,
        "version": 1,
        "doi": None,
        "last_published_files_checksum": None,
    }
    db["depositions"][str(dep_id)] = deposition
    _save_db(db)
    return jsonify(deposition), 201


@fakenodo_bp.route("/deposit/depositions", methods=["GET"])
def list_depositions():
    db = _load_db()
    return jsonify(list(db["depositions"].values())), 200


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>", methods=["GET"])
def get_deposition(dep_id):
    db = _load_db()
    dep = db["depositions"].get(str(dep_id))
    if not dep:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dep), 200


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>/files", methods=["POST"])
def upload_file(dep_id):
    db = _load_db()
    dep = db["depositions"].get(str(dep_id))
    if not dep:
        return jsonify({"error": "Not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    filename = f.filename
    dest_dir = os.path.join(STORAGE, str(dep_id))
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, filename)
    f.save(file_path)

    file_entry = {"name": filename, "size": os.path.getsize(file_path), "uploaded_at": time.time()}
    dep["files"].append(file_entry)
    db["depositions"][str(dep_id)] = dep
    _save_db(db)
    return jsonify(file_entry), 201


@fakenodo_bp.route("/deposit/depositions/<int:dep_id>/actions/publish", methods=["POST"])
def publish_deposition(dep_id):
    db = _load_db()
    dep = db["depositions"].get(str(dep_id))
    if not dep:
        return jsonify({"error": "Not found"}), 404

    current_checksum = _files_checksum([f["name"] + str(f["size"]) for f in dep["files"]])

    if dep["last_published_files_checksum"] != current_checksum:
        dep["version"] = dep.get("version", 1) + (0 if not dep["published"] else 1)
        dep["doi"] = f"10.9999/fakenodo.{dep['id']}.v{dep['version']}"
        dep["last_published_files_checksum"] = current_checksum
        dep["published"] = True
        db["depositions"][str(dep_id)] = dep
        _save_db(db)
        return jsonify({"id": dep_id, "doi": dep["doi"], "version": dep["version"]}), 202
    else:
        return jsonify({"id": dep_id, "doi": dep.get("doi"), "version": dep.get("version", 1)}), 200
