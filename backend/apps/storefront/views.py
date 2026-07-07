"""Public storefront API (AllowAny): browse stores and their published catalog.

Cross-store and unauthenticated, so it uses the unscoped ``all_objects`` manager
with explicit ``is_deleted=False`` filters instead of the tenant-scoped default.
"""

from __future__ import annotations

from django.db.models import Avg, Count, Exists, F, Max, OuterRef, Prefetch, Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.core.exceptions import NotFoundError
from apps.core.mixins import BaseAPIView, BaseGenericAPIView
from apps.core.responses import APIResponse
from apps.inventory.models import StockItem
from apps.stores.models import Store, StoreStatus

from .serializers import (
    StorefrontProductDetailSerializer,
    StorefrontProductSerializer,
    StorefrontReviewSerializer,
    StorefrontStoreSerializer,
)

# Products that are visible in the public storefront.
_PUBLIC_PRODUCTS = Q(
    status=ProductStatus.PUBLISHED,
    is_deleted=False,
    store__status=StoreStatus.ACTIVE,
    store__is_deleted=False,
)

# Attach real warehouse stock to each variant so availability is computed without
# a per-variant query. The storefront is cross-store and unauthenticated, so it
# must use the unscoped ``all_objects`` manager.
_STOCK_PREFETCH = Prefetch(
    "variants__stock_items", queryset=StockItem.all_objects.filter(is_deleted=False)
)


def _in_stock_filter() -> Q:
    """Keep only products with a sellable active variant: an untracked one (always
    available, e.g. digital) or a tracked one holding net stock in some warehouse."""
    untracked = ProductVariant.all_objects.filter(
        product=OuterRef("pk"), is_active=True, is_deleted=False, track_inventory=False
    )
    tracked = StockItem.all_objects.filter(
        variant__product=OuterRef("pk"),
        variant__is_active=True,
        variant__track_inventory=True,
        is_deleted=False,
        quantity__gt=F("reserved_quantity"),
    )
    return Q(Exists(untracked)) | Q(Exists(tracked))


def _annotate_rating(qs):
    """Attach approved-review average + count so cards can show star ratings."""
    from apps.reviews.models import ReviewStatus

    approved = Q(reviews__status=ReviewStatus.APPROVED, reviews__is_deleted=False)
    return qs.annotate(
        rating_avg=Avg("reviews__rating", filter=approved),
        rating_count=Count("reviews", filter=approved),
    )


def _active_store_or_404(slug: str) -> Store:
    store = Store.all_objects.filter(slug=slug, status=StoreStatus.ACTIVE, is_deleted=False).first()
    if store is None:
        raise NotFoundError("Store not found.")
    return store


