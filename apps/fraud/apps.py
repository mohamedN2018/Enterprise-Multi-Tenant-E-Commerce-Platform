from django.apps import AppConfig


class FraudConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fraud"
    label = "fraud"
    verbose_name = "Fraud detection"

    def ready(self) -> None:
        # Risk-score every placed order via the order_placed signal.
        from apps.fraud import receivers  # noqa: F401
