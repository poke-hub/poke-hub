import hashlib
import io
import logging
import os
import shutil
import uuid
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from zipfile import BadZipFile, ZipFile

import requests
from flask import request

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DataSet, DSMetaData, DSViewRecord
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import FeatureModelRepository, FMMetaDataRepository
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


def _ensure_unique_filename(dest_dir: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    candidate = filename
    dest_path = os.path.join(dest_dir, candidate)
    i = 1
    while os.path.exists(dest_path):
        candidate = f"{base} ({i}){ext}"
        dest_path = os.path.join(dest_dir, candidate)
        i += 1
    return candidate


def _safe_norm(path: str) -> str:
    norm = os.path.normpath(path).replace("\\", "/")
    return norm


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.feature_model_repository = FeatureModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.fmmetadata_repository = FMMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()

    def move_feature_models(self, dataset: DataSet):
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

        os.makedirs(dest_dir, exist_ok=True)

        for feature_model in dataset.feature_models:
            poke_filename = feature_model.fm_meta_data.poke_filename
            shutil.move(os.path.join(source_dir, poke_filename), dest_dir)

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_feature_models(self):
        return self.feature_model_service.count_feature_models()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()

    def create_from_form(self, form, current_user) -> DataSet:
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:
            logger.info(f"Creating dsmetadata...: {form.get_dsmetadata()}")
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            dataset = self.create(commit=False, user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            for feature_model in form.feature_models:
                poke_filename = feature_model.poke_filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **feature_model.get_fmmetadata())
                for author_data in feature_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.feature_model_repository.create(
                    commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                # associated files in feature model
                file_path = os.path.join(current_user.temp_folder(), poke_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False, name=poke_filename, checksum=checksum, size=size, feature_model_id=fm.id
                )
                fm.files.append(file)
            self.repository.session.commit()
        except Exception as exc:
            logger.info(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc
        return dataset

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_pokehub_doi(self, dataset: DataSet) -> str:
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"

    def get_view_count(self, dataset_id: int) -> int:
        return self.dsviewrecord_repostory.get_view_count(dataset_id)

    def increment_download_count(self, dataset_id):
        dataset = self.repository.get_or_404(dataset_id)
        self.repository.update(dataset_id, download_count=dataset.download_count + 1)

    def trending_by_views(self, limit: int = 5, days: int = 30):
        """
        Returns a list of (DataSet, views_count) limited to the last `days`.
        """
        return self.repository.trending_by_views(limit=limit, days=days)

    def trending_by_downloads(self, limit: int = 5, days: int = 30):
        """
        Returns a list of (DataSet, downloads_count) limited to the last `days`.
        """
        return self.repository.trending_by_downloads(limit=limit, days=days)

    def extract_uvls_from_zip(self, file_stream, dest_dir: str) -> List[str]:
        """
        Extrae SOLO .uvl del stream ZIP (file-like), guarda en dest_dir
        con nombres únicos. Devuelve la lista de nombres guardados.
        """
        os.makedirs(dest_dir, exist_ok=True)
        saved, _ignored = self._extract_uvls_from_zip(ZipFile(file_stream), dest_dir=dest_dir, subdir=None)
        return saved

    def fetch_repo_zip(self, repo_url: str, branch: str | None) -> bytes:
        if not repo_url:
            raise ValueError("repo_url is required")

        parsed = urlparse(repo_url)
        if "github.com" not in parsed.netloc.lower():
            raise ValueError("Only GitHub URLs are supported")

        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise ValueError("Invalid GitHub repo URL")

        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]

        branch = branch or "main"
        archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"

        try:
            resp = requests.get(archive_url, timeout=60)
            if resp.status_code != 200:
                raise RuntimeError(f"GitHub returned {resp.status_code}")
            return resp.content
        except Exception as e:
            logger.exception("Error downloading GitHub archive")
            raise e

    def import_uvls_from_github(
        self,
        repo_url: str,
        branch: str = "main",
        subdir: str | None = None,
        dest_dir: str = "",
    ) -> List[str]:
        if not dest_dir:
            raise ValueError("dest_dir is required")

        zip_bytes = self.fetch_repo_zip(repo_url=repo_url, branch=branch)
        os.makedirs(dest_dir, exist_ok=True)

        try:
            with ZipFile(io.BytesIO(zip_bytes)) as zf:
                saved, _ignored = self._extract_uvls_from_zip(zf, dest_dir=dest_dir, subdir=subdir)
                return saved
        except BadZipFile as e:
            logger.exception("Invalid ZIP from GitHub")
            raise e

    def _extract_uvls_from_zip(self, zf: ZipFile, dest_dir: str, subdir: str | None) -> Tuple[List[str], List[str]]:
        saved: List[str] = []
        ignored: List[str] = []

        possible_root = ""
        try:
            first = zf.namelist()[0]
            if "/" in first:
                possible_root = first.split("/")[0]  # 'repo-branch'
        except Exception:
            possible_root = ""

        prefixes: List[str] = []
        if subdir:
            subdir = subdir.strip("/")

            if possible_root:
                prefixes.append(f"{possible_root}/{subdir}/")
            prefixes.append(f"{subdir}/")

        for member in zf.infolist():
            name = member.filename

            if member.is_dir():
                continue

            if prefixes:
                if not any(name.startswith(p) for p in prefixes):
                    continue

            norm = _safe_norm(name)

            if norm.startswith("../") or norm.startswith("/"):
                ignored.append(name)
                continue

            if not norm.lower().endswith(".uvl"):
                ignored.append(name)
                continue

            base_filename = os.path.basename(norm)
            candidate = _ensure_unique_filename(dest_dir, base_filename)
            dest_path = os.path.join(dest_dir, candidate)

            with zf.open(member, "r") as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

            saved.append(candidate)

        return saved, ignored


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService:

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        else:
            return f"{round(size / (1024 ** 3), 2)} GB"
