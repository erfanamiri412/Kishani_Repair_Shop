from dataclasses import dataclass

from django.contrib.auth.models import (
    Group,
    Permission,
)

from django.contrib.contenttypes.models import (
    ContentType,
)
from django.contrib.contenttypes.models import ContentType


# ==========================================================
# Permission Definition
# ==========================================================

@dataclass(frozen=True)
class PermissionDefinition:

    codename: str
    title: str
    module: str
    description: str = ""
    dangerous: bool = False

    @property
    def django_codename(self):
        return self.codename.split(".")[-1]

# ==========================================================
# Base Module
# ==========================================================

class PermissionModules:

    CUSTOMERS = "customers"

    REPAIRS = "repairs"

    INVENTORY = "inventory"

    FINANCE = "finance"

    REPORTS = "reports"

    SYSTEM = "system"


    META = {

        CUSTOMERS: {

            "title": "مشتریان",

            "icon": "bi-people",

            "order": 1,

        },

        REPAIRS: {

            "title": "تعمیرات",

            "icon": "bi-tools",

            "order": 2,

        },

        INVENTORY: {

            "title": "انبار",

            "icon": "bi-box-seam",

            "order": 3,

        },

        FINANCE: {

            "title": "مالی",

            "icon": "bi-cash-stack",

            "order": 4,

        },

        REPORTS: {

            "title": "گزارش‌ها",

            "icon": "bi-bar-chart",

            "order": 5,

        },

        SYSTEM: {

            "title": "سیستم",

            "icon": "bi-gear",

            "order": 6,

        },

    }

    @classmethod
    def meta(cls, module):

        return cls.META[module]
    
class BasePermissionModule:

    module = None

    permissions_list = []

    @classmethod
    def permissions(cls):
        result = []

        for value in cls.__dict__.values():
            if isinstance(value, PermissionDefinition):
                result.append(value)

        return result

    @classmethod
    def codenames(cls):

        return [

            permission.codename

            for permission in cls.permissions()

        ]

    @classmethod
    def meta(cls):

        return PermissionModules.meta(

            cls.module

        )
    
# ==========================================================
# Customers
# ==========================================================

class CustomersPermissions(BasePermissionModule):
    
    module = PermissionModules.CUSTOMERS
    CATEGORY = "مشتریان"

    VIEW = PermissionDefinition(
        "crm.view_customers",
        "مشاهده مشتریان",
        CATEGORY,
    )

    CREATE = PermissionDefinition(
        "crm.create_customer",
        "ثبت مشتری",
        CATEGORY,
    )

    EDIT = PermissionDefinition(
        "crm.edit_customer",
        "ویرایش مشتری",
        CATEGORY,
    )

    DELETE = PermissionDefinition(
        "crm.delete_customer",
        "حذف مشتری",
        CATEGORY,
    )

    VIEW_HISTORY = PermissionDefinition(
        "crm.view_customer_history",
        "مشاهده سوابق مشتری",
        CATEGORY,
    )

    MANAGE_VEHICLES = PermissionDefinition(
        "crm.manage_customer_vehicles",
        "مدیریت خودروهای مشتری",
        CATEGORY,
    )

# ==========================================================
# Repairs
# ==========================================================

class RepairsPermissions(BasePermissionModule):
    
    module = PermissionModules.REPAIRS
    CATEGORY = "تعمیرات"

    VIEW_REQUESTS = PermissionDefinition(
        "crm.view_service_requests",
        "مشاهده درخواست‌های تعمیر",
        CATEGORY,
    )

    CREATE_REQUEST = PermissionDefinition(
        "crm.create_service_request",
        "ثبت درخواست تعمیر",
        CATEGORY,
    )

    EDIT_REQUEST = PermissionDefinition(
        "crm.edit_service_request",
        "ویرایش درخواست تعمیر",
        CATEGORY,
    )

    REGISTER_REPAIR = PermissionDefinition(
        "crm.register_repair",
        "ثبت عملیات تعمیر",
        CATEGORY,
    )

    DELIVER_VEHICLE = PermissionDefinition(
        "crm.deliver_vehicle",
        "تحویل خودرو",
        CATEGORY,
    )


# ==========================================================
# Inventory
# ==========================================================

class InventoryPermissions(BasePermissionModule):
    
    module = PermissionModules.INVENTORY
    CATEGORY = "انبار"

    VIEW = PermissionDefinition(
        "crm.view_inventory",
        "مشاهده موجودی قطعات",
        CATEGORY,
    )

    MANAGE = PermissionDefinition(
        "crm.manage_inventory",
        "مدیریت موجودی قطعات",
        CATEGORY,
    )

    CONSUME_PARTS = PermissionDefinition(
        "crm.consume_parts",
        "ثبت مصرف قطعات",
        CATEGORY,
    )


# ==========================================================
# Finance
# ==========================================================

