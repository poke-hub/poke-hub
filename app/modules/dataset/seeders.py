import os
import shutil
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import and_

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):

    priority = 2  # Lower priority

    def _get_or_create(self, model, defaults=None, **filters):
        """
        Idempotencia sencilla: busca por filtros; si no existe, crea con defaults.
        Devuelve instancia y booleano created.
        """
        instance = model.query.filter_by(**filters).first()
        if instance:
            return instance, False
        data = dict(defaults or {})
        data.update(filters)
        instance = model(**data)
        db.session.add(instance)
        db.session.flush()
        return instance, True

    def run(self):
        # 1) Usuarios requeridos
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()
        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        # 2) Métricas (una sola fila, idempotente por números)
        ds_metrics, _ = self._get_or_create(
            DSMetrics,
            number_of_models="5",
            number_of_features="50",
        )

        # 3) Metadatos de dataset (4 ejemplos)
        #    0 y 1 -> borradores (dataset_doi=None)
        #    2 y 3 -> publicados (dataset_doi con valor)
        ds_meta_specs = []
        for i in range(4):
            is_draft = i < 2
            ds_meta_specs.append(
                dict(
                    title=f"Sample dataset {i+1}",
                    description=f"Description for dataset {i+1}",
                    publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                    publication_doi=(None if is_draft else f"10.1234/dataset_pub_{i+1}"),
                    dataset_doi=(None if is_draft else f"10.1234/dataset_pub_{i+1}"),
                    tags="tag1, tag2",
                    ds_metrics_id=ds_metrics.id,
                    # deposition_id lo dejamos en None en draft; opcional poner número en publicados
                    deposition_id=(None if is_draft else (100 + i)),
                )
            )

        seeded_ds_meta_data = []
        for spec in ds_meta_specs:
            # Idempotencia: usamos title como clave "humana"
            dsmeta, _ = self._get_or_create(
                DSMetaData,
                # defaults:
                description=spec["description"],
                publication_type=spec["publication_type"],
                publication_doi=spec["publication_doi"],
                dataset_doi=spec["dataset_doi"],
                tags=spec["tags"],
                ds_metrics_id=spec["ds_metrics_id"],
                deposition_id=spec["deposition_id"],
                # filtro:
                title=spec["title"],
            )
            # Si por idempotencia algún campo cambió entre ejecuciones, actualizamos:
            dsmeta.description = spec["description"]
            dsmeta.publication_type = spec["publication_type"]
            dsmeta.publication_doi = spec["publication_doi"]
            dsmeta.dataset_doi = spec["dataset_doi"]
            dsmeta.tags = spec["tags"]
            dsmeta.ds_metrics_id = spec["ds_metrics_id"]
            dsmeta.deposition_id = spec["deposition_id"]
            seeded_ds_meta_data.append(dsmeta)

        # 4) Autores (1 autor por cada DSMetaData)
        for i, dsmeta in enumerate(seeded_ds_meta_data):
            name = f"Author {i+1}"
            author, created = self._get_or_create(
                Author,
                # defaults:
                affiliation=f"Affiliation {i+1}",
                orcid=f"0000-0000-0000-000{i}",
                # filtro:
                name=name,
                ds_meta_data_id=dsmeta.id,
            )
            # idempotencia: refrescamos datos "suaves"
            author.affiliation = f"Affiliation {i+1}"
            author.orcid = f"0000-0000-0000-000{i}"

        # 5) DataSet (enlazar a usuarios; marcar draft_mode según el caso)
        seeded_datasets = []
        for i, dsmeta in enumerate(seeded_ds_meta_data):
            is_draft = i < 2
            owner_id = user1.id if i % 2 == 0 else user2.id
            dataset, _ = self._get_or_create(
                DataSet,
                # defaults:
                created_at=datetime.now(timezone.utc),
                draft_mode=is_draft,
                # filtro:
                ds_meta_data_id=dsmeta.id,
                user_id=owner_id,
            )
            # idempotencia: aseguramos el flag correctamente
            dataset.draft_mode = is_draft
            seeded_datasets.append(dataset)

        # 6) Feature models (12 en total, 3 por dataset)
        fm_meta_data_list = []
        for i in range(12):
            filename = f"file{i+1}.uvl"
            fmmeta, _ = self._get_or_create(
                FMMetaData,
                # defaults:
                title=f"Feature Model {i+1}",
                description=f"Description for feature model {i+1}",
                publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                publication_doi=f"10.1234/fm{i+1}",
                tags="tag1, tag2",
                uvl_version="1.0",
                # filtro:
                uvl_filename=filename,
            )
            # idempotencia: refrescamos algunos campos
            fmmeta.title = f"Feature Model {i+1}"
            fmmeta.description = f"Description for feature model {i+1}"
            fmmeta.publication_type = PublicationType.SOFTWARE_DOCUMENTATION
            fmmeta.publication_doi = f"10.1234/fm{i+1}"
            fmmeta.tags = "tag1, tag2"
            fmmeta.uvl_version = "1.0"
            fm_meta_data_list.append(fmmeta)

        seeded_feature_models = []
        for i in range(12):
            ds_idx = i // 3  # 0..3
            fmmeta = fm_meta_data_list[i]
            dataset = seeded_datasets[ds_idx]
            fm, _ = self._get_or_create(
                FeatureModel,
                # no defaults adicionales
                fm_meta_data_id=fmmeta.id,
                data_set_id=dataset.id,
            )
            seeded_feature_models.append(fm)

        # Create files, associate them with FeatureModels and copy files
        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "uvl_examples")

        for i in range(12):
            file_name = f"file{i+1}.uvl"
            feature_model = seeded_feature_models[i]
            dataset = next(ds for ds in seeded_datasets if ds.id == feature_model.data_set_id)
            user_id = dataset.user_id

            # origen
            src_path = os.path.join(src_folder, file_name)
            if not os.path.exists(src_path):
                # Si no están los ejemplos, no rompas el seed
                continue

            # destino
            dest_folder = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, file_name)

            # copiar si hace falta
            if not os.path.exists(dest_path):
                shutil.copy(src_path, dest_path)

            size = os.path.getsize(dest_path)

            # Hubfile idempotente por (feature_model_id, name)
            hubfile, _ = self._get_or_create(
                Hubfile,
                # defaults:
                checksum=f"checksum{i+1}",
                size=size,
                # filtro:
                feature_model_id=feature_model.id,
                name=file_name,
            )
            # refrescamos tamaño por si cambió
            hubfile.size = size

        # commit final por si quedaron cambios pendientes de idempotencia
        db.session.commit()
