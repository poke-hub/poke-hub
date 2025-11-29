from flask import Blueprint, url_for
from app import db
from app.modules.community.models import Community


community_bp = Blueprint(
    'community',
    __name__,
    template_folder='templates',
    url_prefix='/community'
)

@community_bp.app_context_processor
def inject_community_links():
    return {
        'community_list_url': url_for('community.list_communities'),
        'community_create_url': url_for('community.create_community'),
    }
