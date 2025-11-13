from flask import Flask, request, jsonify, send_from_directory
import os
import json
import hashlib
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
DB_PATH = os.path.join(os.getenv("WORKING_DIR", ""), "fakenodo_db.json")
STORAGE = os.path.join(os.getenv("WORKING_DIR", ""), "fakenodo_storage")
os.makedirs(STORAGE, exist_ok=True)

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {"next_id": 1, "depositions": {}}

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)

def files_checksum(files):
    h = hashlib.sha256()
    for f in sorted(files):
        h.update(f.encode("utf-8"))
    return h.hexdigest()

@app.route("/api/deposit/depositions", methods=["POST"])
def create_deposition():
    db = load_db()
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
    save_db(db)
    return jsonify(deposition), 201

@app.route("/api/deposit/depositions", methods=["GET"])
def list_depositions():
    db = load_db()
    return jsonify(list(db["depositions"].values())), 200

@app.route("/api/deposit/depositions/<int:dep_id>", methods=["GET"])
def get_deposition(dep_id):
    db = load_db()
    dep = db["depositions"].get(str(dep_id))
    if not dep:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dep), 200

@app.route("/api/deposit/depositions/<int:dep_id>/files", methods=["POST"])
def upload_file(dep_id):
    db = load_db()
    dep = db["depositions"].get(str(dep_id))
    if not dep:
        return jsonify({"error": "Not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    dest_dir = os.path.join(STORAGE, str(dep_id))
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, filename)
    f.save(file_path)

    file_entry = {"name": filename, "size": os.path.getsize(file_path), "uploaded_at": time.time()}
    dep["files"].append(file_entry)
    db["depositions"][str(dep_id)] = dep
    save_db(db)
    return jsonify(file_entry), 201

@app.route("/api/deposit/depositions/<int:dep_id>/actions/publish", methods=["POST"])
def publish_deposition(dep_id):
    db = load_db()
    dep = db["depositions"].get(str(dep_id))
    if not dep:
        return jsonify({"error": "Not found"}), 404

    current_checksum = files_checksum([f["name"] + str(f["size"]) for f in dep["files"]])

    # If files have changed since last publish -> new version + new DOI
    if dep["last_published_files_checksum"] != current_checksum:
        dep["version"] = dep.get("version", 1) + (0 if not dep["published"] else 1)
        # generate a pseudo-DOI (not real)
        dep["doi"] = f"10.9999/fakenodo.{dep['id']}.v{dep['version']}"
        dep["last_published_files_checksum"] = current_checksum
        dep["published"] = True
        db["depositions"][str(dep_id)] = dep
        save_db(db)
        return jsonify({"id": dep_id, "doi": dep["doi"], "version": dep["version"]}), 202
    else:
        # metadata-only changes => do not issue new DOI, return current doi/version
        return jsonify({"id": dep_id, "doi": dep.get("doi"), "version": dep.get("version", 1)}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FAKENODO_PORT", 8000)), debug=True)