import re
from collections import defaultdict

import unidecode
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.pokemodel.models import FMMetaData, PokeModel
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
        return [{"id": r.id, "name": r.name, "count": int(r.count)} for r in results]

    def get_all_tags(self):
        # Obtenemos las tags en un diccionario con su count
        tags_dict = defaultdict(int)
        metadata_datasets = DSMetaData.query.all()

        for metadata in metadata_datasets:
            for tag in metadata.get_all_tags():
                tags_dict[tag] += 1

        # Lo devolvemos como JSON, ordenado por count desc
        sorted_tags = sorted(tags_dict.items(), key=lambda kv: kv[1], reverse=True)
        return [{"name": tag, "count": int(count)} for tag, count in sorted_tags]

    def filter(
        self, query="", sorting="newest", publication_type="any", authors_filter="any", tags_filter="any", **kwargs
    ):
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        DsAuthor = aliased(Author)
        FmAuthor = aliased(Author)

        filters = []
        for word in cleaned_query.split():
            like = f"%{word}%"
            filters.extend([DSMetaData.title.ilike(like), DSMetaData.description.ilike(like)])

        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .outerjoin(DsAuthor, DsAuthor.ds_meta_data_id == DSMetaData.id)
            .join(DataSet.poke_models)
            .join(PokeModel.fm_meta_data)
            .outerjoin(FmAuthor, FmAuthor.fm_meta_data_id == FMMetaData.id)
            .filter(True if not filters else or_(*filters))
            .filter(DSMetaData.dataset_doi.isnot(None))
        )

        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break
            if matching_type is not None:
                # comparar con el enum, no con .name
                datasets = datasets.filter(DSMetaData.publication_type == matching_type)

        if authors_filter not in ("any", None, "") and authors_filter.isdigit():
            author_id = int(authors_filter)
            datasets = datasets.filter(or_(DsAuthor.id == author_id, FmAuthor.id == author_id))

        if tags_filter not in ("any", None, ""):
            tag_name = tags_filter.strip()
            if tag_name:
                like_tag = f"%{tag_name}%"
                datasets = datasets.filter(or_(DSMetaData.tags.ilike(like_tag), FMMetaData.tags.ilike(like_tag)))

        if sorting == "oldest":
            datasets = datasets.order_by(self.model.created_at.asc())
        else:
            datasets = datasets.order_by(self.model.created_at.desc())

        return datasets.all()

    def get_all_datasets(self):
        return self.filter()
