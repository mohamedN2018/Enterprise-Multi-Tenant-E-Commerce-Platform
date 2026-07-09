"""Outbound POS supplier link: verify the key, import & upsert the catalog."""

from __future__ import annotations

import pytest
from django.db import connection as db_connection
from django.test import override_settings
from django.urls import reverse

from apps.catalog.models import Product
from apps.catalog.services import CatalogService
from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.inventory.models import StockItem
from apps.pos import client as client_mod
from apps.pos import security
from apps.pos.client import PosAuthError, PosOutOfStockError, PosSupplierClient, PosUnavailableError
from apps.pos.models import PosSupplierConnection
from apps.pos.services import PosSupplierService
from apps.stores.models import StoreRole

pytestmark = pytest.mark.django_db

SUPPLIER_URL = reverse("v1:pos:supplier")
IMPORT_URL = reverse("v1:pos:supplier-import")

STORE_SUMMARY = {"store": "سوبر ماركت النيل", "provider": "q-shop POS", "productCount": 46}
PRODUCTS = [
    {
        "id": "u-cola", "name": "كوكاكولا كانز 330 مل", "name_en": "Coca-Cola Cans 330ml",
        "description": None, "sku": None, "barcode": "5449000000996", "price": 12.0,
        "cost": 8.0, "stock": 34, "category": "المشروبات", "image_url": None,
        "type": "STANDARD", "is_active": True,
    },
    {
        "id": "u-chips", "name": "شيبسي", "name_en": "Chips", "description": None,
        "sku": None, "barcode": "6221031492891", "price": 10.0, "cost": 6.0, "stock": 5,
        "category": "سناكس", "image_url": None, "type": "STANDARD", "is_active": True,
    },
]

CONNECT_BODY = {
    "provider": "q-shop POS",
    "api_url": "https://q-shop-cashier.deplois.net/api",
    "api_key": "secret-key-123",
}


@pytest.fixture
def mock_pos(monkeypatch):
    """Stub the outbound HTTP client so no real network call happens."""
    monkeypatch.setattr(PosSupplierClient, "verify", lambda self: dict(STORE_SUMMARY))
    monkeypatch.setattr(PosSupplierClient, "fetch_products", lambda self: [dict(p) for p in PRODUCTS])


def _connect(store_client, store, owner):
    return store_client(owner, store).post(SUPPLIER_URL, CONNECT_BODY, format="json")


def _on_hand(store, sku):
    from apps.catalog.models import ProductVariant

    variant = ProductVariant.all_objects.get(store=store, sku=sku)
    return sum(i.quantity for i in StockItem.all_objects.filter(store=store, variant=variant))


# --- Connect ---------------------------------------------------------------
def test_connect_verifies_key_and_stores(store_client, make_store, mock_pos):
    store, owner = make_store()
    resp = _connect(store_client, store, owner)
    assert resp.status_code == 200, resp.content
    data = resp.json()["data"]
    assert data["is_connected"] is True
    assert data["remote_store_name"] == "سوبر ماركت النيل"
    assert data["remote_product_count"] == 46
    assert "api_key" not in data  # never exposed
    assert data["has_key"] is True


def test_connect_rejects_bad_key(store_client, make_store, monkeypatch):
    store, owner = make_store()

    def _boom(self):
        raise PosAuthError()

    monkeypatch.setattr(PosSupplierClient, "verify", _boom)
    resp = _connect(store_client, store, owner)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "pos_invalid_key"


def test_employee_without_settings_cannot_connect(store_client, make_store, make_user, add_member, mock_pos):
    store, owner = make_store()
    employee = make_user()
    add_member(store, employee, StoreRole.EMPLOYEE, permissions=["catalog"])
    assert store_client(employee, store).post(SUPPLIER_URL, CONNECT_BODY, format="json").status_code == 403


