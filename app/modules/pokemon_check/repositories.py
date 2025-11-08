from app.modules.pokemon_check.models import PokemonCheck
from core.repositories.BaseRepository import BaseRepository


class PokemonCheckRepository(BaseRepository):
    def __init__(self):
        super().__init__(PokemonCheck)
