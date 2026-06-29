"""Celery application factory.

Configuration is pulled from Django settings using the ``CELERY_`` namespace,
keeping a single source of truth (the settings module).
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("marketplace")

# All Celery configuration keys live in Django settings, prefixed with CELERY_.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py modules in every installed app.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover - operational helper
    print(f"Request: {self.request!r}")
