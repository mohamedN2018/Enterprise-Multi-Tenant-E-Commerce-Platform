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

# Rich demo catalog: category -> [(name, price, description), ...].
CATALOG = {
    "Electronics": [
        (
            "Wireless Headphones",
            "79.99",
            "Over-ear Bluetooth headphones with active noise cancellation.",
        ),
        ("4K Monitor", "329.00", "27-inch 4K IPS monitor with slim bezels."),
        ("Mechanical Keyboard", "119.00", "Hot-swappable RGB mechanical keyboard."),
        ("USB-C Cable", "9.99", "1m braided USB-C to USB-C charging cable."),
        ("Bluetooth Speaker", "59.00", "Portable waterproof speaker with 12-hour battery."),
        ("Gaming Mouse", "45.00", "16000 DPI ergonomic gaming mouse."),
        ("1080p Webcam", "49.00", "Full-HD webcam with dual microphones."),
    ],
    "Home & Kitchen": [
        ("Laptop Stand", "39.50", "Aluminium adjustable laptop stand."),
        ("LED Desk Lamp", "34.00", "Dimmable LED desk lamp with a USB charging port."),
        ("Coffee Maker", "89.00", "12-cup programmable drip coffee maker."),
        ("Air Fryer 5L", "129.00", "Digital air fryer with a 5-litre capacity."),
        ("Ceramic Mug Set", "24.00", "Set of four stoneware coffee mugs."),
    ],
    "Sports & Outdoors": [
        ("Yoga Mat", "27.00", "Non-slip 6mm yoga mat with a carry strap."),
        ("Adjustable Dumbbell Set", "119.00", "Adjustable dumbbells from 2 to 24 kg."),
        ("Insulated Water Bottle", "22.00", "1L stainless-steel vacuum bottle."),
        ("Resistance Bands", "18.00", "Set of five resistance loop bands."),
    ],
    "Accessories": [
        ("Power Bank 20000mAh", "35.00", "Fast-charge dual-port power bank."),
        ("Smart Watch", "149.00", "Fitness smartwatch with a heart-rate sensor."),
        ("Laptop Backpack", "54.00", "Water-resistant 15-inch laptop backpack."),
        ("Clear Phone Case", "14.00", "Shockproof transparent phone case."),
    ],
    "Fashion": [
        ("Cotton T-Shirt", "19.99", "Organic cotton crew-neck t-shirt."),
        ("Denim Jacket", "69.00", "Classic washed denim jacket."),
        ("Running Shoes", "94.00", "Lightweight breathable running shoes."),
        ("Leather Wallet", "39.00", "Slim RFID-blocking leather wallet."),
        ("Polarized Sunglasses", "29.00", "UV400 polarized sunglasses."),
    ],
    "Beauty & Care": [
        ("Vitamin C Serum", "25.00", "Brightening facial serum, 30 ml."),
        ("Lip Balm Trio", "12.00", "Pack of three nourishing lip balms."),
        ("Sonic Toothbrush", "49.00", "Rechargeable sonic electric toothbrush."),
    ],
}

# Which categories live in which store (marketplace feel: two shops).
STORES = [
    ("Demo Store", ["Electronics", "Home & Kitchen", "Sports & Outdoors", "Accessories"]),
    ("Style Studio", ["Fashion", "Beauty & Care"]),
]

# A few approved reviews (from distinct reviewers — one review per product/user)
# so product pages show real ratings.  (product, reviewer_email, rating, title, body)
REVIEWS = [
    (
        "Wireless Headphones",
        "alice@demo.com",
        5,
        "Amazing sound",
        "Fantastic noise cancellation and battery life.",
    ),
    (
        "Wireless Headphones",
        "bob@demo.com",
        4,
        "Very comfortable",
        "Great for long calls, a little bass-heavy.",
    ),
    (
        "4K Monitor",
        "alice@demo.com",
        5,
        "Crisp and bright",
        "Colours are gorgeous — perfect for design work.",
    ),
    (
        "Mechanical Keyboard",
        "carol@demo.com",
        4,
        "Satisfying typing",
        "Love the switches, slightly loud for the office.",
    ),
    (
        "Laptop Stand",
        "bob@demo.com",
        5,
        "Rock solid",
        "Sturdy aluminium build, great posture helper.",
    ),
    ("Air Fryer 5L", "carol@demo.com", 4, "Cooks evenly", "Big capacity and easy to clean."),
]


