"""Catalog domain models (store-scoped via ``TenantOwnedModel``).

Every model here is tenant-owned: ``Model.objects`` is automatically filtered to
the active store (resolved from the request). Uniqueness of slugs/SKUs is scoped
per-store and ignores soft-deleted rows (partial unique constraints).

This increment covers the commerce core — Category, Brand, Product, Variant.
Media (images/video), attributes, collections, tags and bulk import are layered
on in later increments.
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TenantOwnedModel


def _generate_download_token() -> str:
    return secrets.token_urlsafe(32)


class SEOFields(models.Model):
    """Reusable SEO metadata mix-in."""

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True


class ProductType(models.TextChoices):
    PHYSICAL = "physical", "Physical"
    DIGITAL = "digital", "Digital"


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class ProductKind(models.TextChoices):
    SIMPLE = "simple", "Simple"
    CONFIGURABLE = "configurable", "Configurable"
    BUNDLE = "bundle", "Bundle"
    KIT = "kit", "Kit"
    COMPOSITE = "composite", "Composite"


#: Kinds whose sellable price/availability derive from their components rather
#: than from their own stock.
COMPOSITE_KINDS = frozenset({ProductKind.BUNDLE, ProductKind.KIT, ProductKind.COMPOSITE})


class Category(TenantOwnedModel, SEOFields):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    position = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ("position", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["store", "slug"],
                condition=Q(is_deleted=False),
                name="uniq_category_store_slug",
            )
        ]
        indexes = [models.Index(fields=["store", "is_active"])]

    def __str__(self) -> str:
        return self.name


class Brand(TenantOwnedModel, SEOFields):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "slug"],
                condition=Q(is_deleted=False),
                name="uniq_brand_store_slug",
            )
        ]

    def __str__(self) -> str:
        return self.name


class Product(TenantOwnedModel, SEOFields):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    product_type = models.CharField(
        max_length=16, choices=ProductType.choices, default=ProductType.PHYSICAL
    )
    # Structural kind. Defaults to SIMPLE so existing products are unaffected.
    kind = models.CharField(
        max_length=16, choices=ProductKind.choices, default=ProductKind.SIMPLE, db_index=True
    )
    status = models.CharField(
        max_length=16,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "slug"],
                condition=Q(is_deleted=False),
                name="uniq_product_store_slug",
            )
        ]
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "category"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_published(self) -> bool:
        return self.status == ProductStatus.PUBLISHED

    def publish(self) -> None:
        self.status = ProductStatus.PUBLISHED
        if self.published_at is None:
            self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def archive(self) -> None:
        self.status = ProductStatus.ARCHIVED
        self.save(update_fields=["status", "updated_at"])


class ProductVariant(TenantOwnedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=64, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Simple single-location stock; superseded by the multi-warehouse inventory
    # feature, which will become the source of truth.
    stock_quantity = models.PositiveIntegerField(default=0)
    track_inventory = models.BooleanField(default=True)

    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    # e.g. {"color": "red", "size": "L"}
    options = models.JSONField(default=dict, blank=True)

    is_default = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Product variant"
        verbose_name_plural = "Product variants"
        ordering = ("position", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["store", "sku"],
                condition=Q(is_deleted=False),
                name="uniq_variant_store_sku",
            )
        ]
        indexes = [models.Index(fields=["product", "is_active"])]

    def __str__(self) -> str:
        return f"{self.sku} ({self.name})" if self.name else self.sku


class BundleComponent(TenantOwnedModel):
    """A component (variant + quantity) of a bundle/kit/composite product."""

    bundle = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="components")
    component_variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, related_name="component_of"
    )
    quantity = models.PositiveIntegerField(default=1)
    is_optional = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Bundle component"
        verbose_name_plural = "Bundle components"
        ordering = ("sort_order", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["bundle", "component_variant"],
                condition=Q(is_deleted=False),
                name="uniq_bundle_component",
            )
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.component_variant_id} in {self.bundle_id}"


# --- Digital products ------------------------------------------------------
class LicenseKeyStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    ASSIGNED = "assigned", "Assigned"
    REVOKED = "revoked", "Revoked"


class DigitalAsset(TenantOwnedModel):
    """Downloadable deliverable for a (digital) product variant."""

    variant = models.OneToOneField(
        ProductVariant, on_delete=models.CASCADE, related_name="digital_asset"
    )
    name = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="catalog/digital/", null=True, blank=True)
    external_url = models.URLField(blank=True)
    # Per-grant limits (null = unlimited / never expires).
    download_limit = models.PositiveIntegerField(null=True, blank=True)
    download_expiry_days = models.PositiveIntegerField(null=True, blank=True)
    requires_license = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Digital asset"
        verbose_name_plural = "Digital assets"

    def __str__(self) -> str:
        return self.name or f"asset:{self.variant_id}"

    @property
    def download_url(self) -> str:
        if self.file:
            return self.file.url
        return self.external_url


class LicenseKey(TenantOwnedModel):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="license_keys"
    )
    key = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16,
        choices=LicenseKeyStatus.choices,
        default=LicenseKeyStatus.AVAILABLE,
        db_index=True,
    )
    assigned_order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "License key"
        verbose_name_plural = "License keys"
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["store", "key"],
                condition=Q(is_deleted=False),
                name="uniq_license_key_store",
            )
        ]
        indexes = [models.Index(fields=["variant", "status"])]

    def __str__(self) -> str:
        return self.key


class DownloadGrant(TenantOwnedModel):
    """Access granted to a buyer for a digital asset after order confirmation."""

    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="download_grants"
    )
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="+")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="download_grants"
    )
    digital_asset = models.ForeignKey(
        DigitalAsset, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    download_limit = models.PositiveIntegerField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    token = models.CharField(
        max_length=64, unique=True, default=_generate_download_token, editable=False
    )

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Download grant"
        verbose_name_plural = "Download grants"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["user", "order"])]

    def __str__(self) -> str:
        return f"grant:{self.token[:8]} ({self.variant_id})"

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and timezone.now() > self.expires_at

    @property
    def remaining_downloads(self):
        if self.download_limit is None:
            return None
        return max(self.download_limit - self.download_count, 0)

    def can_download(self) -> bool:
        if self.is_expired:
            return False
        return self.download_limit is None or self.download_count < self.download_limit


# --- Configurable products & attributes ------------------------------------
class Attribute(TenantOwnedModel):
    """A variant axis, e.g. Color or Size."""

    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=120)
    is_variant = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"
        ordering = ("sort_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["store", "code"],
                condition=Q(is_deleted=False),
                name="uniq_attribute_store_code",
            )
        ]

    def __str__(self) -> str:
        return self.name


class AttributeValue(TenantOwnedModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=120)
    label = models.CharField(max_length=120, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Attribute value"
        verbose_name_plural = "Attribute values"
        ordering = ("sort_order", "value")
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"],
                condition=Q(is_deleted=False),
                name="uniq_attribute_value",
            )
        ]

    def __str__(self) -> str:
        return self.label or self.value


class ProductAttribute(TenantOwnedModel):
    """Declares an attribute as one of a configurable product's variant axes."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_attributes"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT, related_name="+")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Product attribute"
        verbose_name_plural = "Product attributes"
        ordering = ("sort_order",)
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute"],
                condition=Q(is_deleted=False),
                name="uniq_product_attribute",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_id}:{self.attribute_id}"


class VariantOption(TenantOwnedModel):
    """A variant's chosen value on one attribute axis (its coordinate)."""

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="option_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT, related_name="+")
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.PROTECT, related_name="+")

    class Meta(TenantOwnedModel.Meta):
        verbose_name = "Variant option"
        verbose_name_plural = "Variant options"
        ordering = ("attribute__sort_order",)
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "attribute"],
                condition=Q(is_deleted=False),
                name="uniq_variant_attribute_option",
            )
        ]

    def __str__(self) -> str:
        return f"{self.variant_id}:{self.attribute_value_id}"
