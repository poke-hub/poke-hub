import uuid
from datetime import datetime, timedelta

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.profile.models import UserProfile


@pytest.fixture
def new_user_with_profile(test_client):
    """Create a fresh user with profile for tests."""
    unique_email = f"profile_user_{uuid.uuid4().hex}@example.com"
    user = User(email=unique_email, password="test1234")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(user_id=user.id, name="Prof", surname="User")
    db.session.add(profile)
    db.session.commit()

    yield user


def test_view_profile_no_datasets(test_client, new_user_with_profile):
    """Public profile view for a user without datasets should return 200 and show no datasets message."""
    user = new_user_with_profile

    response = test_client.get(f"/profile/{user.id}")
    assert response.status_code == 200
    assert b"No datasets found" in response.data or b"No datasets uploaded." in response.data


def test_view_profile_with_datasets_and_pagination(test_client, new_user_with_profile):
    """Create 6 datasets for the user and verify pagination shows 5 on first page and 1 on second."""
    user = new_user_with_profile

    base = datetime.utcnow()
    for i in range(6):
        meta = DSMetaData(title=f"Title {i+1}", description=f"Desc {i+1}", publication_type=PublicationType.NONE)
        db.session.add(meta)
        db.session.commit()

        ds = DataSet(user_id=user.id, ds_meta_data_id=meta.id, created_at=base + timedelta(seconds=i))
        db.session.add(ds)
        db.session.commit()

    resp1 = test_client.get(f"/profile/{user.id}")
    assert resp1.status_code == 200
    data1 = resp1.data.decode("utf-8")
    assert "Title 6" in data1
    assert "Title 2" in data1
    assert "Title 1" not in data1

    resp2 = test_client.get(f"/profile/{user.id}?page=2")
    assert resp2.status_code == 200
    data2 = resp2.data.decode("utf-8")
    assert "Title 1" in data2
