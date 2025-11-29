import click
from flask.cli import with_appcontext


@click.command(
    "elasticsearch:reset",
    help="Deletes and recreates the Elasticsearch index, then reindexes all documents.",
)
@with_appcontext
def elasticsearch_reset():
    from app.modules.elasticsearch.services import ElasticsearchService

    search = ElasticsearchService()

    try:
        click.echo(click.style("🗑️  Deleting Elasticsearch index...", fg="yellow"))
        search.es.indices.delete(index=search.index_name)
        click.echo(click.style("✅ Index deleted successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"⚠️  Could not delete index: {e}", fg="bright_yellow"))

    try:
        click.echo(click.style("📦 Recreating Elasticsearch index...", fg="cyan"))
        search.create_index_if_not_exists()
        click.echo(click.style("✅ Index created successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] Failed to create index: {e}", fg="red"))
        return

    try:
        click.echo(click.style("🔁 Reindexing all documents...", fg="cyan"))
        search.seed_index_from_db_if_empty()
        click.echo(click.style("✅ Reindexing completed successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] Reindexing failed: {e}", fg="red"))


@click.command(
    "elasticsearch:delete",
    help="Deletes the Elasticsearch index.",
)
@with_appcontext
def elasticsearch_delete():
    from app.modules.elasticsearch.services import ElasticsearchService

    search = ElasticsearchService()

    click.echo(click.style("[INFO] Starting deletion process...", fg="cyan"))
    try:
        search.delete_index()
        click.echo(click.style("[SUCCESS] Deletion completed successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] Deletion failed: {e}", fg="red"))
