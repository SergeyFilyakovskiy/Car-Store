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


class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )


class HasRole(permissions.BasePermission):
    """
    Allow access only to users with a specific role.

    Usage:
        permission_classes = [HasRole("buyer")]
        permission_classes = [HasRole("supplier")]
        permission_classes = [HasRole("dealership")]
        permission_classes = [HasRole("admin")]
    """

    required_role = None

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == self.required_role
        )


class HasRoleOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to any authenticated user,
    but write access only to users with a specific role.

    Usage:
        permission_classes = [HasRoleOrReadOnly("buyer")]
        permission_classes = [HasRoleOrReadOnly("supplier")]
        permission_classes = [HasRoleOrReadOnly("dealership")]
    """

    required_role = None

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == self.required_role
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
