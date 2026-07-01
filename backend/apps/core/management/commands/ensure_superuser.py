"""Create the production superuser from environment variables (idempotent).

Reads ``DJANGO_SUPERUSER_EMAIL`` and ``DJANGO_SUPERUSER_PASSWORD``. Runs on every
backend start (from the Docker entrypoint), so a fresh production database always
has a ready admin account. Safe to run repeatedly:

  * not configured (vars missing) -> does nothing.
  * user absent                   -> creates the superuser with the env password.
  * user present                  -> ensures admin flags, leaves the password
                                     alone (so an admin who changed it in-app is
                                     not reset on the next deploy).

    python manage.py ensure_superuser
"""

from __future__ import annotations

import os

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Create/ensure the superuser from DJANGO_SUPERUSER_EMAIL/PASSWORD (idempotent)."

    def handle(self, *args, **options):
        from apps.accounts.models import User

        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not email or not password:
            self.stdout.write(
                "ensure_superuser: DJANGO_SUPERUSER_EMAIL/PASSWORD not set — skipping."
            )
            return

        email = User.objects.normalize_email(email)

        with transaction.atomic():
            user = User.all_objects.filter(email=email).first()
            if user is None:
                User.objects.create_superuser(email=email, password=password)
                self.stdout.write(
                    self.style.SUCCESS(f"ensure_superuser: created superuser {email}")
                )
                return

            # Already exists — make sure it can reach the admin, but keep its password.
            changed = False
            if user.is_deleted:
                user.is_deleted = False
                changed = True
            for field in ("is_staff", "is_superuser", "is_active", "is_verified"):
                if not getattr(user, field, False):
                    setattr(user, field, True)
                    changed = True
            if changed:
                user.save()
            self.stdout.write(
                f"ensure_superuser: superuser {email} already exists (password unchanged)."
            )
