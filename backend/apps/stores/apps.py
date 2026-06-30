from django.apps import AppConfig


class StoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stores"
    label = "stores"
    verbose_name = "Stores"

    def ready(self) -> None:
        # Invalidate the tenant-resolution cache on store/settings changes.
        from apps.stores import receivers  # noqa: F401
