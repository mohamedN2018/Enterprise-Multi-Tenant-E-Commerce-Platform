"""Seed a demo store with published, stocked products.

Idempotent and development-oriented: gives a fresh database something to explore
in the API docs / admin and for a frontend to render. Refuses to run with
``DEBUG=False`` unless ``--force`` is passed.

    python manage.py seed_demo
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DEMO_PRODUCTS = [
    ("Wireless Headphones", "79.99", "Over-ear Bluetooth headphones with ANC."),
    ("Mechanical Keyboard", "119.00", "Hot-swappable RGB mechanical keyboard."),
    ("USB-C Cable", "9.99", "1m braided USB-C to USB-C charging cable."),
    ("4K Monitor", "329.00", "27-inch 4K IPS monitor, 60Hz."),
    ("Laptop Stand", "39.50", "Aluminium adjustable laptop stand."),
]


class Command(BaseCommand):
    help = "Seed a demo store with published, stocked products (development only)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Allow running with DEBUG=False.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to seed with DEBUG=False (pass --force to override).")

        from apps.accounts.models import User
        from apps.catalog.models import Product, ProductStatus
        from apps.catalog.services import CatalogService
        from apps.inventory.models import Warehouse
        from apps.inventory.services import InventoryService
        from apps.stores.models import Store
        from apps.stores.services import StoreService

        owner = self._user(User, "owner@demo.com")
        self._user(User, "buyer@demo.com")

        store = Store.all_objects.filter(name="Demo Store").first()
        created_products = 0
        if store is None:
            store = StoreService().create_store(owner=owner, data={"name": "Demo Store"})
            warehouse, _ = Warehouse.objects.get_or_create(
                store=store, code="MAIN", defaults={"name": "Main Warehouse"}
            )
            catalog, inventory = CatalogService(), InventoryService()
            for name, price, description in DEMO_PRODUCTS:
                product = catalog.create_product(
                    store=store,
                    data={
                        "name": name,
                        "status": ProductStatus.PUBLISHED,
                        "description": description,
                    },
                )
                variant = catalog.create_variant(
                    store=store,
                    product=product,
                    data={"sku": name.replace(" ", "-").upper(), "price": Decimal(price)},
                )
                inventory.receive(store=store, variant=variant, warehouse=warehouse, quantity=50)
                created_products += 1

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"  Store:        Demo Store  (X-Store-Id: {store.id})")
        self.stdout.write(f"  Products:     {Product.all_objects.count()} total")
        self.stdout.write("  Admin:        admin@example.com")
        self.stdout.write("  Store owner:  owner@demo.com / Demo12345!")
        self.stdout.write("  Buyer:        buyer@demo.com / Demo12345!")

    @staticmethod
    def _user(model, email):
        user, _ = model.objects.get_or_create(email=email)
        user.set_password("Demo12345!")
        user.is_verified = True
        user.save()
        return user