class FinancePermissions(BasePermissionModule):
    
    module = PermissionModules.FINANCE
    CATEGORY = "مالی"

    VIEW_INVOICES = PermissionDefinition(
        "crm.view_invoices",
        "مشاهده فاکتورها",
        CATEGORY,
    )

    CREATE_INVOICE = PermissionDefinition(
        "crm.create_invoice",
        "صدور فاکتور",
        CATEGORY,
    )

    REGISTER_PAYMENT = PermissionDefinition(
        "crm.register_payment",
        "ثبت پرداخت مشتری",
        CATEGORY,
    )

    EDIT_PAYMENT = PermissionDefinition(
        "crm.edit_payment",
        "ویرایش پرداخت",
        CATEGORY,
    )


# ==========================================================
# Reports
# ==========================================================

class ReportsPermissions(BasePermissionModule):

    module = PermissionModules.REPORTS
    CATEGORY = "گزارشات"

    VIEW = PermissionDefinition(
        "crm.view_reports",
        "مشاهده گزارشات",
        CATEGORY,
    )

    EXPORT = PermissionDefinition(
        "crm.export_reports",
        "خروجی گرفتن از گزارشات",
        CATEGORY,
    )


# ==========================================================
# System
# ==========================================================

class SystemPermissions(BasePermissionModule):

    module = PermissionModules.SYSTEM
    CATEGORY = "سیستم"

    MANAGE_USERS = PermissionDefinition(
        "crm.manage_users",
        "مدیریت کاربران",
        CATEGORY,
    )

    MANAGE_ROLES = PermissionDefinition(
        "crm.manage_roles",
        "مدیریت نقش‌ها و دسترسی‌ها",
        CATEGORY,
    )

    MANAGE_SETTINGS = PermissionDefinition(
        "crm.manage_settings",
        "مدیریت تنظیمات سیستم",
        CATEGORY,
    )

    VIEW_AUDIT_LOG = PermissionDefinition(
        "crm.view_audit_log",
        "مشاهده لاگ سیستم",
        CATEGORY,
    )


# ==========================================================
# Registry
# ==========================================================

class PermissionRegistry:

    MODULES = [

        CustomersPermissions,

        RepairsPermissions,

        InventoryPermissions,

        FinancePermissions,

        ReportsPermissions,

        SystemPermissions,

    ]

    @classmethod
    def modules(cls):

        return cls.MODULES

    @classmethod
    def permission_codenames(cls):

        result = []

        for module in cls.MODULES:

            result.extend([
                permission.django_codename
                for permission in module.permissions()
            ])

        return result
    
    @classmethod
    def permission_codes(cls):

        result = []

        for module in cls.MODULES:

            result.extend(
                module.permissions()
            )

        return result
# ==========================================================
# Roles
# ==========================================================

class CRMRoles:
    """
    System Roles

    هر Role فقط ماژول‌ها را می‌شناسد.
    """

    MANAGER = "manager"

    MECHANIC = "mechanic"

    LABELS = {

        MANAGER: "مدیر",

        MECHANIC: "مکانیک",

    }


    ROLES = {

        MANAGER: [

            CustomersPermissions,

            RepairsPermissions,

            InventoryPermissions,

            FinancePermissions,

            ReportsPermissions,

            SystemPermissions,

        ],

        MECHANIC: [

            CustomersPermissions,

            RepairsPermissions,

            InventoryPermissions,

        ],

    }

    @classmethod
    def names(cls):

        return list(

            cls.ROLES.keys()

        )

    @classmethod
    def modules(

        cls,

        role,

    ):

        return cls.ROLES.get(

            role,

            [],

        )

    @classmethod
    def label(cls, role):

        return cls.LABELS[role]

    @classmethod
    def permissions(

        cls,

        role,

    ):

        permissions = []

        for module in cls.modules(

            role

        ):

            permissions.extend(

                module.permissions()

            )

        return permissions

    @classmethod
    def permission_codenames(
        cls,
        role,
    ):
        return [
            permission.django_codename
            for permission in cls.permissions(
                role
            )
        ]

    @classmethod
    def permission_codenames(

        cls,

        role,

    ):

        return [

            permission.codename

            for permission in cls.permissions(

                role

            )

        ]

    @classmethod
    def label(cls, role):

        return cls.LABELS.get(role, role)

    @classmethod
    def exists(

        cls,

        role,

    ):

        return role in cls.ROLES
    

# ==========================================================
# Permission Helper
# ==========================================================

