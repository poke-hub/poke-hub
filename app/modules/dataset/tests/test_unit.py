import pytest
from unittest.mock import MagicMock
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.dataset.models import DSMetaData, DataSet, Author


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"

def test_ds_meta_data_get_all_tags():

    metadata = DSMetaData(tags="tag1,tag2,tag3")
    dataset = DataSet(ds_meta_data=metadata)
    tags = metadata.get_all_tags()
    assert tags == {"tag1", "tag2", "tag3"}, "The tags extracted do not match the expected set."

    fm_meta_data = FMMetaData(tags="tag3,tag5")
    fm_meta_data2 = FMMetaData(tags="tag4")
    fm1 = FeatureModel(fm_meta_data=fm_meta_data)
    fm2 = FeatureModel(fm_meta_data=fm_meta_data2)
    metadata_complex = DSMetaData(tags="tag1 , tag2")
    dataset = DataSet(feature_models=[fm1, fm2], ds_meta_data=metadata_complex)
    tags_complex = metadata_complex.get_all_tags()
    assert tags_complex == {"tag1", "tag2", "tag3", "tag4", "tag5"}, "The tags extracted with spaces do not match the expected set."

    metadata_empty = DSMetaData(tags="")
    dataset = DataSet(ds_meta_data=metadata_empty)
    tags_empty = metadata_empty.get_all_tags()
    assert tags_empty == set(), "The tags extracted from an empty string should be an empty set."

def test_ds_meta_data_get_all_authors():

    author1 = Author(name="author1")
    author2 = Author(name="author2")
    metadata = DSMetaData(authors=[author1, author2])
    dataset = DataSet(ds_meta_data=metadata)
    authors = metadata.get_all_authors()
    assert authors == {author1, author2}, "The authors extracted do not match the expected set."

    author3 = Author(name="author3")
    author4 = Author(name="author4")
    fm_meta_data = FMMetaData(authors=[author1, author2])
    fm_meta_data2 = FMMetaData(authors=[author3])
    fm1 = FeatureModel(fm_meta_data=fm_meta_data)
    fm2 = FeatureModel(fm_meta_data=fm_meta_data2)
    metadata_complex = DSMetaData(authors=[author1, author4])
    dataset = DataSet(feature_models=[fm1, fm2], ds_meta_data=metadata_complex)
    authors_complex = metadata_complex.get_all_authors()
    assert authors_complex == {author1, author2, author3, author4}, "The authors extracted with spaces do not match the expected set."

    metadata_empty = DSMetaData(authors=[])
    dataset = DataSet(ds_meta_data=metadata_empty)
    authors_empty = metadata_empty.get_all_authors()
    assert authors_empty == set(), "The authors extracted from an empty list should be an empty set."

def test_ds_meta_data_has_tag():

    metadata = DSMetaData(tags="tag1,tag3")
    fm_meta_data = FMMetaData(tags="tag2,tag3")
    fm = FeatureModel(fm_meta_data=fm_meta_data)
    dataset = DataSet(feature_models=[fm], ds_meta_data=metadata)

    assert metadata.has_tag("tag1") is True, "The tag 'tag1' should be found."
    assert metadata.has_tag("tag2") is True, "The tag 'tag2' should be found."
    assert metadata.has_tag("tag4") is False, "The tag 'tag4' should not be found."

def test_ds_meta_data_has_author():

    author1 = Author(id=1, name="author1")
    author2 = Author(id=2, name="author2")
    author3 = Author(id=3, name="author3")
    author4 = Author(id=4, name="author4")
    metadata = DSMetaData(authors=[author1, author3])
    fm_meta_data = FMMetaData(authors=[author2, author3])
    fm = FeatureModel(fm_meta_data=fm_meta_data)
    dataset = DataSet(feature_models=[fm], ds_meta_data=metadata)

    assert metadata.has_author(1) is True, "The author 'author1' should be found."
    assert metadata.has_author(2) is True, "The author 'author2' should be found."
    assert metadata.has_author(4) is False, "The author 'author4' should not be found."