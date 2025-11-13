import io
from unittest.mock import Mock, patch
from zipfile import ZipFile

import pytest

from app.modules.dataset.models import Author, DataSet, DSMetaData
from app.modules.dataset.services import DataSetService, SizeService
from app.modules.featuremodel.models import FeatureModel, FMMetaData


class DummyDS:
    def __init__(self, id, title, user):
        self.id = id

        class Meta:
            pass

        self.ds_meta_data = Mock()
        self.ds_meta_data.title = title
        self.user = user

    def get_pokehub_doi(self):
        return f"http://localhost/doi/10.1234/ds.{self.id}"

    def get_file_total_size_for_human(self):
        return "1.00 MB"


def test_trending_by_views_delegates_to_repository():
    svc = DataSetService()
    # mock repository.trending_by_views
    expected = [(DummyDS(1, "T1", Mock()), 10), (DummyDS(2, "T2", Mock()), 7)]
    svc.repository = Mock()
    svc.repository.trending_by_views.return_value = expected

    res = svc.trending_by_views(limit=3, days=30)

    svc.repository.trending_by_views.assert_called_once_with(limit=3, days=30)
    assert res == expected


def test_trending_by_downloads_delegates_to_repository():
    svc = DataSetService()
    expected = [(DummyDS(5, "D1", Mock()), 4)]
    svc.repository = Mock()
    svc.repository.trending_by_downloads.return_value = expected

    res = svc.trending_by_downloads(limit=1, days=7)

    svc.repository.trending_by_downloads.assert_called_once_with(limit=1, days=7)
    assert res == expected


@pytest.mark.parametrize(
    "size,expected",
    [
        (10, "10 bytes"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (1024**2, "1.0 MB"),
        (3 * 1024**2 + 512, f"{round((3*1024**2 + 512)/(1024**2), 2)} MB"),
        (5 * 1024**3, "5.0 GB"),
    ],
)
def test_size_service_human_readable(size, expected):
    s = SizeService()
    res = s.get_human_readable_size(size)
    # for MB/GB rounding differences, assert startswith for MB/GB
    if "MB" in expected or "GB" in expected:
        assert expected.split()[1] in res
    else:
        assert res == expected


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
    DataSet(ds_meta_data=metadata)
    tags = metadata.get_all_tags()
    assert tags == {"tag1", "tag2", "tag3"}, "The tags extracted do not match the expected set."

    fm_meta_data = FMMetaData(tags="tag3,tag5")
    fm_meta_data2 = FMMetaData(tags="tag4")
    fm1 = FeatureModel(fm_meta_data=fm_meta_data)
    fm2 = FeatureModel(fm_meta_data=fm_meta_data2)
    metadata_complex = DSMetaData(tags="tag1 , tag2")
    DataSet(feature_models=[fm1, fm2], ds_meta_data=metadata_complex)
    tags_complex = metadata_complex.get_all_tags()
    assert tags_complex == {
        "tag1",
        "tag2",
        "tag3",
        "tag4",
        "tag5",
    }, "The tags extracted with spaces do not match the expected set."

    metadata_empty = DSMetaData(tags="")
    DataSet(ds_meta_data=metadata_empty)
    tags_empty = metadata_empty.get_all_tags()
    assert tags_empty == set(), "The tags extracted from an empty string should be an empty set."


def test_ds_meta_data_get_all_authors():

    author1 = Author(name="author1")
    author2 = Author(name="author2")
    metadata = DSMetaData(authors=[author1, author2])
    DataSet(ds_meta_data=metadata)
    authors = metadata.get_all_authors()
    assert authors == {author1, author2}, "The authors extracted do not match the expected set."

    author3 = Author(name="author3")
    author4 = Author(name="author4")
    fm_meta_data = FMMetaData(authors=[author1, author2])
    fm_meta_data2 = FMMetaData(authors=[author3])
    fm1 = FeatureModel(fm_meta_data=fm_meta_data)
    fm2 = FeatureModel(fm_meta_data=fm_meta_data2)
    metadata_complex = DSMetaData(authors=[author1, author4])
    DataSet(feature_models=[fm1, fm2], ds_meta_data=metadata_complex)
    authors_complex = metadata_complex.get_all_authors()
    assert authors_complex == {
        author1,
        author2,
        author3,
        author4,
    }, "The authors extracted with spaces do not match the expected set."

    metadata_empty = DSMetaData(authors=[])
    DataSet(ds_meta_data=metadata_empty)
    authors_empty = metadata_empty.get_all_authors()
    assert authors_empty == set(), "The authors extracted from an empty list should be an empty set."


def test_ds_meta_data_has_tag():

    metadata = DSMetaData(tags="tag1,tag3")
    fm_meta_data = FMMetaData(tags="tag2,tag3")
    fm = FeatureModel(fm_meta_data=fm_meta_data)
    DataSet(feature_models=[fm], ds_meta_data=metadata)

    assert metadata.has_tag("tag1") is True, "The tag 'tag1' should be found."
    assert metadata.has_tag("tag2") is True, "The tag 'tag2' should be found."
    assert metadata.has_tag("tag4") is False, "The tag 'tag4' should not be found."


def test_ds_meta_data_has_author():

    author1 = Author(id=1, name="author1")
    author2 = Author(id=2, name="author2")
    author3 = Author(id=3, name="author3")
    Author(id=4, name="author4")
    metadata = DSMetaData(authors=[author1, author3])
    fm_meta_data = FMMetaData(authors=[author2, author3])
    fm = FeatureModel(fm_meta_data=fm_meta_data)
    DataSet(feature_models=[fm], ds_meta_data=metadata)

    assert metadata.has_author(1) is True, "The author 'author1' should be found."
    assert metadata.has_author(2) is True, "The author 'author2' should be found."
    assert metadata.has_author(4) is False, "The author 'author4' should not be found."


@pytest.fixture
def dataset_service():
    return DataSetService()


def test_extract_pokes_from_zip(dataset_service, tmp_path):
    buf = io.BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("file1.poke", "content1")
        zf.writestr("file2.txt", "should be ignored")
    buf.seek(0)

    saved = dataset_service.extract_pokes_from_zip(buf, tmp_path)
    assert "file1.poke" in saved
    assert not any(f.endswith(".txt") for f in saved)
    assert (tmp_path / "file1.poke").exists()


def test_import_pokes_from_github(dataset_service, tmp_path):
    fake_zip = io.BytesIO()
    with ZipFile(fake_zip, "w") as zf:
        zf.writestr("repo-branch/file1.poke", "content")
    fake_zip.seek(0)

    with patch.object(dataset_service, "fetch_repo_zip", return_value=fake_zip.getvalue()):
        saved = dataset_service.import_pokes_from_github("https://github.com/fake/repo", dest_dir=tmp_path)
        assert "file1.poke" in saved
        assert (tmp_path / "file1.poke").exists()
