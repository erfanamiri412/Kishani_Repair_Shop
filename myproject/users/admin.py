from django.contrib import admin
from django.contrib.auth.models import Group
from core.admin import BaseModelAdmin
from .models import (
    EmployeeProfile,
    SalaryPayment,
    SalaryRevision,
    SalaryAdvance,
    SalaryBonus,
    PayrollSnapshot,
)

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(BaseModelAdmin):

    autocomplete_fields = (
        "user",
    )

    list_display = (
        "user",
        "role",
        "phone",
        "payment_period",
        "fixed_salary_display",
    )

    list_filter = (
        "role",
        "payment_period",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    ordering = (
        "user__first_name",
    )

    list_per_page = 25

    fieldsets = (

        (
            "اطلاعات پرسنل",
            {
                "fields": (
                    "user",
                    "role",
                    "phone",
                )
            },
        ),

        (
            "اطلاعات حقوق و دستمزد",
            {
                "fields": (
                    "fixed_salary",
                    "payment_period",
                )
            },
        ),

        (
            "یادداشت",
            {
                "fields": (
                    "notes",
                )
            },
        ),

    )

    @admin.display(
        description="حقوق ثابت"
    )
    def fixed_salary_display(
        self,
        obj,
    ):

        return self.format_price(
            obj.fixed_salary
        )

@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(BaseModelAdmin):

    list_display = (
        "employee",
        "date",
        "amount_display",
        "paid_amount_display",
        "remaining_amount_display",
    )

    list_filter = (
        "date",
        "employee__role",
    )

    search_fields = (
        "employee__user__username",
        "employee__user__first_name",
        "employee__user__last_name",
        "description",
    )

    autocomplete_fields = (
        "employee",
    )

    readonly_fields = (
        "remaining_amount_display",
        "created_at",
    )

    ordering = (
        "-date",
        "-id",
    )

    fieldsets = (

        (
            "اطلاعات پرسنل",
            {
                "fields": (
                    "employee",
                )
            },
        ),

        (
            "اطلاعات قرض / علی‌الحساب",
            {
                "fields": (
                    "date",
                    "amount",
                    "paid_amount",
                )
            },
        ),

        (
            "توضیحات",
            {
                "fields": (
                    "description",
                )
            },
        ),

        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "created_at",
                )
            },
        ),

    )

    @admin.display(
        description="مبلغ قرض"
    )
    def amount_display(
        self,
        obj,
    ):

        return self.format_price(
            obj.amount
        )

    @admin.display(
        description="تسویه شده"
    )
    def paid_amount_display(
        self,
        obj,
    ):

        return self.format_price(
            obj.paid_amount
        )

    @admin.display(
        description="مانده"
    )
    def remaining_amount_display(
        self,
        obj,
    ):

        return self.format_price(
            obj.remaining_amount
        )

@admin.register(SalaryPayment)
class SalaryPaymentAdmin(BaseModelAdmin):

    list_display = (
        "employee",
        "start_date",
        "end_date",
        "amount_display",
        "payment_date",
    )

    list_filter = (
        "payment_date",
        "employee__role",
    )

    search_fields = (
        "employee__user__first_name",
        "employee__user__last_name",
        "employee__user__username",
    )

    autocomplete_fields = (
        "employee",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-payment_date",
        "-id",
    )

    fieldsets = (

        (
            "اطلاعات پرسنل",
            {
                "fields": (
                    "employee",
                )
            },
        ),

        (
            "بازه پرداختی",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),

        (
            "پرداخت",
            {
                "fields": (
                    "amount",
                    "payment_date",
                )
            },
        ),

        (
            "توضیحات",
            {
                "fields": (
                    "description",
                )
            },
        ),

        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "created_at",
                )
            },
        ),

    )

    @admin.display(
        description="مبلغ پرداختی"
    )
    def amount_display(
        self,
        obj,
    ):

        return self.format_price(
            obj.amount
        )
