import logging

from flask import render_template, request

from app.modules.dataset.services import DataSetService
from app.modules.pokemodel.services import PokeModelService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    poke_model_service = PokeModelService()

    # Statistics: total datasets and poke models
    datasets_counter = dataset_service.count_synchronized_datasets()
    poke_models_counter = poke_model_service.count_poke_models()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_poke_model_downloads = poke_model_service.total_poke_model_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()
    total_poke_model_views = poke_model_service.total_poke_model_views()

    metric = request.args.get("metric", "views")
    trending_views = dataset_service.trending_by_views(limit=3, days=30)
    trending_downloads = dataset_service.trending_by_downloads(limit=3, days=30)
    selected_metric = "downloads" if metric == "downloads" else "views"

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        poke_models_counter=poke_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_poke_model_downloads=total_poke_model_downloads,
        total_dataset_views=total_dataset_views,
        total_poke_model_views=total_poke_model_views,
        trending_views=trending_views,
        trending_downloads=trending_downloads,
        selected_metric=selected_metric,
    )
