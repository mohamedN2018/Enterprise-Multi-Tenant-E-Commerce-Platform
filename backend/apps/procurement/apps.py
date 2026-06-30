from django.apps import AppConfig


class ProcurementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.procurement"
    label = "procurement"
    verbose_name = "Procurement & advanced inventory"

    def ready(self) -> None:
        # FEFO batch depletion when stock is committed/issued.
        from apps.procurement import receivers  # noqa: F401
