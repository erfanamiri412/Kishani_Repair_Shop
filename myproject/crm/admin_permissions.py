from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from crm.permissions import (
    PermissionHelper,
    CRMRoles,
)


@admin.register(Group)
class CRMGroupAdmin(admin.ModelAdmin):

    exclude = (
        "permissions",
    )

    list_display = (

        "name",

        "permissions_count",

    )

    ordering = (

        "name",

    )

    search_fields = (

        "name",

    )

    filter_horizontal = (

        "permissions",

    )

    # def save_model(
    #     self,
    #     request,
    #     obj,
    #     form,
    #     change,
    # ):

    #     super().save_model(
    #         request,
    #         obj,
    #         form,
    #         change,
    #     )

    #     if not change:

    #         role = obj.name.lower()

    #         if CRMRoles.exists(role):

    #             permissions = Permission.objects.filter(
    #                 codename__in=
    #                 CRMRoles.permission_codenames(role)
    #             )

    #             obj.permissions.set(
    #                 permissions
    #             )

    def permissions_count(

        self,

        obj,

    ):

        return obj.permissions.count()

    permissions_count.short_description = "تعداد دسترسی‌ها"

    # def formfield_for_manytomany(

    #     self,

    #     db_field,

    #     request,

    #     **kwargs,

    # ):

    #     if db_field.name == "permissions":

    #         allowed = PermissionHelper.all_codenames()

    #         kwargs["queryset"] = Permission.objects.filter(

    #             pk__in=[

    #                 permission.pk

    #                 for permission in self.get_permission_queryset()

    #             ]

    #         )

    #     return super().formfield_for_manytomany(

    #         db_field,

    #         request,

    #         **kwargs,

    #     )
    
    def get_permission_queryset(self):

        permissions = list(

            Permission.objects.filter(

                codename__in=PermissionHelper.all_codenames()

            )

        )

        modules = PermissionHelper.grouped_permissions()

        module_order = {

            module: data["order"]

            for module, data in modules.items()

        }

        permission_order = {}

        index = 0

        for module in PermissionHelper.all_modules():

            for permission in module.permissions():

                permission_order[

                    permission.codename

                ] = index

                index += 1

        permissions.sort(

            key=lambda permission: (

                module_order.get(

                    PermissionHelper.find(

                        f"{permission.content_type.app_label}.{permission.codename}"

                    ).module,

                    999,

                ),

                permission_order.get(

                    permission.codename,

                    999,

                ),

            )

        )

        return permissions
    
    def get_form(

        self,

        request,

        obj=None,

        **kwargs,

    ):

        form = super().get_form(

            request,

            obj,

            **kwargs,

        )

        if "permissions" in form.base_fields:

            permissions = form.base_fields["permissions"]

            permissions.label = "دسترسی‌های نقش"

            permissions.help_text = (
                "دسترسی‌هایی که این نقش خواهد داشت."
            )

        if "name" in form.base_fields:

            form.base_fields["name"].label = "نام نقش"

            form.base_fields["name"].help_text = (
                "نام نقش سیستمی"
            )

        return form
        
    def change_view(

        self,

        request,

        object_id,

        form_url="",

        extra_context=None,

    ):

        extra_context = extra_context or {}

        extra_context["title"] = "مدیریت نقش"

        return super().change_view(

            request,

            object_id,

            form_url,

            extra_context,

        )
    
    def has_add_permission(

        self,

        request,

    ):

        return False
    
    def has_delete_permission(

        self,

        request,

        obj=None,

    ):

        return False
    
    readonly_fields = (
        "name",
    )