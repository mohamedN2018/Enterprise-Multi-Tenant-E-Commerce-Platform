from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
    label = "search"
    verbose_name = "Search"

    def ready(self) -> None:
        # Invalidate cached search results when the catalog changes.
        from apps.search import receivers  # noqa: F401
