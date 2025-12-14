from app.modules.explore.repositories import ExploreRepository
from core.services.BaseService import BaseService


class ExploreService(BaseService):
    def __init__(self):
        super().__init__(ExploreRepository())

    def filter(
        self, query="", sorting="newest", publication_type="any", authors_filter="any", tags_filter="any", **kwargs
    ):
        return self.repository.filter(query, sorting, publication_type, authors_filter, tags_filter, **kwargs)

    def get_all_authors(self):
        return self.repository.get_all_authors()

    def get_all_tags(self):
        return self.repository.get_all_tags()

    def get_all_datasets(self):
        return self.repository.get_all_datasets()
