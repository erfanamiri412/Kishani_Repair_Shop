from django.contrib import admin
from django.db import models
from core.admin import BaseModelAdmin
from django.core.exceptions import ValidationError
from users.models import User
from .models import (
    Attendance,
    DailyExpense,
    DailyIncome,
    DailyNote
)

@admin.register(Attendance)
class AttendanceAdmin(BaseModelAdmin):

    autocomplete_fields = (
        'employee',
    )

    list_display = (
        'employee',
        'status',
        'date',
        'check_in',
        'check_out',
        'worked_hours_display',
    )

    list_filter = (

        'status',
        'date',

    )

    search_fields = (

        'employee__user__first_name',
        'employee__user__last_name',
        'employee__user__username',
        'employee__phone',

    )

    readonly_fields = (
        'created_at',
    )

    ordering = (

        '-date',

    )

    list_per_page = 30

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ثبت کننده"
    )

    def worked_hours_display(self, obj):
        return obj.worked_hours

    worked_hours_display.short_description = "ساعت کار"
    list_per_page = 30

    def formfield_for_foreignkey(
        self,
        db_field,
        request,
        **kwargs,
    ):

        if db_field.name == "employee":

            from users.models import EmployeeProfile

            kwargs["queryset"] = (
                EmployeeProfile.objects
                # .filter(
                #     is_active_employee=True
                # )
                .select_related(
                    "user"
                )
                .order_by(
                    "user__first_name",
                    "user__last_name",
                )
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def clean(self):

        if Attendance.objects.filter(
            employee=self.employee,
            date=self.date,
        ).exclude(
            pk=self.pk
        ).exists():

            raise ValidationError(
                "برای این پرسنل در این تاریخ حضور ثبت شده است."
            )

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if not obj.pk:

            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )

@admin.register(DailyExpense)
class DailyExpenseAdmin(BaseModelAdmin):

    list_display = (

        'title',
        'formatted_amount',
        'expense_date',

    )

    list_filter = (

        'expense_date',

    )

    search_fields = (

        'title',
        'description',

    )

    ordering = (

        '-expense_date',
        '-id'
    )

    def changelist_view(
        self,
        request,
        extra_context=None,
    ):

        from django.db.models import Sum

        extra_context = extra_context or {}

        total = (
            DailyIncome.objects.aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        extra_context["total_income"] = total

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )

    @admin.display(
        description="مبلغ"
    )
    def formatted_amount(
        self,
        obj,
    ):

        return f"{obj.amount:,} تومان"

    def clean(self):

        if self.amount <= 0:

            raise ValidationError(
                "مبلغ باید بیشتر از صفر باشد."
            )
    
@admin.register(DailyIncome)
class DailyIncomeAdmin(BaseModelAdmin):

    list_display = (

        'title',
        'formatted_amount',
        'income_date',

    )

    list_filter = (

        'income_date',
        'id'

    )

    search_fields = (

        'title',
        'description',

    )

    ordering = (

        '-income_date',
        '-id'

    )

    list_per_page = 30

    def changelist_view(
        self,
        request,
        extra_context=None,
    ):

        from django.db.models import Sum

        extra_context = extra_context or {}

        total = (
            DailyIncome.objects.aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        extra_context["total_income"] = total

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )

    @admin.display(
        description="مبلغ"
    )
    def formatted_amount(
        self,
        obj,
    ):

        return f"{obj.amount:,} تومان"

    def clean(self):

        if self.amount <= 0:

            raise ValidationError(
                "مبلغ باید بیشتر از صفر باشد."
            )