class PermissionHelper:
    """
    Central Permission Helper

    تمام پروژه فقط باید از این کلاس استفاده کند.
    """

    # ------------------------------------------------------

    @classmethod
    def all_permissions(cls):

        return PermissionRegistry.permission_codes()

    # ------------------------------------------------------

    @classmethod
    def all_codes(cls):

        return PermissionRegistry.permission_codes()

    # ------------------------------------------------------

    @classmethod
    def all_codenames(cls):

        return PermissionRegistry.permission_codenames()

    # ------------------------------------------------------

    @classmethod
    def role_permissions(

        cls,

        role,

    ):

        return CRMRoles.permissions(

            role

        )

    # ------------------------------------------------------

    @classmethod
    def role_codes(

        cls,

        role,

    ):

        return CRMRoles.permission_codes(

            role

        )

    # ------------------------------------------------------

    @classmethod
    def role_codenames(

        cls,

        role,

    ):

        return CRMRoles.permission_codenames(

            role

        )

    # ------------------------------------------------------

    @classmethod
    def category_permissions(

        cls,

        category,

    ):

        return PermissionRegistry.by_category(

            category

        )

    # ------------------------------------------------------

    @classmethod
    def find(

        cls,

        code,

    ):

        return PermissionRegistry.find(

            code

        )

    # ------------------------------------------------------

    @classmethod
    def exists(

        cls,

        code,

    ):

        return PermissionRegistry.exists(

            code

        )

    # ------------------------------------------------------

    @classmethod
    def categories(cls):

        return PermissionRegistry.categories()

    # ------------------------------------------------------

    @classmethod
    def role_exists(

        cls,

        role,

    ):

        return CRMRoles.exists(

            role

        )

    # ------------------------------------------------------

    @classmethod
    def role_modules(

        cls,

        role,

    ):

        return CRMRoles.modules(

            role

        )

    # ------------------------------------------------------

    @classmethod
    def grouped_permissions(cls):

        grouped = {}

        for module in PermissionRegistry.modules():

            grouped[module.module] = {

                "title": module.meta()["title"],

                "icon": module.meta()["icon"],

                "order": module.meta()["order"],

                "permissions": module.permissions(),

            }

        return grouped

    @classmethod
    def all_modules(cls):

        return PermissionRegistry.modules()

# ==========================================================
# Seeder
# ==========================================================

class PermissionSeeder:
    """
    ساخت و همگام‌سازی Permission ها و Group ها
    """

    @classmethod
    def sync(cls):

        cls.sync_permissions()
        cls.sync_roles()

    # -----------------------------------------------------

    @classmethod
    def sync_permissions(cls):

        from crm.models import Customer
        content_type = ContentType.objects.get_for_model(
            Customer
        )

        for permission in PermissionHelper.all_permissions():

            Permission.objects.update_or_create(

                codename=permission.django_codename,

                content_type=content_type,

                defaults={
                    "name": permission.title,
                },
            )

    # -----------------------------------------------------

    @classmethod
    def sync_roles(cls):
        from crm.models import Customer

        permission_ct = ContentType.objects.get_for_model(Customer)

        for role in CRMRoles.names():
            group, _ = Group.objects.get_or_create(
                name=CRMRoles.label(role)
            )

            codenames = {
                permission.django_codename
                for permission in CRMRoles.permissions(role)
            }

            permissions = Permission.objects.filter(
                content_type=permission_ct,
                codename__in=codenames,
            )

            found_codenames = set(
                permissions.values_list("codename", flat=True)
            )

            missing_codenames = codenames - found_codenames

            if missing_codenames:
                raise ValueError(
                    "مجوزهای زیر برای مدل Customer ثبت نشده‌اند: "
                    + ", ".join(sorted(missing_codenames))
                )

            group.permissions.set(permissions)
            
    # -----------------------------------------------------

    @classmethod
    def rebuild(cls):

        cls.sync()



    help = (
        "Synchronize CRM permissions."
    )

    def handle(self, *args, **options):

        PermissionSeeder.sync()

        self.stdout.write(

            self.style.SUCCESS(

                "Permissions synchronized successfully."

            )

        )

# ==========================================================

class PermissionChecker:
    """
    هسته بررسی دسترسی‌ها.

    از این کلاس در کل پروژه استفاده می‌شود.
    """

    @staticmethod
    def has(user, codename: str) -> bool:

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.has_perm(codename)

    @staticmethod
    def has_any(user, permissions) -> bool:

        return any(

            PermissionChecker.has(user, permission)

            for permission in permissions

        )

    @staticmethod
    def has_all(user, permissions) -> bool:

        return all(

            PermissionChecker.has(user, permission)

            for permission in permissions

        )

    @staticmethod
    def user_permissions(user):

        if not user.is_authenticated:

            return set()

        return {

            permission.codename

            for permission in user.user_permissions.all()

        }

    @staticmethod
    def group_permissions(user):

        if not user.is_authenticated:

            return set()

        permissions = set()

        for group in user.groups.prefetch_related("permissions"):

            permissions.update(

                permission.codename

                for permission in group.permissions.all()

            )

        return permissions

    @staticmethod
    def all_permissions(user):

        return (

            PermissionChecker.user_permissions(user)

            |

            PermissionChecker.group_permissions(user)

        )