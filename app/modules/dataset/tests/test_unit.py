import pytest
from app.modules.feature_model.models import FeatureModel
from app.modules.dataset.models import DSMetaData, Dataset


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
    tags = metadata.get_all_tags()
    assert tags == ["tag1", "tag2", "tag3"], "The tags extracted do not match the expected list."

    fm1 = FeatureModel(tags="tag3,tag5")
    fm2 = FeatureModel(tags="tag4")
    metadata_complex = DSMetaData(tags=" tag1 , tag2 ")
    Dataset = Dataset(feature_models=[fm1, fm2], ds_meta_data=metadata)
    tags_complex = metadata_complex.get_all_tags()
    assert tags_complex == ["tag1", "tag2", "tag3", "tag4", "tag5"], "The tags extracted with spaces do not match the expected list."

    metadata_empty = DSMetaData(tags="")
    tags_empty = metadata_empty.get_all_tags()
    assert tags_empty == [], "The tags extracted from an empty string should be an empty list."

def test_ds_meta_data_get_all_authors():

    metadata = DSMetaData(authors="author1,author2")
    authors = metadata.get_all_authors()
    assert authors == ["author1", "author2"], "The authors extracted do not match the expected list."

    
    fm1 = FeatureModel(authors="author1,author2")
    fm2 = FeatureModel(authors="author3")
    metadata_complex = DSMetaData(authors=" author1 , author4 ")
    Dataset = Dataset(feature_models=[fm1, fm2], ds_meta_data=metadata)
    authors_complex = metadata_complex.get_all_authors()
    assert authors_complex == ["author1", "author2", "author3", "author4"], "The authors extracted with spaces do not match the expected list."

    metadata_empty = DSMetaData(authors="")
    authors_empty = metadata_empty.get_all_authors()
    assert authors_empty == [], "The authors extracted from an empty string should be an empty list."

def test_ds_meta_data_has_tag():

    metadata = DSMetaData(tags="tag1,tag3")
    fm = FeatureModel(tags="tag2,tag3")
    Dataset = Dataset(feature_models=[fm], ds_meta_data=metadata)

    assert metadata.has_tag("tag1") is True, "The tag 'tag1' should be found."
    assert metadata.has_tag("tag2") is True, "The tag 'tag2' should be found."
    assert metadata.has_tag("tag4") is False, "The tag 'tag4' should not be found."

def test_ds_meta_data_has_author():

    metadata = DSMetaData(authors="author1,author3")
    fm = FeatureModel(authors="author2,author3")
    Dataset = Dataset(feature_models=[fm], ds_meta_data=metadata)

    assert metadata.has_author("author1") is True, "The author 'author1' should be found."
    assert metadata.has_author("author2") is True, "The author 'author2' should be found."
    assert metadata.has_author("author4") is False, "The author 'author4' should not be found."