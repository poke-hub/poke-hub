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
        users = User.query.filter(User.email.in_(["user1@example.com", "user2@example.com"])).all()
        if len(users) < 2:
            raise Exception("Users not found. Please seed users first.")
        user1, user2 = users

        # 2) Métricas base
        ds_metrics, _ = self._get_or_create(
            DSMetrics,
            number_of_models="3",
            number_of_features="25",
        )

        # ------------------------------------------------------
        # 3) Crear 3 datasets por usuario: published, unsync, draft
        # ------------------------------------------------------
        dataset_specs = []
        for user in [user1, user2]:
            dataset_specs.extend([
                dict(  # Published
                    owner=user,
                    title=f"Published dataset ({user.email})",
                    description="A published dataset example.",
                    publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                    dataset_doi=f"10.1234/{user.id}_published",
                    publication_doi=f"10.1234/{user.id}_published",
                    draft_mode=False,
                    deposition_id=100 + user.id,
                ),
                dict(  # Unsynchronized (no DOI, no draft)
                    owner=user,
                    title=f"Unsynchronized dataset ({user.email})",
                    description="A local dataset pending synchronization.",
                    publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                    dataset_doi=None,
                    publication_doi=None,
                    draft_mode=False,
                    deposition_id=None,
                ),
                dict(  # Draft (no DOI, draft_mode=True)
                    owner=user,
                    title=f"Draft dataset ({user.email})",
                    description="A dataset saved as draft.",
                    publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                    dataset_doi=None,
                    publication_doi=None,
                    draft_mode=True,
                    deposition_id=None,
                ),
            ])

        seeded_datasets = []

        for spec in dataset_specs:
            dsmeta, _ = self._get_or_create(
                DSMetaData,
                title=spec["title"],
                defaults=dict(
                    description=spec["description"],
                    publication_type=spec["publication_type"],
                    dataset_doi=spec["dataset_doi"],
                    publication_doi=spec["publication_doi"],
                    tags="tag1, tag2",
                    ds_metrics_id=ds_metrics.id,
                    deposition_id=spec["deposition_id"],
                ),
            )

            # autor principal
            author, _ = self._get_or_create(
                Author,
                name=f"{spec['owner'].profile.surname}, {spec['owner'].profile.name}",
                ds_meta_data_id=dsmeta.id,
                defaults=dict(
                    affiliation=spec['owner'].profile.affiliation,
                    orcid=spec['owner'].profile.orcid or f"0000-0000-0000-{spec['owner'].id:04d}",
                ),
            )

            dataset, _ = self._get_or_create(
                DataSet,
                ds_meta_data_id=dsmeta.id,
                user_id=spec["owner"].id,
                defaults=dict(
                    created_at=datetime.now(timezone.utc),
                    draft_mode=spec["draft_mode"],
                ),
            )

            dataset.draft_mode = spec["draft_mode"]
            seeded_datasets.append(dataset)

        # ------------------------------------------------------
        # 4) Crear feature models (3 por dataset, 6 datasets = 18)
        # ------------------------------------------------------
        fm_meta_data_list = []
        for i in range(18):
            filename = f"fm_{i+1}.uvl"
            fmmeta, _ = self._get_or_create(
                FMMetaData,
                uvl_filename=filename,
                defaults=dict(
                    title=f"Feature Model {i+1}",
                    description=f"Description for feature model {i+1}",
                    publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                    publication_doi=f"10.1234/fm{i+1}",
                    tags="tag1, tag2",
                    uvl_version="1.0",
                ),
            )
            fm_meta_data_list.append(fmmeta)

        seeded_feature_models = []
        for i, fmmeta in enumerate(fm_meta_data_list):
            ds_idx = i // 3  # 3 FMs por dataset
            dataset = seeded_datasets[ds_idx]
            fm, _ = self._get_or_create(
                FeatureModel,
                fm_meta_data_id=fmmeta.id,
                data_set_id=dataset.id,
            )
            seeded_feature_models.append(fm)

        # ------------------------------------------------------
        # 5) Crear Hubfiles asociados y copiar ejemplos UVL
        # ------------------------------------------------------
        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "uvl_examples")

        for i, fm in enumerate(seeded_feature_models):
            file_name = fm.fm_meta_data.uvl_filename
            dataset = next(ds for ds in seeded_datasets if ds.id == fm.data_set_id)
            user_id = dataset.user_id

            src_path = os.path.join(src_folder, file_name)
            if not os.path.exists(src_path):
                continue

            dest_folder = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, file_name)
            if not os.path.exists(dest_path):
                shutil.copy(src_path, dest_path)
            size = os.path.getsize(dest_path)

            hubfile, _ = self._get_or_create(
                Hubfile,
                feature_model_id=fm.id,
                name=file_name,
                defaults=dict(
                    checksum=f"checksum_{i+1}",
                    size=size,
                ),
            )
            hubfile.size = size

        db.session.commit()
