from app.modules.pokemon_check.repositories import PokemonCheckRepository
from core.services.BaseService import BaseService


class PokemonCheckService(BaseService):
    def __init__(self):
        super().__init__(PokemonCheckRepository())
