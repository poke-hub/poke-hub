import os

from dotenv import load_dotenv

load_dotenv()


def uploads_folder_name():
    return os.getenv("UPLOADS_DIR", "uploads")


def get_app_version():
    version_file_path = os.path.join(os.getenv("WORKING_DIR", ""), ".version")
    try:
        with open(version_file_path, "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        return "unknown"


def is_develop():
    return os.getenv("FLASK_ENV") == "development"


def is_production():
    return os.getenv("FLASK_ENV") == "production"


def fakenodo_url():
    return os.getenv("FAKENODO_URL")

class Config:
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = ("UVLHub", os.getenv("MAIL_DEFAULT_SENDER"))
