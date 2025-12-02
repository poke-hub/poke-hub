import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def save_image(file, folder):

    if file.filename == "":
        return None

    if not allowed_file(file.filename):
        raise ValueError("Unsupported file type.")

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")

    upload_folder = os.path.join(
        current_app.static_folder, "img", folder
    )
    os.makedirs(upload_folder, exist_ok=True)
    print("STATIC FOLDER:", current_app.static_folder)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    return f"img/{folder}/{filename}"
