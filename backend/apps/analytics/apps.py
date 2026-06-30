from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    label = "analytics"
    verbose_name = "Analytics"

    def ready(self) -> None:
        # Connect domain-signal receivers (order lifecycle -> analytics events).
        from apps.analytics import receivers  # noqa: F401
