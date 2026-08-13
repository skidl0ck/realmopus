"""Shared DRF permission classes, keyed off accounts.User.role."""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAdminOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_accountant)
        )


class IsAdminOrSalesAgent(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_sales_agent)
        )


class IsStaff(permissions.BasePermission):
    """Any internal role: admin, sales_agent, or accountant — excludes clients."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in ("admin", "sales_agent", "accountant")
        )


class ReadOnlyOrIsStaff(permissions.BasePermission):
    """Public/client users can read (e.g. browse published lots); only staff can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in ("admin", "sales_agent", "accountant")
        )


class IsOwnerClientOrStaff(permissions.BasePermission):
    """Clients can only access objects tied to their own user; staff can access all."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in ("admin", "sales_agent", "accountant"):
            return True
        # Direct owner field (e.g. Contract.client, Reservation.client)...
        owner = getattr(obj, "client", None) or getattr(obj, "user", None)
        if owner is None:
            # ...or nested under a related contract (e.g. Payment.contract.client,
            # Receipt.payment.contract.client, Installment.contract.client).
            contract = getattr(obj, "contract", None) or getattr(
                getattr(obj, "payment", None), "contract", None
            )
            owner = getattr(contract, "client", None)
        return owner == user