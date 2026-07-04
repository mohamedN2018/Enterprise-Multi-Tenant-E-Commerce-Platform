"""Store (tenant) domain models.

A ``Store`` is the tenant boundary for the platform. Every store-scoped resource
(catalog, inventory, orders, …) references a store and is isolated via the
tenant-aware managers (see :class:`apps.core.models.TenantOwnedModel`).

* ``Store``            — the tenant: identity, status, branding, localisation.
* ``StoreSettings``    — 1:1 operational configuration (tax / inventory / units).
* ``StoreMembership``  — User↔Store with a role; the RBAC backbone.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class StoreStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    CLOSED = "closed", "Closed"


class StoreRole(models.TextChoices):
    OWNER = "owner", "Owner"
    MANAGER = "manager", "Manager"
    EMPLOYEE = "employee", "Employee"


class Store(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_stores",
    )
    status = models.CharField(
        max_length=16,
        choices=StoreStatus.choices,
        default=StoreStatus.DRAFT,
        db_index=True,
    )
    description = models.TextField(blank=True)

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)

    # Branding
    logo = models.ImageField(upload_to="stores/logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="stores/banners/", null=True, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True, editable=False)

    # Localisation
    currency = models.CharField(max_length=3, default="USD")
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=64, default="UTC")
    country = models.CharField(max_length=2, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Store"
        verbose_name_plural = "Stores"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "is_verified"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_operational(self) -> bool:
        return self.status == StoreStatus.ACTIVE and not self.is_deleted

    def mark_verified(self) -> None:
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=["is_verified", "verified_at", "updated_at"])


class StoreSettings(BaseModel):
    class WeightUnit(models.TextChoices):
        KILOGRAM = "kg", "Kilogram"
        POUND = "lb", "Pound"

    class DimensionUnit(models.TextChoices):
        CENTIMETER = "cm", "Centimeter"
        INCH = "in", "Inch"

    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name="settings")

    # Tax
    tax_inclusive_pricing = models.BooleanField(default=False)
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Inventory
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    # Units & numbering
    weight_unit = models.CharField(
        max_length=4, choices=WeightUnit.choices, default=WeightUnit.KILOGRAM
    )
    dimension_unit = models.CharField(
        max_length=4, choices=DimensionUnit.choices, default=DimensionUnit.CENTIMETER
    )
    order_number_prefix = models.CharField(max_length=12, default="ORD")

    # Team size cap: max employees the store may add. Set by a platform admin per
    # the agreement; the seller requests raises. Enforced in MembershipService.
    max_employees = models.PositiveIntegerField(
        default=1,
        help_text="Maximum employees this store may add (set by a platform admin).",
    )

    # Extensible bag for forward-compatible settings.
    metadata = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Store settings"
        verbose_name_plural = "Store settings"

    def __str__(self) -> str:
        return f"Settings for {self.store_id}"


class StoreMembership(BaseModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store_memberships",
    )
    role = models.CharField(
        max_length=16, choices=StoreRole.choices, default=StoreRole.EMPLOYEE, db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Store membership"
        verbose_name_plural = "Store memberships"
        constraints = [
            models.UniqueConstraint(fields=["store", "user"], name="unique_store_user_membership")
        ]
        indexes = [
            models.Index(fields=["store", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.store_id} ({self.role})"

    @property
    def is_owner(self) -> bool:
        return self.role == StoreRole.OWNER

    @property
    def can_manage(self) -> bool:
        return self.role in {StoreRole.OWNER, StoreRole.MANAGER}


class LimitRequestKind(models.TextChoices):
    EMPLOYEES = "employees", "Employees"
    STORES = "stores", "Stores"


class LimitRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class LimitRequest(BaseModel):
    """A seller's request to a platform admin to raise a cap (employees or stores).

    Not tenant-scoped: a platform admin lists these across every store, while a
    store owner sees only their own store's requests.
    """

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="limit_requests"
    )
    # Set for employee requests; null for account-level store-count requests.
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, null=True, blank=True, related_name="limit_requests"
    )
    kind = models.CharField(
        max_length=16, choices=LimitRequestKind.choices, default=LimitRequestKind.EMPLOYEES,
        db_index=True,
    )
    current_limit = models.PositiveIntegerField(default=0)
    requested_limit = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=LimitRequestStatus.choices,
        default=LimitRequestStatus.PENDING, db_index=True,
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Limit request"
        verbose_name_plural = "Limit requests"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "kind"])]

    def __str__(self) -> str:
        return f"{self.kind} {self.current_limit}->{self.requested_limit} ({self.status})"