class Command(BaseCommand):
    help = "Seed a demo store with published, stocked products (development only)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Allow running with DEBUG=False.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to seed with DEBUG=False (pass --force to override).")

        from apps.accounts.models import User
        from apps.catalog.models import Category, Product
        from apps.stores.models import Store, StoreStatus
        from apps.stores.services import StoreService

        owner = self._user(User, "owner@demo.com")
        buyer = self._user(User, "buyer@demo.com")

        demo_store = None
        for store_name, category_names in STORES:
            store = Store.all_objects.filter(name=store_name).first()
            if store is None:
                store = StoreService().create_store(owner=owner, data={"name": store_name})
            self._seed_catalog(store=store, category_names=category_names)
            self._seed_shipping(store=store)
            # Publish the store so it appears in the public storefront.
            if store.status != StoreStatus.ACTIVE:
                store.status = StoreStatus.ACTIVE
                store.save(update_fields=["status", "updated_at"])
            if store_name == "Demo Store":
                demo_store = store

        orders = self._seed_orders(store=demo_store, buyer=buyer)
        self._seed_reviews(store=demo_store, buyer=buyer)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(
            f"  Stores:       {Store.all_objects.filter(status=StoreStatus.ACTIVE).count()} active"
        )
        self.stdout.write(f"  Categories:   {Category.all_objects.count()} total")
        self.stdout.write(f"  Products:     {Product.all_objects.count()} total")
        self.stdout.write(
            f"  Orders:       {orders['total']} total "
            f"({orders['confirmed']} confirmed, {orders['cancelled']} cancelled, "
            f"{orders['pending']} pending); payments: {orders['payments']}"
        )
        self.stdout.write("  Admin:        admin@example.com")
        self.stdout.write("  Store owner:  owner@demo.com / Demo12345!")
        self.stdout.write("  Buyer:        buyer@demo.com / Demo12345!")

    def _seed_shipping(self, *, store) -> None:
        """A default shipping zone + two methods (idempotent)."""
        from apps.shipping.models import ShippingMethod, ShippingZone
        from apps.shipping.services import ShippingService

        if ShippingMethod.all_objects.filter(store=store, is_deleted=False).exists():
            return
        service = ShippingService()
        zone = ShippingZone.all_objects.filter(
            store=store, is_default=True, is_deleted=False
        ).first()
        if zone is None:
            zone = service.create_zone(
                store=store, data={"name": "Worldwide", "is_default": True, "countries": []}
            )
        service.add_method(
            store=store,
            zone=zone,
            data={"name": "Standard", "price": Decimal("5.00"), "free_over": Decimal("100.00")},
        )
        service.add_method(
            store=store, zone=zone, data={"name": "Express", "price": Decimal("12.00")}
        )

    def _seed_reviews(self, *, store, buyer) -> None:
        """Approved demo reviews so product pages show ratings (idempotent)."""
        from apps.accounts.models import User
        from apps.catalog.models import Product
        from apps.reviews.models import Review, ReviewStatus

        for name, reviewer_email, rating, title, body in REVIEWS:
            product = Product.all_objects.filter(store=store, name=name, is_deleted=False).first()
            if product is None:
                continue
            reviewer = self._user(User, reviewer_email)
            # One review per (store, product, user) — respect the unique constraint.
            if Review.all_objects.filter(store=store, product=product, user=reviewer).exists():
                continue
            Review.objects.create(
                store=store,
                product=product,
                user=reviewer,
                rating=rating,
                title=title,
                body=body,
                status=ReviewStatus.APPROVED,
                is_verified_purchase=True,
            )

    def _seed_catalog(self, *, store, category_names) -> None:
        """Create categories + published, stocked products for a store (idempotent)."""
        from apps.catalog.models import Category, Product, ProductStatus
        from apps.catalog.services import CatalogService
        from apps.inventory.models import Warehouse
        from apps.inventory.services import InventoryService

        warehouse, _ = Warehouse.objects.get_or_create(
            store=store, code="MAIN", defaults={"name": "Main Warehouse"}
        )
        catalog, inventory = CatalogService(), InventoryService()
        for cat_name in category_names:
            category = Category.all_objects.filter(
                store=store, name=cat_name, is_deleted=False
            ).first()
            if category is None:
                category = catalog.create_category(store=store, data={"name": cat_name})
            for name, price, description in CATALOG[cat_name]:
                product = Product.all_objects.filter(
                    store=store, name=name, is_deleted=False
                ).first()
                if product is None:
                    product = catalog.create_product(
                        store=store,
                        data={
                            "name": name,
                            "status": ProductStatus.PUBLISHED,
                            "description": description,
                            "category": category,
                        },
                    )
                    variant = catalog.create_variant(
                        store=store,
                        product=product,
                        data={"sku": name.replace(" ", "-").upper(), "price": Decimal(price)},
                    )
                    inventory.receive(
                        store=store, variant=variant, warehouse=warehouse, quantity=50
                    )
                elif product.category_id is None:
                    product.category = category
                    product.save(update_fields=["category", "updated_at"])

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
