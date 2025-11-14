from app.modules.elasticsearch.repositories import ElasticsearchRepository
from core.services.BaseService import BaseService
from elasticsearch import Elasticsearch
from datetime import datetime


class ElasticsearchService(BaseService):
    def __init__(self):
        super().__init__(ElasticsearchRepository())
