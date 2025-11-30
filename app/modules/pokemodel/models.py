import os
import re

from flask import current_app
from sqlalchemy import Enum as SQLAlchemyEnum

from app import db
from app.modules.dataset.models import Author, PublicationType


class Pokemon:
    name: str
    item: str
    ability: str
    tera_type: str
    evs: dict[str, int]
    ivs: dict[str, int]
    moves: list[str]


class PokeModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_set_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), nullable=False)
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey("fm_meta_data.id"))
    files = db.relationship("Hubfile", backref="poke_model", lazy=True, cascade="all, delete")
    fm_meta_data = db.relationship("FMMetaData", uselist=False, backref="poke_model", cascade="all, delete")

    def __repr__(self):
        return f"PokeModel<{self.id}>"

    def get_pokemon(self):

        directory_path = f"uploads/user_{self.data_set.user_id}/dataset_{self.data_set_id}/{self.files[0].name}"
        parent_directory_path = os.path.dirname(current_app.root_path)
        file_path = os.path.join(parent_directory_path, directory_path)

        pokemon = parse_poke(file_path)
        return pokemon

    def get_total_ivs(self):
        pokemon = self.get_pokemon()
        return sum(pokemon.ivs.values())

    def get_total_evs(self):
        pokemon = self.get_pokemon()
        return sum(pokemon.evs.values())


def parse_poke(file_path):

    with open(file_path, "r") as f:
        lines = f.read().strip().splitlines()
        name = lines[0].split("@")[0].strip()
        item = lines[0].split("@")[1].strip() if "@" in lines[0] else ""
        moves = []
        ability = ""
        tera_type = ""
        evs = {}
        ivs = {}

        for line in lines[1:]:
            if not line:
                continue

            kv_match = re.match(r"^\s*([^:]+):\s*(.*)$", line, re.IGNORECASE)
            if kv_match:
                key = kv_match.group(1).strip().lower()
                value = kv_match.group(2).strip()

                if key == "ability":
                    ability = value
                elif key == "tera type":
                    tera_type = value
                elif key == "evs":
                    ev_parts = value.split("/")
                    for ev in ev_parts:
                        val, stat = ev.strip().split()
                        evs[stat] = int(val)
                elif key == "ivs":
                    iv_parts = value.split("/")
                    for iv in iv_parts:
                        val, stat = iv.strip().split()
                        ivs[stat] = int(val)
                continue

            move_match = re.match(r"^\s*-\s+(.*)$", line)
            if move_match:
                moves.append(move_match.group(1).strip())
                continue

        pokemon = Pokemon()
        pokemon.name = name
        pokemon.item = item
        pokemon.ability = ability
        pokemon.tera_type = tera_type
        pokemon.evs = evs
        pokemon.ivs = ivs
        pokemon.moves = moves
    return pokemon


class FMMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poke_filename = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    poke_version = db.Column(db.String(120))
    fm_metrics_id = db.Column(db.Integer, db.ForeignKey("fm_metrics.id"))
    fm_metrics = db.relationship("FMMetrics", uselist=False, backref="fm_meta_data")
    authors = db.relationship(
        "Author", backref="fm_metadata", lazy=True, cascade="all, delete", foreign_keys=[Author.fm_meta_data_id]
    )

    def __repr__(self):
        return f"FMMetaData<{self.title}"

    def get_all_tags(self):
        res = set()
        if self.tags:
            res.update(self.tags.split(","))
        return res


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.Text)
    not_solver = db.Column(db.Text)

    def __repr__(self):
        return f"FMMetrics<solver={self.solver}, not_solver={self.not_solver}>"
