import pytest
from unittest.mock import Mock

from app.modules.dataset.services import DataSetService, SizeService


class DummyDS:
    def __init__(self, id, title, user):
        self.id = id
        class Meta: pass
        self.ds_meta_data = Mock()
        self.ds_meta_data.title = title
        self.user = user
    def get_uvlhub_doi(self):
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


@pytest.mark.parametrize("size,expected", [
    (10, "10 bytes"),
    (1024, "1.0 KB"),
    (1536, "1.5 KB"),
    (1024**2, "1.0 MB"),
    (3 * 1024**2 + 512, f"{round((3*1024**2 + 512)/(1024**2), 2)} MB"),
    (5 * 1024**3, "5.0 GB"),
])
def test_size_service_human_readable(size, expected):
    s = SizeService()
    res = s.get_human_readable_size(size)
    # for MB/GB rounding differences, assert startswith for MB/GB
    if "MB" in expected or "GB" in expected:
        assert expected.split()[1] in res
    else:
        assert res == expected
