from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    label = "payments"
    verbose_name = "Payments"

    def ready(self) -> None:
        # Importing the package registers all bundled gateways.
        from apps.payments import gateways  # noqa: F401
