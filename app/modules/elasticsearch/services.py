# from datetime import datetime

# from elasticsearch import Elasticsearch

from app.modules.elasticsearch.repositories import ElasticsearchRepository
from core.services.BaseService import BaseService

index_name = "search_index"


class ElasticsearchService(BaseService):
    def __init__(self):
        super().__init__(ElasticsearchRepository())
        # self.es = Elasticsearch(hosts=[TODO COMPLETAR CON EL NOMBRE DEL HOST (PROBABLEMENTE VARIABLE DE ENTORNO)])
        self.index_name = index_name

    def create_index_if_not_exists(self):
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "title": {"type": "text"},
                            "description": {"type": "text"},
                            "tags": {"type": "keyword"},
                            "authors": {"type": "keyword"},
                            "publication_type": {"type": "keyword"},
                            "created_at": {"type": "date"},
                        }
                    }
                },
            )
