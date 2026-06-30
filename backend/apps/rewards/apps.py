from django.apps import AppConfig


class RewardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rewards"
    label = "rewards"
    verbose_name = "Rewards & wallet"

    def ready(self) -> None:
        # Register the store-credit payment gateway with the payments registry.
        # Connect referral reward settlement to the order-confirmed signal.
        from apps.rewards import (
            gateway,  # noqa: F401
            receivers,  # noqa: F401
        )
