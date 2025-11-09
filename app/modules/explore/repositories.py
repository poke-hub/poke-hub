import re

import unidecode
from sqlalchemy import any_, or_, func
from collections import defaultdict

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType, Author
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from core.repositories.BaseRepository import BaseRepository



class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def get_all_authors(self):
        # También con el count para mostrarlo
        results = (
            Author.query.with_entities(
                Author.id.label("id"),
                Author.name.label("name"),
                func.count(Author.id).label("count"),
            )
            .group_by(Author.id)
            .order_by(func.count(Author.id).desc())
            .all()
        )
        # Lo devolvemos como JSON
        return [
            {"id": r.id, "name": r.name, "count": int(r.count)}
            for r in results
        ]

    def get_all_tags(self):
        # Obtenemos las tags en un diccionario con su count
        tags_dict = defaultdict(int)
        metadata_datasets = DSMetaData.query.all()

        for metadata in metadata_datasets:
            for tag in metadata.get_all_tags():
                tags_dict[tag] += 1

        # Lo devolvemos como JSON
        return [{"name": tag, "count": count} for tag, count in tags_dict.items()]

    def filter(self, query="", sorting="newest", publication_type="any", authors_filter="any", tags_filter="any", **kwargs):
        # Normalize and remove unwanted characters
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        filters = []
        for word in cleaned_query.split():
            filters.append(DSMetaData.title.ilike(f"%{word}%"))
            filters.append(DSMetaData.description.ilike(f"%{word}%"))
            filters.append(Author.name.ilike(f"%{word}%"))
            filters.append(Author.affiliation.ilike(f"%{word}%"))
            filters.append(Author.orcid.ilike(f"%{word}%"))
            filters.append(FMMetaData.uvl_filename.ilike(f"%{word}%"))
            filters.append(FMMetaData.title.ilike(f"%{word}%"))
            filters.append(FMMetaData.description.ilike(f"%{word}%"))
            filters.append(FMMetaData.publication_doi.ilike(f"%{word}%"))
            filters.append(FMMetaData.tags.ilike(f"%{word}%"))
            filters.append(DSMetaData.tags.ilike(f"%{word}%"))

        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models)
            .join(FeatureModel.fm_meta_data)
            .filter(or_(*filters))
            .filter(DSMetaData.dataset_doi.isnot(None))  # Exclude datasets with empty dataset_doi
        )

        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

        if authors_filter != "any" and authors_filter is not None:
            author_id = int(authors_filter) if authors_filter.isdigit() else None
            if author_id:
                filtered_datasets = []
                for dataset in datasets:
                    if data_set.has_author(author_id):
                        filtered_datasets.append(dataset)
                datasets = filtered_datasets

        if tags_filter != "any" and tags_filter is not None:
            tag_name = tags_filter.strip()
            if tag_name:
                filtered_datasets = []
                for dataset in datasets:
                    if dataset.ds_meta_data.has_tag(tag_name):
                        filtered_datasets.append(dataset)
                datasets = filtered_datasets

        # Order by created_at
        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()
