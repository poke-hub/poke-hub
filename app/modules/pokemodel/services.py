from app.modules.hubfile.services import HubfileService
from app.modules.pokemodel.repositories import FMMetaDataRepository, PokeModelRepository
from core.services.BaseService import BaseService


class PokeModelService(BaseService):
    def __init__(self):
        super().__init__(PokeModelRepository())
        self.hubfile_service = HubfileService()

    def total_poke_model_views(self) -> int:
        return self.hubfile_service.total_hubfile_views()

    def total_poke_model_downloads(self) -> int:
        return self.hubfile_service.total_hubfile_downloads()

    def count_poke_models(self):
        return self.repository.count_poke_models()

    class FMMetaDataService(BaseService):
        def __init__(self):
            super().__init__(FMMetaDataRepository())
