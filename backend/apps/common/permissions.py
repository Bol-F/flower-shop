from rest_framework.permissions import BasePermission, SAFE_METHODS


def staff_has_model_permissions(user, *permissions):
    """The staff flag opens the admin site; it does not grant access to its data."""
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.is_staff
        and permissions
        and user.has_perms(permissions)
    )


class HasStaffModelPermissions(BasePermission):
    """Require every model permission explicitly declared by a staff API view."""

    def has_permission(self, request, view):
        return staff_has_model_permissions(request.user, *getattr(view, 'staff_permissions', ()))


class IsAdminOrReadOnly(BasePermission):
    """Public reads; model-specific add/change/delete permissions for staff writes."""

    method_actions = {'POST': 'add', 'PUT': 'change', 'PATCH': 'change', 'DELETE': 'delete'}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        action = self.method_actions.get(request.method)
        model = getattr(getattr(view, 'queryset', None), 'model', None)
        if not action or model is None:
            return False
        return staff_has_model_permissions(
            request.user, f'{model._meta.app_label}.{action}_{model._meta.model_name}'
        )


class IsOwnerOrAdmin(BasePermission):
    """Owners retain access; staff need the view's explicit model permissions."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        return obj.user_id == user.pk or staff_has_model_permissions(
            user, *getattr(view, 'staff_permissions', ())
        )


class IsCustomer(BasePermission):
    """Authenticated non-staff users only — staff are support, not customers."""

    message = 'Staff accounts reply from the admin dashboard, not the support chat.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_staff)
