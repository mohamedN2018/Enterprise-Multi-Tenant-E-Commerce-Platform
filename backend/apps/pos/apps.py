from django.apps import AppConfig


class PosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pos"
    label = "pos"
    verbose_name = "Point of sale (cashier) integration"

    def ready(self) -> None:
        # Push stock changes out to a linked cashier when stock is committed.
        from apps.pos import receivers  # noqa: F401
