"""Catalog application services.

Own the catalog write-side business rules: per-store slug generation, product
status transitions, and product-variant invariants (unique SKU, exactly one
default variant per product).
"""

from __future__ import annotations

import itertools
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import (
    COMPOSITE_KINDS,
    Attribute,
    AttributeValue,
    Brand,
    BundleComponent,
    Category,
    DigitalAsset,
    DownloadGrant,
    LicenseKey,
    LicenseKeyStatus,
    Product,
    ProductAttribute,
    ProductKind,
    ProductStatus,
    ProductVariant,
    VariantOption,
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
        if "stock_quantity" in data:
            self._sync_variant_stock(store=store, variant=variant, quantity=data["stock_quantity"])
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
        if "stock_quantity" in data:
            self._sync_variant_stock(
                store=instance.store, variant=instance, quantity=data["stock_quantity"]
            )
        return instance

    @staticmethod
    def _clear_other_defaults(*, product: Product, keep: ProductVariant) -> None:
        ProductVariant.objects.filter(product=product).exclude(pk=keep.pk).update(is_default=False)

    def _sync_variant_stock(self, *, store, variant: ProductVariant, quantity) -> None:
        """Mirror the variant's form-entered ``stock_quantity`` into real warehouse
        inventory (a ``StockItem``), which is what actually gates storefront
        availability and checkout reservation. Without this a variant saved with a
        quantity still reads as out of stock. Untracked variants (e.g. digital) hold
        no physical stock and are always available, so they need no record."""
        if not variant.track_inventory or quantity is None:
            return
        from apps.inventory.services import InventoryService

        inventory = InventoryService()
        warehouse = InventoryService.default_warehouse(store=store)
        item = inventory.get_or_create_item(store=store, variant=variant, warehouse=warehouse)
        # Absolute set (adjust), but never below what carts have already reserved.
        target = max(int(quantity), item.reserved_quantity)
        if target != item.quantity:
            inventory.adjust(
                store=store,
                variant=variant,
                warehouse=warehouse,
                new_quantity=target,
                note="Stock set from product form",
            )


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


class DigitalProductService(BaseService):
    """Staff-side management of digital assets and license-key pools."""

    def get_variant(self, *, variant_id) -> ProductVariant:
        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant is None:
            raise NotFoundError("Product variant not found.")
        return variant

    def get_asset(self, *, variant) -> DigitalAsset | None:
        return DigitalAsset.objects.filter(variant=variant).first()

    @atomic
    def upsert_asset(self, *, store, variant, data: dict) -> DigitalAsset:
        asset, _ = DigitalAsset.objects.get_or_create(store=store, variant=variant)
        for field, value in data.items():
            setattr(asset, field, value)
        asset.save()
        return asset

    def list_license_keys(self, *, variant):
        return LicenseKey.objects.filter(variant=variant)

    @atomic
    def add_license_keys(self, *, store, variant, keys: list[str]) -> list[LicenseKey]:
        cleaned = [k.strip() for k in keys if k.strip()]
        if not cleaned:
            raise ValidationError("Provide at least one license key.", code="no_keys")
        existing = set(
            LicenseKey.all_objects.filter(
                store=store, key__in=cleaned, is_deleted=False
            ).values_list("key", flat=True)
        )
        duplicates = [k for k in cleaned if k in existing]
        if duplicates:
            raise ConflictError(
                f"These license keys already exist: {', '.join(duplicates)}",
                code="duplicate_keys",
            )
        return LicenseKey.objects.bulk_create(
            [LicenseKey(store=store, variant=variant, key=k) for k in dict.fromkeys(cleaned)]
        )


class DigitalFulfillmentService(BaseService):
    """Fulfil digital order items: assign license keys + create download grants.

    Invoked from ``CheckoutService.confirm_order`` inside its transaction, so any
    failure (e.g. insufficient license keys) rolls the confirmation back.
    """

    @atomic
    def fulfill(self, *, order) -> list[DownloadGrant]:
        grants: list[DownloadGrant] = []
        for item in order.items.select_related("variant"):
            asset = DigitalAsset.objects.filter(variant=item.variant, is_active=True).first()
            if asset is None:
                continue
            if asset.requires_license:
                self._assign_licenses(
                    asset=asset, order=order, user=order.user, quantity=item.quantity
                )
            grants.append(self._create_grant(order=order, asset=asset, variant=item.variant))
        return grants

    def _assign_licenses(self, *, asset, order, user, quantity: int) -> None:
        available = list(
            LicenseKey.objects.select_for_update().filter(
                variant=asset.variant, status=LicenseKeyStatus.AVAILABLE
            )[:quantity]
        )
        if len(available) < quantity:
            raise BusinessRuleError(
                "Not enough license keys available to fulfil this order.",
                code="insufficient_license_keys",
            )
        now = timezone.now()
        for license_key in available:
            license_key.status = LicenseKeyStatus.ASSIGNED
            license_key.assigned_order = order
            license_key.assigned_user = user
            license_key.assigned_at = now
            license_key.save(
                update_fields=[
                    "status",
                    "assigned_order",
                    "assigned_user",
                    "assigned_at",
                    "updated_at",
                ]
            )

    def _create_grant(self, *, order, asset, variant) -> DownloadGrant:
        expires_at = None
        if asset.download_expiry_days:
            expires_at = timezone.now() + timedelta(days=asset.download_expiry_days)
        return DownloadGrant.objects.create(
            store=order.store,
            order=order,
            user=order.user,
            variant=variant,
            digital_asset=asset,
            download_limit=asset.download_limit,
            expires_at=expires_at,
        )


class DownloadService(BaseService):
    """Buyer-side download access enforcing per-grant limits/expiry."""

    def get_grant(self, *, user, token) -> DownloadGrant:
        grant = (
            DownloadGrant.objects.filter(token=token, user=user)
            .select_related("digital_asset")
            .first()
        )
        if grant is None:
            raise NotFoundError("Download not found.")
        return grant

    @atomic
    def consume(self, *, grant: DownloadGrant) -> str:
        locked = DownloadGrant.objects.select_for_update().get(pk=grant.pk)
        if not locked.can_download():
            raise BusinessRuleError(
                "This download is no longer available (limit reached or expired).",
                code="download_unavailable",
            )
        locked.download_count += 1
        locked.save(update_fields=["download_count", "updated_at"])
        asset = locked.digital_asset
        return asset.download_url if asset else ""


class AttributeService(BaseService):
    """Manage attributes (variant axes) and their values."""

    @atomic
    def create_attribute(self, *, store, data: dict) -> Attribute:
        code = data.get("code")
        if code:
            if Attribute.all_objects.filter(store=store, code=code, is_deleted=False).exists():
                raise ConflictError(
                    "An attribute with this code already exists.", code="code_taken"
                )
        else:
            code = self._unique_code(store=store, name=data["name"])
        payload = {k: v for k, v in data.items() if k != "code"}
        return Attribute.objects.create(store=store, code=code, **payload)

    @atomic
    def update_attribute(self, *, instance: Attribute, data: dict) -> Attribute:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def get_attribute(self, *, attribute_id) -> Attribute:
        attribute = Attribute.objects.filter(id=attribute_id).first()
        if attribute is None:
            raise NotFoundError("Attribute not found.")
        return attribute

    def list_values(self, attribute: Attribute):
        return attribute.values.all()

    @atomic
    def add_value(self, *, store, attribute: Attribute, data: dict) -> AttributeValue:
        if attribute.values.filter(value=data["value"]).exists():
            raise ConflictError("This value already exists for the attribute.", code="value_exists")
        return AttributeValue.objects.create(store=store, attribute=attribute, **data)

    def _unique_code(self, *, store, name: str) -> str:
        base = slugify(name)[:110] or "attr"
        code = base
        suffix = 1
        while Attribute.all_objects.filter(store=store, code=code, is_deleted=False).exists():
            suffix += 1
            code = f"{base}-{suffix}"
        return code


class ConfigurableProductService(BaseService):
    """Declare attribute axes on configurable products and set variant options."""

    def list_product_attributes(self, product: Product):
        return product.product_attributes.select_related("attribute").all()

    @atomic
    def add_product_attribute(self, *, store, product: Product, attribute_id) -> ProductAttribute:
        if product.kind != ProductKind.CONFIGURABLE:
            raise BusinessRuleError(
                "Only configurable products can declare attributes.", code="not_configurable"
            )
        attribute = Attribute.objects.filter(id=attribute_id).first()
        if attribute is None:
            raise ValidationError(
                "Attribute not found in this store.",
                code="attribute_not_found",
                errors={"attribute_id": ["Not found in this store."]},
            )
        if product.product_attributes.filter(attribute=attribute).exists():
            raise ConflictError(
                "This attribute is already declared on the product.", code="attribute_declared"
            )
        return ProductAttribute.objects.create(store=store, product=product, attribute=attribute)

    @atomic
    def remove_product_attribute(self, *, product: Product, product_attribute_id) -> None:
        link = product.product_attributes.filter(id=product_attribute_id).first()
        if link is None:
            raise NotFoundError("Product attribute not found.")
        link.delete()

    @atomic
    def set_variant_options(self, *, store, variant: ProductVariant, attribute_value_ids: list):
        declared = set(variant.product.product_attributes.values_list("attribute_id", flat=True))
        values = list(
            AttributeValue.objects.filter(id__in=attribute_value_ids).select_related("attribute")
        )
        if len(values) != len(set(attribute_value_ids)):
            raise ValidationError(
                "One or more attribute values were not found.", code="value_not_found"
            )
        seen_attributes = set()
        for value in values:
            if value.attribute_id not in declared:
                raise ValidationError(
                    f"Attribute '{value.attribute.name}' is not declared on this product.",
                    code="attribute_not_declared",
                )
            if value.attribute_id in seen_attributes:
                raise ValidationError(
                    f"Multiple values supplied for attribute '{value.attribute.name}'.",
                    code="duplicate_attribute",
                )
            seen_attributes.add(value.attribute_id)

        variant.option_values.all().delete()
        VariantOption.objects.bulk_create(
            [
                VariantOption(
                    store=store, variant=variant, attribute=value.attribute, attribute_value=value
                )
                for value in values
            ]
        )
        return variant.option_values.select_related("attribute", "attribute_value").all()

    @atomic
    def generate_variant_matrix(
        self, *, store, product: Product, base_price, sku_prefix=None, selections=None
    ) -> list[ProductVariant]:
        """Create the Cartesian product of the product's declared attribute values.

        One variant per combination not already present (so it can be re-run after
        adding a value), each with its option coordinates and an auto-generated SKU.
        ``selections`` optionally restricts the values used per attribute id.
        """
        if product.kind != ProductKind.CONFIGURABLE:
            raise BusinessRuleError(
                "Only configurable products can generate a variant matrix.",
                code="not_configurable",
            )
        declared = list(
            product.product_attributes.select_related("attribute").order_by("sort_order")
        )
        if not declared:
            raise ValidationError(
                "Declare at least one attribute before generating variants.", code="no_attributes"
            )
        axes = []
        for product_attribute in declared:
            values = self._axis_values(product_attribute, selections)
            if not values:
                raise ValidationError(
                    f"Attribute '{product_attribute.attribute.name}' has no values to combine.",
                    code="no_values",
                )
            axes.append((product_attribute.attribute, values))

        existing = {
            frozenset(option.attribute_value_id for option in variant.option_values.all())
            for variant in product.variants.prefetch_related("option_values")
        }
        existing.discard(frozenset())

        prefix = (sku_prefix or product.slug or "var").strip()
        price = Decimal(str(base_price))
        taken = set(
            ProductVariant.all_objects.filter(store=store, is_deleted=False).values_list(
                "sku", flat=True
            )
        )
        has_default = product.variants.filter(is_default=True).exists()
        created: list[ProductVariant] = []
        for combo in itertools.product(*[values for _, values in axes]):
            signature = frozenset(value.id for value in combo)
            if signature in existing:
                continue
            sku = self._matrix_sku(prefix, combo, taken)
            taken.add(sku)
            variant = ProductVariant.objects.create(
                store=store,
                product=product,
                sku=sku,
                price=price,
                is_default=(not has_default and not created),
            )
            VariantOption.objects.bulk_create(
                [
                    VariantOption(
                        store=store, variant=variant, attribute=attribute, attribute_value=value
                    )
                    for (attribute, _values), value in zip(axes, combo, strict=False)
                ]
            )
            existing.add(signature)
            created.append(variant)
        return created

    @staticmethod
    def _axis_values(product_attribute, selections):
        values = list(product_attribute.attribute.values.all())
        if selections:
            wanted = selections.get(str(product_attribute.attribute_id))
            if wanted:
                wanted_ids = {str(value_id) for value_id in wanted}
                values = [value for value in values if str(value.id) in wanted_ids]
        return values

    @staticmethod
    def _matrix_sku(prefix, combo, taken) -> str:
        parts = [slugify(value.value or value.label or str(value.id))[:12] for value in combo]
        base = "-".join([prefix, *parts]).upper()
        sku = base
        index = 1
        while sku in taken:
            index += 1
            sku = f"{base}-{index}"
        return sku
