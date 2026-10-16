from crm.permissions import CRMPermissions
from functools import wraps

from django.core.exceptions import PermissionDenied

from .permissions import PermissionChecker

class Authorization:

    @staticmethod
    def has_permission(
        *,
        user,
        permission,
    ):

        if user.is_superuser:
            return True

        return user.has_perm(
            permission.value.split(".")[-1]
        )

    # ===========================
    # Customers
    # ===========================

    @classmethod
    def can_view_customers(
        cls,
        *,
        user,
    ):

        return cls.has_permission(

            user=user,

            permission=CRMPermissions.VIEW_CUSTOMERS,

        )

    @classmethod
    def can_create_customer(
        cls,
        *,
        user,
    ):

        return cls.has_permission(

            user=user,

            permission=CRMPermissions.CREATE_CUSTOMER,

        )

    @classmethod
    def can_edit_customer(
        cls,
        *,
        user,
    ):

        return cls.has_permission(

            user=user,

            permission=CRMPermissions.EDIT_CUSTOMER,

        )

    # ===========================
    # Repairs
    # ===========================

    @classmethod
    def can_register_repair(
        cls,
        *,
        user,
    ):

        return cls.has_permission(

            user=user,

            permission=CRMPermissions.REGISTER_REPAIR,

        )

    @classmethod
    def can_register_payment(
        cls,
        *,
        user,
    ):

        return cls.has_permission(

            user=user,

            permission=CRMPermissions.REGISTER_PAYMENT,

        )

    @classmethod
    def can_view_reports(
        cls,
        *,
        user,
    ):

        return cls.has_permission(

            user=user,

            permission=CRMPermissions.VIEW_REPORTS,

        )
    
    def require_permission(permission):

        """
        بررسی یک Permission
        """

        def decorator(view):

            @wraps(view)
            def wrapper(request, *args, **kwargs):

                if not PermissionChecker.has(

                    request.user,

                    permission,

                ):

                    raise PermissionDenied(
                        "شما اجازه انجام این عملیات را ندارید."
                    )

                return view(

                    request,

                    *args,

                    **kwargs,

                )

            return wrapper

        return decorator

    def require_any_permission(*permissions):

        """
        داشتن حداقل یکی از Permissionها
        """

        def decorator(view):

            @wraps(view)
            def wrapper(request, *args, **kwargs):

                if not PermissionChecker.has_any(

                    request.user,

                    permissions,

                ):

                    raise PermissionDenied(
                        "شما اجازه انجام این عملیات را ندارید."
                    )

                return view(

                    request,

                    *args,

                    **kwargs,

                )

            return wrapper

        return decorator

    def require_all_permissions(*permissions):

        """
        داشتن تمام Permissionها
        """

        def decorator(view):

            @wraps(view)
            def wrapper(request, *args, **kwargs):

                if not PermissionChecker.has_all(

                    request.user,

                    permissions,

                ):

                    raise PermissionDenied(
                        "شما اجازه انجام این عملیات را ندارید."
                    )

                return view(

                    request,

                    *args,

                    **kwargs,

                )

            return wrapper

        return decorator
    
    def require_role(*roles):

        """
        فقط نقش‌های مشخص شده
        """

        def decorator(view):

            @wraps(view)
            def wrapper(request, *args, **kwargs):

                if request.user.is_superuser:

                    return view(

                        request,

                        *args,

                        **kwargs,

                    )

                user_roles = {

                    group.name

                    for group in request.user.groups.all()

                }

                if not user_roles.intersection(roles):

                    raise PermissionDenied(
                        "شما اجازه انجام این عملیات را ندارید."
                    )

                return view(

                    request,

                    *args,

                    **kwargs,

                )

            return wrapper

        return decorator