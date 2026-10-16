from django.contrib import admin, messages
from core.admin import BaseModelAdmin
from .forms import MaintenanceRuleAdminForm
from .models import MaintenanceReminderType, MaintenanceRule
from .services import MaintenanceRuleSeedService
from django import forms
from django.db.models import Q
from core.admin import BaseAdminForm


class MaintenanceRuleAdminForm(BaseAdminForm):

    keywords_text = forms.CharField(
        required=False,
        label="کلیدواژه‌ها",
        help_text=(
            "با ویرگول جدا کنید؛ مثال: تعویض روغن, روغن موتور. "
            "برای تطبیق همه رویدادها از * استفاده کنید."
        ),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
    )

    class Meta:
        model = MaintenanceRule
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_type_id = getattr(
            self.instance,
            "reminder_type_id",
            None,
        )

        queryset = MaintenanceReminderType.objects.filter(
            is_active=True,
        )

        if current_type_id:
            queryset = MaintenanceReminderType.objects.filter(
                Q(is_active=True)
                | Q(pk=current_type_id),
            )

        self.fields["reminder_type"].queryset = (
            queryset.order_by(
                "order",
                "title",
            )
        )

        self.fields["keywords_text"].initial = (
            ", ".join(
                self.instance.keywords or []
            )
        )

    @staticmethod
    def _parse_list(value):
        value = (value or "").strip()

        if not value:
            return []

        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    def clean(self):
        cleaned = super().clean()

        cleaned["keywords"] = self._parse_list(
            cleaned.pop("keywords_text", "")
        )

        return cleaned
    
@admin.register(MaintenanceReminderType)
class MaintenanceReminderTypeAdmin(BaseModelAdmin):

    list_display = (
        "title",
        "updated_at",
    )

    search_fields = (
        "title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "نوع یادآوری",
            {
                "fields": (
                    "title",
                ),
            },
        ),
        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

@admin.register(MaintenanceRule)
class MaintenanceRuleAdmin(BaseModelAdmin):

    form = MaintenanceRuleAdminForm

    class Media:
        js = (
            "assets/js/audit_inline.js",
            "assets/js/admin_number_formatter.js",
            "assets/js/admin_time_picker.js",
        )

        css = {
            "all": (
                "assets/css/admin_time_picker.css",
            ),
        }

    list_display = (
        "title",
        "reminder_type",
        "keywords_display",
        "interval_display",
        "send_window_display",
        "updated_at",
    )

    list_filter = (
        "reminder_type",
    )

    search_fields = (
        "title",
        "description",
    )

    autocomplete_fields = (
        "template",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "قاعده",
            {
                "fields": (
                    "title",
                    "description",
                    "reminder_type",
                    "keywords_text",
                ),
            },
        ),
        (
            "زمان‌بندی",
            {
                "fields": (
                    "interval_months",
                    "send_window_start",
                    "send_window_end",
                ),
            },
        ),
        (
            "ارسال",
            {
                "fields": (
                    "template",
                ),
            },
        ),
        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    # ------------------------------------------------------
    # Display
    # ------------------------------------------------------

    @admin.display(description="کلیدواژه‌ها")
    def keywords_display(self, obj):
        return "، ".join(obj.keywords or []) or "-"

    @admin.display(description="فاصله")
    def interval_display(self, obj):
        if obj.interval_months is None:
            return "-"
        return f"{obj.interval_months} ماه"

    @admin.display(description="بازه ارسال")
    def send_window_display(self, obj):
        if not obj.send_window_start or not obj.send_window_end:
            return "-"

        return (
            f"{obj.send_window_start.strftime('%H:%M')}"
            f" تا "
            f"{obj.send_window_end.strftime('%H:%M')}"
        )

    # ------------------------------------------------------
    # Actions
    # ------------------------------------------------------

    @admin.action(description="فعال کردن قواعد")
    def activate_rules(self, request, queryset):

        updated = queryset.update(
            is_active=True
        )

        self.message_user(
            request,
            f"{updated} قاعده فعال شد.",
            level=messages.SUCCESS,
        )

    @admin.action(description="غیرفعال کردن قواعد")
    def deactivate_rules(self, request, queryset):

        updated = queryset.update(
            is_active=False
        )

        self.message_user(
            request,
            f"{updated} قاعده غیرفعال شد.",
            level=messages.SUCCESS,
        )

    @admin.action(description="ساخت/به‌روزرسانی قواعد پیش‌فرض")
    def seed_default_rules(self, request, queryset):

        result = MaintenanceRuleSeedService.seed()

        self.message_user(
            request,
            (
                "قواعد پیش‌فرض آماده شد. "
                f"جدید: {result['created']} | "
                f"بروزرسانی: {result['updated']} | "
                f"انواع یادآوری: {result['reminder_types']}"
            ),
            level=messages.SUCCESS,
        )

    def save_model(self, request, obj, form, change):

        # فقط هنگام ایجاد قاعده جدید
        if not change:
            obj.automatic = True
            obj.is_active = True

        super().save_model(
            request,
            obj,
            form,
            change,
        )