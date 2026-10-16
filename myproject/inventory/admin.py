from django.contrib import admin
from .models import Part, Supplier
from core.admin import BaseModelAdmin

@admin.register(Supplier)
class SupplierAdmin(BaseModelAdmin):

    list_display = (
        "name",
        "phone",
    )

    search_fields = (
        "name",
        "phone",
    )

@admin.register(Part)
class PartAdmin(BaseModelAdmin):

    list_display = (
        "title",
        "category",
        "brand",
        "stock",
        "minimum_stock",
        "purchase_price",
        "sale_price",
        "need_restock_status",
    )

    list_filter = (
        "category",
        "brand",
    )

    search_fields = (
        "title",
        "brand",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "title",
    )

    list_per_page = 30

    fieldsets = (

        ("مشخصات قطعه", {
            "fields": (
                "title",
                "category",
                "brand",
            )
        }),

        ("تأمین و خرید", {
            "fields": (
                "supplier",
                "purchase_price",
            )
        }),

        ("فروش و موجودی", {
            "fields": (
                "sale_price",
                "stock",
                "minimum_stock",
            )
        }),

        ("وضعیت قطعه", {
            "fields": (
                "description",
            )
        }),

        ("اطلاعات سیستمی", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),

    )

    @admin.display(description=" موجودی")
    def need_restock_status(self, obj):

        if obj.stock <= obj.minimum_stock:
            return "⚠ "

        return "✅"