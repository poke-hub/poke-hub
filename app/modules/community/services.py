from app import db
from app.modules.community.models import CommunityDatasetRequest
from core.services.BaseService import BaseService


class CommunityService(BaseService):

    def get_available_user_datasets_for_proposal(user, community):
        requested_ids = {
            req.dataset_id
            for req in CommunityDatasetRequest.query.filter_by(community_id=community.id, status="pending").all()
        }

        return [
            ds
            for ds in user.data_sets
            if ds.community_id != community.id and ds.id not in requested_ids and not ds.draft_mode
        ]

    def create_proposal(community, dataset, requester, message=None):
        existing = CommunityDatasetRequest.query.filter_by(
            community_id=community.id, dataset_id=dataset.id, status="pending"
        ).first()

        if existing:
            raise ValueError("This dataset already has a pending request.")

        request = CommunityDatasetRequest(
            community_id=community.id,
            dataset_id=dataset.id,
            requester_id=requester.id,
            message=message,
            status="pending",
        )

        db.session.add(request)
        db.session.commit()

        return request
