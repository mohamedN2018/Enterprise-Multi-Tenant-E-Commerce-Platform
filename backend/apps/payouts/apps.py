from django.apps import AppConfig


class PayoutsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payouts"
    label = "payouts"
    verbose_name = "Seller payouts & commissions"

    def ready(self) -> None:
        # Credit the seller's account (net of commission) on order confirmation.
        from apps.payouts import receivers  # noqa: F401
