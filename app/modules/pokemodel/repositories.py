from sqlalchemy import func

from app.modules.pokemodel.models import FMMetaData, PokeModel
from core.repositories.BaseRepository import BaseRepository


class PokeModelRepository(BaseRepository):
    def __init__(self):
        super().__init__(PokeModel)

    def count_poke_models(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0


class FMMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(FMMetaData)
