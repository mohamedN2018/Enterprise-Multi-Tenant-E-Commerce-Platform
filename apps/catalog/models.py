"""Catalog domain models (store-scoped via ``TenantOwnedModel``).

Every model here is tenant-owned: ``Model.objects`` is automatically filtered to
the active store (resolved from the request). Uniqueness of slugs/SKUs is scoped
per-store and ignores soft-deleted rows (partial unique constraints).

This increment covers the commerce core — Category, Brand, Product, Variant.
Media (images/video), attributes, collections, tags and bulk import are layered
on in later increments.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TenantOwnedModel


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
