"""Wipe demo/sample catalog content so real products can be added on a clean slate.

Soft-deletes (not hard-deletes) so existing order history keeps referencing its
products and the unique-slug/SKU constraints (scoped to is_deleted=False) free
up for reuse. Run on the server:

    python manage.py clear_demo --force
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Soft-delete all catalog content (products, variants, images, categories, brands)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Required when DEBUG=False.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to run with DEBUG=False without --force.")

        from apps.catalog.models import Brand, Category, Product, ProductImage, ProductVariant

        counts = {}
        # Order matters little (soft delete), but clear leaves → up for tidiness.
        for label, model in (
            ("product images", ProductImage),
            ("variants", ProductVariant),
            ("products", Product),
            ("categories", Category),
            ("brands", Brand),
        ):
            qs = model.all_objects.filter(is_deleted=False)
            counts[label] = qs.count()
            qs.delete()  # bulk soft-delete (sets is_deleted=True)

        self.stdout.write(self.style.SUCCESS("Demo catalog cleared (soft-deleted):"))
        for label, n in counts.items():
            self.stdout.write(f"  {label:16} {n}")
        self.stdout.write("You can now add real products on a clean slate.")
