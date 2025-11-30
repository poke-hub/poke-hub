# from datetime import datetime

import os
from elasticsearch import Elasticsearch

from app.modules.elasticsearch.repositories import ElasticsearchRepository
from app.modules.explore.services import ExploreService # Para acceder a los datos de la BD
from core.services.BaseService import BaseService

index_name = "search_index"

class ElasticsearchService(BaseService):
    def __init__(self):
        super().__init__(ElasticsearchRepository())
        # NOTA: Reemplaza 'tu_contraseña' con la contraseña real del usuario 'elastic'.
        # NOTA: Reemplaza '/ruta/a/tu/elasticsearch/config/certs/http_ca.crt' con la ruta real.
        self.es = Elasticsearch(
            hosts=[os.environ.get("ELASTICSEARCH_HOST")],
            basic_auth=(os.environ.get("ELASTICSEARCH_USER"), os.environ.get("ELASTICSEARCH_PASSWORD")),
            ca_certs=os.environ.get("ELASTICSEARCH_CERT_PATH"),
        )
        self.index_name = index_name
        self.create_index_if_not_exists()
        self.seed_index_from_db_if_empty()
        

    def create_index_if_not_exists(self):
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "title": {"type": "search_as_you_type"},
                            "description": {"type": "text"},
                            "tags": {"type": "search_as_you_type"},
                            "authors": {"type": "search_as_you_type"},
                            "created_at": {"type": "date"},
                            "pokemons": {"type": "search_as_you_type"},
                            "abilities": {"type": "search_as_you_type"},
                            "moves": {"type": "text"},
                            "max_ev_count": {"type": "integer"},
                            "max_iv_count": {"type": "integer"},
                            "doi": {"type": "keyword"}
                        }
                    }
                },
            )

    def seed_index_from_db_if_empty(self):
        """
        Verifica si el índice está vacío. Si lo está, lo puebla con todos los
        documentos de la base de datos.
        """
        count_response = self.es.count(index=self.index_name)
        if count_response['count'] == 0:
            print(f"Index '{self.index_name}' is empty. Seeding from database...")
            datasets = ExploreService().get_all_datasets()
            for dataset in datasets:
                self.index_document(doc_id=dataset.id, document=dataset.to_indexed())
            print(f"Seeding complete. Indexed {len(datasets)} documents.")

    def index_document(self, doc_id, document):
        self.es.index(index=self.index_name, id=doc_id, body=document)

    def search(self, query, sorting="created_at", desc=False):
        must_clauses = []
        if query:
            must_clauses.append(
                {"multi_match": {"query": query, "fields": ["title", "description", "tags", "authors", "pokemons", "abilities", "moves"]}}
            )
        else:
            must_clauses.append({"match_all": {}})
        body = {
            "query": {
                "bool": {"must": must_clauses}
            },
            "sort": [
                {sorting: {"order": "desc" if desc else "asc"}}
            ]

        }
        response = self.es.search(index=self.index_name, body=body)
        return response

    def delete_from_index(self, doc_id):
        if self.es.exists(index=self.index_name, id=doc_id):
            self.es.delete(index=self.index_name, id=doc_id)
        else:
            print(f"Document {doc_id} tried to be deleted but does not exist.")

    def delete_index(self):
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
            print(f"Index {self.index_name} deleted.")
        else:
            print(f"Index {self.index_name} does not exist.")