# --- Import ----------------------------------------------------------------
def test_import_creates_products_with_price_and_stock(store_client, make_store, mock_pos):
    store, owner = make_store()
    _connect(store_client, store, owner)

    resp = store_client(owner, store).post(IMPORT_URL, {}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.json()["data"]["summary"] == {"created": 2, "updated": 0, "skipped": 0}

    assert Product.all_objects.filter(store=store, is_deleted=False).count() == 2
    # Price landed on the default variant; stock became real warehouse inventory.
    cola = Product.all_objects.get(store=store, name="كوكاكولا كانز 330 مل")
    variant = cola.variants.get(is_default=True)
    assert str(variant.price) == "12.00" and str(variant.cost_price) == "8.00"
    assert variant.barcode == "5449000000996"
    assert _on_hand(store, variant.sku) == 34
    # Category was created from the Arabic name.
    assert cola.category and cola.category.name == "المشروبات"


def test_reimport_updates_in_place(store_client, make_store, mock_pos, monkeypatch):
    store, owner = make_store()
    _connect(store_client, store, owner)
    store_client(owner, store).post(IMPORT_URL, {}, format="json")

    # Price + stock change upstream; a second import must update, not duplicate.
    bumped = [dict(p) for p in PRODUCTS]
    bumped[0] = {**bumped[0], "price": 15.5, "stock": 100}
    monkeypatch.setattr(PosSupplierClient, "fetch_products", lambda self: bumped)

    resp = store_client(owner, store).post(IMPORT_URL, {}, format="json")
    assert resp.json()["data"]["summary"] == {"created": 0, "updated": 2, "skipped": 0}
    assert Product.all_objects.filter(store=store, is_deleted=False).count() == 2

    cola = Product.all_objects.get(store=store, name="كوكاكولا كانز 330 مل")
    assert str(cola.variants.get(is_default=True).price) == "15.50"
    assert _on_hand(store, cola.variants.get(is_default=True).sku) == 100


def test_import_matches_existing_by_barcode(store_client, make_store, mock_pos):
    store, owner = make_store()
    # A product already exists locally with the same barcode as an incoming one.
    product = CatalogService().create_product(store=store, data={"name": "كولا قديمة"})
    CatalogService().create_variant(
        store=store,
        product=product,
        data={"sku": "OLD-1", "barcode": "5449000000996", "price": "9.00", "is_default": True},
    )
    _connect(store_client, store, owner)

    store_client(owner, store).post(IMPORT_URL, {}, format="json")

    # The barcode match links to the existing product — no duplicate created.
    assert (
        Product.all_objects.filter(store=store, is_deleted=False, variants__barcode="5449000000996")
        .distinct()
        .count()
        == 1
    )


# --- Robustness: never bubble a 500 -----------------------------------------
class _FakeResp:
    def __init__(self, body: bytes):
        self._body = body

    def read(self, *args):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_client_sends_browser_user_agent(monkeypatch):
    """POS providers behind Cloudflare block the default urllib agent; we must
    present a browser UA so server-to-server calls aren't challenged."""
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["ua"] = req.get_header("User-agent")
        captured["key"] = req.get_header("X-api-key")
        return _FakeResp(b'{"store":"S","productCount":1}')

    monkeypatch.setattr(client_mod.urllib.request, "urlopen", _fake_urlopen)
    PosSupplierClient(api_url="https://x/api", api_key="k").verify()
    assert "Mozilla/5.0" in (captured["ua"] or "")
    assert captured["key"] == "k"


def test_arabic_store_name_header_is_latin1_safe():
    """An Arabic store name must not crash urllib — HTTP header values are
    latin-1, so non-ASCII identity headers are percent-encoded."""
    client = PosSupplierClient(
        api_url="https://x/api",
        api_key="k",
        store_name="سوبر ماركت النيل",
        store_url="https://shop.example/store/nile",
    )
    headers = client._headers()
    for value in headers.values():
        value.encode("latin-1")  # would raise UnicodeEncodeError before the fix
    assert headers["x-store-name"].isascii()
    assert "%D8" in headers["x-store-name"]  # percent-encoded UTF-8 bytes


def test_non_json_response_becomes_unavailable_not_500(monkeypatch):
    """A 200 with a non-JSON body is surfaced as a clean error, never a 500."""
    monkeypatch.setattr(
        client_mod.urllib.request, "urlopen", lambda req, timeout=None: _FakeResp(b"<html>oops</html>")
    )
    client = PosSupplierClient(api_url="https://q-shop.example/api", api_key="k")
    with pytest.raises(PosUnavailableError):
        client.verify()


def test_import_skips_a_failing_row(store_client, make_store, mock_pos, monkeypatch):
    """One product that blows up during upsert is skipped; the rest still import."""
    store, owner = make_store()
    _connect(store_client, store, owner)

    original = PosSupplierService._upsert

    def flaky(self, *, store, connection, item):
        if item["id"] == "u-chips":
            raise ValueError("boom")
        return original(self, store=store, connection=connection, item=item)

    monkeypatch.setattr(PosSupplierService, "_upsert", flaky)

    resp = store_client(owner, store).post(IMPORT_URL, {}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.json()["data"]["summary"] == {"created": 1, "updated": 0, "skipped": 1}
    assert Product.all_objects.filter(store=store, is_deleted=False).count() == 1


# --- Push placed orders to the cashier --------------------------------------
def test_push_order_maps_items_and_skips_unmapped(make_store, make_variant, monkeypatch):
    """A confirmed order is pushed with each line mapped to its cashier product id;
    lines with no cashier equivalent are omitted."""
    from apps.orders.models import Order, OrderItem
    from apps.pos.models import PosImportedProduct, PosSupplierConnection

    store, owner = make_store()
    product, variant = make_variant(store, sku="MAP-1", stock=5)
    _unmapped_product, unmapped = make_variant(store, sku="LOCAL-1", stock=5)

    conn = PosSupplierConnection.objects.create(
        store=store, provider="q-shop POS", api_url="https://x/api", api_key="k", is_connected=True
    )
    PosImportedProduct.objects.create(
        store=store, connection=conn, external_id="CASHIER-9", product=product
    )

    order = Order.objects.create(
        store=store,
        user=owner,
        number="ORD-1",
        total="150.00",
        tax_total="0.00",
        discount_total="0.00",
        shipping_address={"full_name": "أحمد علي", "phone": "01000000000"},
    )
    for v, price in ((variant, "50.00"), (unmapped, "50.00")):
        OrderItem.objects.create(
            store=store, order=order, variant=v, product_name=v.sku, sku=v.sku,
            unit_price=price, quantity=2, line_total="100.00",
        )

    captured = {}
    monkeypatch.setattr(
        client_mod.PosSupplierClient,
        "push_order",
        lambda self, payload: (captured.update(payload), {"id": "tx1"})[1],
    )
    PosSupplierService().push_order(connection=conn, order=order)

    assert captured["external_id"] == "ORD-1"
    assert captured["customer_name"] == "أحمد علي"
    assert captured["customer_phone"] == "01000000000"
    assert captured["total_amount"] == 150.0
    # Only the mapped line is sent, with the cashier's product id.
    assert captured["items"] == [{"product_id": "CASHIER-9", "quantity": 2, "unit_price": 50.0}]

    # The order is stamped as synced so the seller can see it reached the cashier.
    order.refresh_from_db()
    assert order.pos_reference == "tx1"
    assert order.pos_synced_at is not None


def test_push_order_raises_when_no_line_maps_to_cashier(make_store, make_variant, monkeypatch):
    """No line maps to a cashier product → must NOT silently push an empty order;
    it raises and never POSTs, so the seller isn't told it was 'sent'."""
    from apps.orders.models import Order, OrderItem
    from apps.pos.models import PosSupplierConnection

    store, owner = make_store()
    _p, unmapped = make_variant(store, sku="LOCAL-ONLY", stock=5)
    conn = PosSupplierConnection.objects.create(
        store=store, provider="q-shop POS", api_url="https://x/api", api_key="k", is_connected=True
    )
    order = Order.objects.create(
        store=store, user=owner, number="ORD-NO-MAP", total="100.00",
        tax_total="0.00", discount_total="0.00", shipping_address={},
    )
    OrderItem.objects.create(
        store=store, order=order, variant=unmapped, product_name="x", sku="LOCAL-ONLY",
        unit_price="50.00", quantity=2, line_total="100.00",
    )

    called = {"pushed": False}
    monkeypatch.setattr(
        client_mod.PosSupplierClient, "push_order",
        lambda self, payload: called.update(pushed=True) or {"id": "tx"},
    )
    with pytest.raises(ConflictError) as exc:
        PosSupplierService().push_order(connection=conn, order=order)
    assert exc.value.code == "pos_no_cashier_items"
    assert called["pushed"] is False  # never POSTed an empty order
    order.refresh_from_db()
    assert order.pos_synced_at is None


def test_push_order_raises_when_cashier_returns_no_id(make_store, make_variant, monkeypatch):
    """A 200 without an { id } isn't a confirmation — treat as NOT sent and don't
    stamp the order as synced."""
    from apps.orders.models import Order, OrderItem
    from apps.pos.models import PosImportedProduct, PosSupplierConnection

    store, owner = make_store()
    product, variant = make_variant(store, sku="MAP-2", stock=5)
    conn = PosSupplierConnection.objects.create(
        store=store, provider="q-shop POS", api_url="https://x/api", api_key="k", is_connected=True
    )
    PosImportedProduct.objects.create(
        store=store, connection=conn, external_id="CASHIER-2", product=product
    )
    order = Order.objects.create(
        store=store, user=owner, number="ORD-NOID", total="50.00",
        tax_total="0.00", discount_total="0.00", shipping_address={},
    )
    OrderItem.objects.create(
        store=store, order=order, variant=variant, product_name="x", sku="MAP-2",
        unit_price="50.00", quantity=1, line_total="50.00",
    )
    # Cashier answers 200 but with no id → not confirmed.
    monkeypatch.setattr(
        client_mod.PosSupplierClient, "push_order", lambda self, payload: {"duplicate": True}
    )
    with pytest.raises(PosUnavailableError):
        PosSupplierService().push_order(connection=conn, order=order)
    order.refresh_from_db()
    assert order.pos_synced_at is None
    assert not order.pos_reference


def test_check_cashier_stock_flags_shortfall(make_store, make_variant, monkeypatch):
    """Before payment we flag lines the cashier can't fulfil; unreachable → allow."""
    from apps.pos.models import PosImportedProduct, PosSupplierConnection

    store, owner = make_store()
    product, variant = make_variant(store, sku="S-1", stock=10)
    conn = PosSupplierConnection.objects.create(
        store=store, provider="q-shop POS", api_url="https://x/api", api_key="k", is_connected=True
    )
    PosImportedProduct.objects.create(store=store, connection=conn, external_id="C-1", product=product)

    monkeypatch.setattr(client_mod.PosSupplierClient, "fetch_products", lambda self: [{"id": "C-1", "stock": 1}])
    svc = PosSupplierService()
    assert svc.check_cashier_stock(store=store, lines=[(variant, 3)]) == [product.name]
    assert svc.check_cashier_stock(store=store, lines=[(variant, 1)]) == []

    def _down(self):
        raise PosUnavailableError()

    monkeypatch.setattr(client_mod.PosSupplierClient, "fetch_products", _down)
    assert svc.check_cashier_stock(store=store, lines=[(variant, 3)]) == []


def test_client_409_raises_out_of_stock(monkeypatch):
    import io
    import urllib.error

    def _conflict(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 409, "Conflict", {}, io.BytesIO(b'{"out_of_stock":["Cola"]}')
        )

    monkeypatch.setattr(client_mod.urllib.request, "urlopen", _conflict)
    with pytest.raises(PosOutOfStockError) as excinfo:
        PosSupplierClient(api_url="https://x/api", api_key="k").push_order({"external_id": "O1"})
    assert excinfo.value.items == ["Cola"]


def test_manual_push_requires_cashier_and_confirmed(make_store):
    from apps.orders.models import Order

    store, owner = make_store()
    order = Order.objects.create(store=store, user=owner, number="ORD-2", status="confirmed", total="10.00")
    # No cashier linked → clean not-found.
    with pytest.raises(NotFoundError):
        PosSupplierService().push_order_for(store=store, order=order)
    # An unpaid order can't be sent.
    order.status = "pending"
    order.save(update_fields=["status"])
    with pytest.raises(ConflictError):
        PosSupplierService().push_order_for(store=store, order=order)


# --- Security: encryption at rest -------------------------------------------
def test_api_key_is_encrypted_at_rest(store_client, make_store, mock_pos):
    store, owner = make_store()
    _connect(store_client, store, owner)  # stores api_key "secret-key-123"

    # Decrypted transparently on read...
    conn = PosSupplierConnection.all_objects.get(store=store)
    assert conn.api_key == "secret-key-123"
    # ...but the raw column is ciphertext, not the plaintext key.
    with db_connection.cursor() as cur:
        cur.execute("SELECT api_key FROM pos_possupplierconnection")
        raw = cur.fetchone()[0]
    assert raw != "secret-key-123"
    assert "secret-key-123" not in raw


# --- Security: SSRF guard ---------------------------------------------------
@override_settings(POS_ALLOW_UNSAFE_URLS=False)
def test_ssrf_guard_blocks_internal_targets(monkeypatch):
    # Non-http(s) and localhost are rejected without any DNS lookup.
    assert security.is_public_url("file:///etc/passwd") is False
    assert security.is_public_url("http://localhost/api") is False

    # A host that resolves to a private/internal address is blocked...
    monkeypatch.setattr(
        security.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("169.254.169.254", 80))]
    )
    assert security.is_public_url("http://metadata.internal/api") is False
    with pytest.raises(ValidationError):
        security.assert_public_url("http://metadata.internal/api")

    # ...while a public address is allowed.
    monkeypatch.setattr(
        security.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))]
    )
    assert security.is_public_url("https://example.com/api") is True


# --- Security: rate limiting ------------------------------------------------
def test_connect_is_rate_limited(store_client, make_store, mock_pos):
    """Repeated connects hit the pos_connect throttle (default 20/min)."""
    store, owner = make_store()
    client = store_client(owner, store)
    statuses = [
        client.post(SUPPLIER_URL, CONNECT_BODY, format="json").status_code for _ in range(25)
    ]
    assert statuses[0] == 200
    assert 429 in statuses
