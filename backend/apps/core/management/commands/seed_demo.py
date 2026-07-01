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
        buyer = self._user(User, "buyer@demo.com")

        store = Store.all_objects.filter(name="Demo Store").first()
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

        orders = self._seed_orders(store=store, buyer=buyer)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"  Store:        Demo Store  (X-Store-Id: {store.id})")
        self.stdout.write(f"  Products:     {Product.all_objects.count()} total")
        self.stdout.write(
            f"  Orders:       {orders['total']} total "
            f"({orders['confirmed']} confirmed, {orders['cancelled']} cancelled, "
            f"{orders['pending']} pending); payments: {orders['payments']}"
        )
        self.stdout.write("  Admin:        admin@example.com")
        self.stdout.write("  Store owner:  owner@demo.com / Demo12345!")
        self.stdout.write("  Buyer:        buyer@demo.com / Demo12345!")

    def _seed_orders(self, *, store, buyer) -> dict:
        """Place demo orders so the dashboard/analytics have real data.

        Idempotent: skips if the store already has orders. Confirmed orders drive
        revenue + order-lifecycle analytics events; a captured manual payment
        confirms each one (also populating the Payments page).
        """
        from apps.catalog.models import ProductVariant
        from apps.orders.models import Order, OrderStatus
        from apps.orders.services import CartService, CheckoutService
        from apps.payments.services import PaymentService

        existing = Order.all_objects.filter(store=store)
        if existing.exists():
            confirmed = existing.filter(status=OrderStatus.CONFIRMED).count()
            cancelled = existing.filter(status=OrderStatus.CANCELLED).count()
            return {
                "total": existing.count(),
                "confirmed": confirmed,
                "cancelled": cancelled,
                "pending": existing.filter(status=OrderStatus.PENDING).count(),
                "payments": "already seeded",
            }

        variants = list(
            ProductVariant.objects.filter(product__store=store, is_active=True)
            .select_related("product")
            .order_by("created_at")
        )
        if not buyer or not variants:
            return {"total": 0, "confirmed": 0, "cancelled": 0, "pending": 0, "payments": 0}

        cart, checkout, payments = CartService(), CheckoutService(), PaymentService()

        def variant(i):
            return variants[i % len(variants)]

        # Deterministic baskets so the demo looks the same on every fresh DB.
        baskets = [
            [(0, 1), (1, 2)],
            [(2, 3)],
            [(3, 1), (4, 1)],
            [(1, 1)],
            [(0, 2), (4, 1)],
            [(2, 1), (3, 2)],
        ]
        placed = []
        for basket in baskets:
            for idx, qty in basket:
                cart.add_item(store=store, user=buyer, variant_id=variant(idx).id, quantity=qty)
            placed.append(checkout.checkout(store=store, user=buyer))

        captured = 0
        # First four: pay + capture (capture confirms the order).
        for order in placed[:4]:
            payment = payments.create_payment(
                store=store, user=buyer, order=order, gateway_code="manual"
            )
            payments.capture_payment(payment=payment)
            captured += 1
        # Fifth: cancelled. Sixth: left pending, with an uncaptured payment.
        checkout.cancel_order(order=placed[4])
        payments.create_payment(store=store, user=buyer, order=placed[5], gateway_code="manual")

        return {
            "total": len(placed),
            "confirmed": captured,
            "cancelled": 1,
            "pending": 1,
            "payments": captured + 1,
        }

    @staticmethod
    def _user(model, email):
        user, _ = model.objects.get_or_create(email=email)
        user.set_password("Demo12345!")
        user.is_verified = True
        user.save()
        return user
