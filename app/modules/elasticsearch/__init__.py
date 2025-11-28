from core.blueprints.base_blueprint import BaseBlueprint

elasticsearch_bp = BaseBlueprint("elasticsearch", __name__, template_folder="templates")

from app.modules.elasticsearch import models, routes  # noqa: F401, E402
