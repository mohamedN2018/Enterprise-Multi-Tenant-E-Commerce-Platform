"""Catalog application services.

Own the catalog write-side business rules: per-store slug generation, product
status transitions, and product-variant invariants (unique SKU, exactly one
default variant per product).
"""

from __future__ import annotations

from django.utils import timezone

from apps.catalog.models import (
    COMPOSITE_KINDS,
    Brand,
    BundleComponent,
    Category,
    Product,
    ProductStatus,
    ProductVariant,
)
from apps.catalog.repositories import ProductVariantRepository
from apps.catalog.slugs import unique_slug
from apps.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from apps.core.services import BaseService, atomic


class CatalogService(BaseService):
    # --- Category ---
    @atomic
    def create_category(self, *, store, data: dict) -> Category:
        slug = unique_slug(Category, store=store, name=data["name"])
        return Category.objects.create(store=store, slug=slug, **data)

    @atomic
    def update_category(self, *, instance: Category, data: dict) -> Category:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    # --- Brand ---
    @atomic
    def create_brand(self, *, store, data: dict) -> Brand:
        slug = unique_slug(Brand, store=store, name=data["name"])
        return Brand.objects.create(store=store, slug=slug, **data)

    @atomic
    def update_brand(self, *, instance: Brand, data: dict) -> Brand:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    # --- Product ---
    @atomic
    def create_product(self, *, store, data: dict) -> Product:
        slug = unique_slug(Product, store=store, name=data["name"])
        product = Product.objects.create(store=store, slug=slug, **data)
        if product.status == ProductStatus.PUBLISHED and product.published_at is None:
            product.published_at = timezone.now()
            product.save(update_fields=["published_at"])
        return product

    @atomic
    def update_product(self, *, instance: Product, data: dict) -> Product:
        for field, value in data.items():
            setattr(instance, field, value)
        if instance.status == ProductStatus.PUBLISHED and instance.published_at is None:
            instance.published_at = timezone.now()
        instance.save()
        return instance

    # --- Variant ---
    @atomic
    def create_variant(self, *, store, product: Product, data: dict) -> ProductVariant:
        repo = ProductVariantRepository()
        sku = data["sku"]
        if repo.sku_exists(store=store, sku=sku):
            raise ConflictError(
                "A variant with this SKU already exists in this store.",
                code="sku_taken",
            )
        make_default = data.pop("is_default", False)
        # The first variant of a product is always the default.
        is_first = not product.variants.exists()
        variant = ProductVariant.objects.create(
            store=store, product=product, is_default=bool(make_default or is_first), **data
        )
        if variant.is_default:
            self._clear_other_defaults(product=product, keep=variant)
        return variant

    @atomic
    def update_variant(self, *, instance: ProductVariant, data: dict) -> ProductVariant:
        new_sku = data.get("sku")
        if new_sku and new_sku != instance.sku:
            repo = ProductVariantRepository()
            if repo.sku_exists(store=instance.store, sku=new_sku, exclude_pk=instance.pk):
                raise ConflictError(
                    "A variant with this SKU already exists in this store.",
                    code="sku_taken",
                )
        make_default = data.pop("is_default", None)
        for field, value in data.items():
            setattr(instance, field, value)
        if make_default is True:
            instance.is_default = True
        instance.save()
        if instance.is_default:
            self._clear_other_defaults(product=instance.product, keep=instance)
        return instance

    @staticmethod
    def _clear_other_defaults(*, product: Product, keep: ProductVariant) -> None:
        ProductVariant.objects.filter(product=product).exclude(pk=keep.pk).update(is_default=False)


class BundleService(BaseService):
    """Manage the components of bundle/kit/composite products."""

    def get_bundle(self, *, product_id) -> Product:
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            raise NotFoundError("Product not found.")
        if product.kind not in COMPOSITE_KINDS:
            raise BusinessRuleError(
                "This product is not a bundle, kit or composite.", code="not_a_bundle"
            )
        return product

    def list_components(self, bundle: Product):
        return bundle.components.select_related("component_variant").all()

    def get_component(self, *, bundle: Product, component_id) -> BundleComponent:
        component = bundle.components.filter(id=component_id).first()
        if component is None:
            raise NotFoundError("Bundle component not found.")
        return component

    @atomic
    def add_component(
        self,
        *,
        store,
        bundle: Product,
        component_variant_id,
        quantity: int = 1,
        is_optional: bool = False,
        sort_order: int = 0,
    ) -> BundleComponent:
        variant = (
            ProductVariant.objects.filter(id=component_variant_id).select_related("product").first()
        )
        if variant is None:
            raise ValidationError(
                "Component variant not found in this store.",
                code="variant_not_found",
                errors={"component_variant_id": ["Not found in this store."]},
            )
        if variant.product_id == bundle.id:
            raise BusinessRuleError("A bundle cannot contain itself.", code="self_component")
        if variant.product.kind in COMPOSITE_KINDS:
            raise BusinessRuleError(
                "Bundle components must be simple products (nested bundles are unsupported).",
                code="nested_bundle_unsupported",
            )
        if bundle.components.filter(component_variant=variant).exists():
            raise ConflictError("This component is already in the bundle.", code="component_exists")
        return BundleComponent.objects.create(
            store=store,
            bundle=bundle,
            component_variant=variant,
            quantity=quantity,
            is_optional=is_optional,
            sort_order=sort_order,
        )

    def remove_component(self, *, component: BundleComponent) -> None:
        component.delete()
