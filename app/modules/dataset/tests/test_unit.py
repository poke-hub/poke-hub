import io
from unittest.mock import patch
from zipfile import ZipFile

import pytest

from app.modules.dataset.services import DataSetService


@pytest.fixture
def dataset_service():
    return DataSetService()


def test_extract_uvls_from_zip(dataset_service, tmp_path):
    buf = io.BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("file1.uvl", "content1")
        zf.writestr("file2.txt", "should be ignored")
    buf.seek(0)

    saved = dataset_service.extract_uvls_from_zip(buf, tmp_path)
    assert "file1.uvl" in saved
    assert not any(f.endswith(".txt") for f in saved)
    assert (tmp_path / "file1.uvl").exists()


def test_import_uvls_from_github(dataset_service, tmp_path):
    fake_zip = io.BytesIO()
    with ZipFile(fake_zip, "w") as zf:
        zf.writestr("repo-branch/file1.uvl", "content")
    fake_zip.seek(0)

    with patch.object(dataset_service, "fetch_repo_zip", return_value=fake_zip.getvalue()):
        saved = dataset_service.import_uvls_from_github("https://github.com/fake/repo", dest_dir=tmp_path)
        assert "file1.uvl" in saved
        assert (tmp_path / "file1.uvl").exists()
