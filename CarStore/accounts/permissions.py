from rest_framework import permissions


class IsBuyer(permissions.BasePermission):
    """Allow access only to users with buyer role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "buyer"
        )


class IsSupplier(permissions.BasePermission):
    """Allow access only to users with supplier role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "supplier"
        )


class IsDealership(permissions.BasePermission):
    """Allow access only to users with dealership role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "dealership"
        )


class IsEmailVerified(permissions.BasePermission):
    """Allow access only to users with a verified email."""

    def has_permission(self, request, view):  # pyright: ignore[reportIncompatibleMethodOverride]
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_verified", None)
        )


class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )


class IsOwnerProfile(permissions.BasePermission):
    """
    Allow access to profile object only if the user is the owner.

    Requires profile model with `user_id` pointing to the user.
    Works for BuyerProfile, SupplierProfile, DealershipProfile, etc.

    Usage:
        permission_classes = [permissions.IsAuthenticated, IsOwnerProfile]
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
        if not (request.user and request.user.is_authenticated):
            return False
        return obj.user == request.user