@extend_schema(tags=["Storefront"])
class StorefrontStoreListView(BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = StorefrontStoreSerializer

    def get_queryset(self):
        return Store.all_objects.filter(status=StoreStatus.ACTIVE, is_deleted=False).order_by(
            "name"
        )


@extend_schema(tags=["Storefront"])
class StorefrontStoreDetailView(BaseAPIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=StorefrontStoreSerializer)
    def get(self, request: Request, slug: str) -> Response:
        store = _active_store_or_404(slug)
        return APIResponse.success(
            StorefrontStoreSerializer(store, context={"request": request}).data
        )


@extend_schema(tags=["Storefront"])
class StorefrontCategoryListView(BaseAPIView):
    """Marketplace categories deduplicated by NAME across active stores, each with
    the total number of published products carrying that category name."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        rows = (
            Category.all_objects.filter(
                is_deleted=False,
                is_active=True,
                store__status=StoreStatus.ACTIVE,
                store__is_deleted=False,
            )
            # Dedup by the canonical `name` ONLY (the filter key), so the same
            # category never splits into two rows across stores. Take a single
            # representative English label via Max — a non-empty `name_en` wins
            # over an empty one — so English mode never falls back to Arabic when
            # *any* store provided the translation.
            .values("name")
            .annotate(
                en_label=Max("name_en"),
                product_count=Count(
                    "products",
                    filter=Q(products__status=ProductStatus.PUBLISHED, products__is_deleted=False),
                ),
            )
            .filter(product_count__gt=0)
            .order_by("name")
        )
        data = [
            {"name": r["name"], "name_en": r["en_label"] or "", "product_count": r["product_count"]}
            for r in rows
        ]
        return APIResponse.success(data)


@extend_schema(tags=["Storefront"])
class StorefrontAllProductsView(BaseGenericAPIView, generics.ListAPIView):
    """All published products across the marketplace.

    Optional filters: ``?category=<id>``, ``?store=<slug>``, ``?search=<q>``.
    """

    permission_classes = [AllowAny]
    serializer_class = StorefrontProductSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.all_objects.none()
        qs = _annotate_rating(
            Product.all_objects.filter(_PUBLIC_PRODUCTS)
            .select_related("store")
            .prefetch_related("variants", "images", _STOCK_PREFETCH)
        )
        params = self.request.query_params
        if params.get("category"):
            qs = qs.filter(category__name=params["category"])
        if params.get("store"):
            qs = qs.filter(store__slug=params["store"])
        if params.get("search"):
            term = params["search"]
            qs = qs.filter(Q(name__icontains=term) | Q(description__icontains=term))
        if params.get("on_sale"):
            qs = qs.filter(
                variants__is_active=True,
                variants__compare_at_price__gt=F("variants__price"),
            ).distinct()
        # Hide sold-out products (used by the home page so they don't take space).
        if params.get("in_stock"):
            qs = qs.filter(_in_stock_filter())
        return qs.order_by("-created_at")


@extend_schema(tags=["Storefront"])
class StorefrontProductListView(BaseGenericAPIView, generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = StorefrontProductSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Product.all_objects.none()
        store = _active_store_or_404(self.kwargs["slug"])
        qs = _annotate_rating(
            Product.all_objects.filter(
                store=store, status=ProductStatus.PUBLISHED, is_deleted=False
            )
            .select_related("store")
            .prefetch_related("variants", "images", _STOCK_PREFETCH)
        )
        if self.request.query_params.get("in_stock"):
            qs = qs.filter(_in_stock_filter())
        return qs.order_by("-created_at")


@extend_schema(tags=["Storefront"])
class StorefrontProductReviewsView(BaseAPIView):
    """Public approved reviews + rating summary for a product (no auth)."""

    permission_classes = [AllowAny]

    def get(self, request: Request, product_id) -> Response:
        from apps.reviews.models import Review, ReviewStatus

        qs = Review.all_objects.filter(
            product_id=product_id, status=ReviewStatus.APPROVED, is_deleted=False
        ).order_by("-created_at")
        agg = qs.aggregate(average=Avg("rating"), count=Count("id"))
        distribution = {str(i): 0 for i in range(1, 6)}
        for row in qs.values("rating").annotate(c=Count("id")):
            distribution[str(row["rating"])] = row["c"]
        summary = {
            "average_rating": round(float(agg["average"] or 0), 2),
            "count": agg["count"] or 0,
            "distribution": distribution,
        }
        return APIResponse.success(
            {"summary": summary, "results": StorefrontReviewSerializer(qs[:50], many=True).data}
        )


@extend_schema(tags=["Storefront"])
class StorefrontProductDetailView(BaseAPIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=StorefrontProductDetailSerializer)
    def get(self, request: Request, product_id) -> Response:
        product = (
            Product.all_objects.filter(
                id=product_id, status=ProductStatus.PUBLISHED, is_deleted=False
            )
            .select_related("store")
            .prefetch_related("variants", "images", _STOCK_PREFETCH)
            .first()
        )
        if product is None:
            raise NotFoundError("Product not found.")
        return APIResponse.success(
            StorefrontProductDetailSerializer(product, context={"request": request}).data
        )
