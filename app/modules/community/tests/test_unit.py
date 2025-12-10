import pytest
from sqlalchemy import text

from app import db
from app.modules.auth.models import User
from app.modules.community.models import Community, CommunityDatasetRequest
from app.modules.community.services import CommunityService
from app.modules.conftest import login, logout
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType


def _make_dataset(user, title, community=None):
    meta = DSMetaData(title=title, description="desc", publication_type=PublicationType.OTHER)
    db.session.add(meta)
    db.session.commit()

    dataset = DataSet(user_id=user.id, ds_meta_data_id=meta.id, community_id=community.id if community else None)
    db.session.add(dataset)
    db.session.commit()
    return dataset


@pytest.fixture(scope="function")
def community_setup(test_client):
    # Clean related tables to avoid FK/uniqueness conflicts between tests
    # Drop association rows first to satisfy FK constraints.
    db.session.execute(text("DELETE FROM community_curators"))
    db.session.execute(text("DELETE FROM community_members"))
    db.session.query(CommunityDatasetRequest).delete()
    db.session.query(DataSet).delete()
    db.session.query(DSMetaData).delete()
    db.session.query(Community).delete()
    db.session.query(User).filter(
        User.email.in_(["owner@example.com", "joiner@example.com", "other@example.com"])
    ).delete()
    db.session.commit()

    owner = User(email="owner@example.com", password="password")
    joiner = User(email="joiner@example.com", password="password")
    other = User(email="other@example.com", password="password")
    db.session.add_all([owner, joiner, other])
    db.session.commit()

    community = Community(name="Community One", description="Desc")
    community.curators.append(owner)
    community.members.append(owner)
    db.session.add(community)
    db.session.commit()

    ds_in_comm = _make_dataset(owner, "In Community", community)
    ds_available = _make_dataset(owner, "Available")
    ds_pending = _make_dataset(owner, "Pending Request")

    pending_req = CommunityDatasetRequest(
        community_id=community.id, dataset_id=ds_pending.id, requester_id=owner.id, status="pending"
    )
    db.session.add(pending_req)
    db.session.commit()

    yield {
        "app": test_client.application,
        "owner": owner,
        "joiner": joiner,
        "other": other,
        "community": community,
        "ds_available": ds_available,
        "ds_pending": ds_pending,
        "ds_in_comm": ds_in_comm,
        "make_dataset": lambda user, title, comm=None: _make_dataset(user, title, comm),
    }


def test_available_datasets_excludes_pending_and_existing(community_setup):
    community = community_setup["community"]
    owner = community_setup["owner"]

    available = CommunityService.get_available_user_datasets_for_proposal(owner, community)

    assert community_setup["ds_available"] in available
    assert community_setup["ds_pending"] not in available  # pending request should hide it
    assert community_setup["ds_in_comm"] not in available  # already inside community


def test_create_proposal_creates_and_blocks_duplicates(community_setup):
    community = community_setup["community"]
    owner = community_setup["owner"]
    dataset = community_setup["make_dataset"](owner, "Fresh Proposal")

    new_req = CommunityService.create_proposal(community=community, dataset=dataset, requester=owner, message="Hi")

    assert new_req.id is not None
    assert new_req.status == "pending"
    assert new_req.requester_id == owner.id

    with pytest.raises(ValueError):
        CommunityService.create_proposal(community=community, dataset=dataset, requester=owner)


def test_request_accept_moves_dataset_to_community(community_setup):
    community = community_setup["community"]
    owner = community_setup["owner"]
    dataset = community_setup["make_dataset"](owner, "To Accept")

    req = CommunityDatasetRequest(
        community_id=community.id, dataset_id=dataset.id, requester_id=owner.id, status="pending"
    )
    db.session.add(req)
    db.session.commit()

    req.accept(actor=owner)
    db.session.refresh(dataset)

    assert req.status == "accepted"
    assert req.decision_at is not None
    assert dataset.community_id == community.id


def test_request_reject_leaves_dataset_outside_community(community_setup):
    community = community_setup["community"]
    owner = community_setup["owner"]
    dataset = community_setup["make_dataset"](owner, "To Reject")

    req = CommunityDatasetRequest(
        community_id=community.id, dataset_id=dataset.id, requester_id=owner.id, status="pending"
    )
    db.session.add(req)
    db.session.commit()

    req.reject(actor=owner)
    db.session.refresh(dataset)

    assert req.status == "rejected"
    assert req.decision_at is not None
    assert dataset.community_id is None


def test_user_can_join_and_leave_via_routes(test_client, community_setup):
    community = community_setup["community"]
    joiner = community_setup["joiner"]

    client = test_client

    # Join community
    response = login(client, joiner.email, "password")
    assert response.status_code in (200, 302)

    join_resp = client.post(f"/community/join/{community.id}", follow_redirects=False)
    assert join_resp.status_code in (302, 303)

    refreshed_joiner = db.session.get(User, joiner.id)
    assert refreshed_joiner is not None
    assert any(c.id == community.id for c in refreshed_joiner.communities)

    # Leave community
    leave_resp = client.post(f"/community/{community.id}/leave", follow_redirects=False)
    assert leave_resp.status_code in (302, 303)

    refreshed_joiner = db.session.get(User, joiner.id)
    assert refreshed_joiner is not None
    assert all(c.id != community.id for c in refreshed_joiner.communities)

    logout(client)
