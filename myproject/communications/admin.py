from django.contrib import admin, messages
from django.utils import timezone

from core.admin import BaseModelAdmin

from .forms import CommunicationTemplateAdminForm, SmsCampaignAdminForm
from .models import CommunicationLog, CommunicationTemplate, SmsCampaign
from .services import SmsCampaignService


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(BaseModelAdmin):
    """مدیریت متن پیام‌های سیستم."""

    form = CommunicationTemplateAdminForm
    save_on_top = False

    list_display = (
        "title",
        "template_type",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "template_type",
        "is_active",
    )

    search_fields = (
        "title",
        "body",
    )

    readonly_fields = (
        "version",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "متن پیام",
            {
                "fields": (
                    "title",
                    "template_type",
                    "body",
                    "is_active",
                ),
            },
        ),
        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "version",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )


@admin.register(SmsCampaign)
class SmsCampaignAdmin(BaseModelAdmin):
    """ارسال دستی پیامک؛ از یک مشتری تا همه مشتریان."""

    form = SmsCampaignAdminForm
    save_on_top = False

    list_display = (
        "title",
        "target_display",
        "status",
        "scheduled_at",
    )

    list_filter = (
        "target_type",
        "status",
    )

    search_fields = (
        "title",
        "body",
        "customer__full_name",
        "customer__mobile",
    )

    autocomplete_fields = (
        "customer",
    )

    filter_horizontal = (
        "selected_customers",
    )

    readonly_fields = (
        "status",
        "total_recipients",
        "sent_count",
        "failed_count",
        "created_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "پیامک",
            {
                "fields": (
                    "title",
                    "body",
                ),
            },
        ),
        (
            "گیرندگان",
            {
                "description": "برای ارسال همگانی، «همه مشتریان» را انتخاب کن.",
                "fields": (
                    "target_type",
                    "customer",
                    "selected_customers",
                ),
            },
        ),
        (
            "زمان ارسال",
            {
                "fields": (
                    "scheduled_at",
                ),
            },
        ),
        (
            "نتیجه ارسال",
            {
                "fields": (
                    "status",
                    "total_recipients",
                    "sent_count",
                    "failed_count",
                    "created_by",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    actions = (
        "send_selected_sms",
        "cancel_drafts",
    )

    @admin.display(description="گیرندگان")
    def target_display(self, obj):
        return obj.get_target_type_display()

    @admin.action(description="ارسال پیامک‌های انتخاب‌شده")
    def send_selected_sms(self, request, queryset):
        service = SmsCampaignService()

        scheduled = 0
        success = 0
        failed = 0

        for campaign in queryset:
            try:
                result = service.send_campaign(campaign)

                if result["scheduled"]:
                    scheduled += 1
                else:
                    success += result["success_count"]
                    failed += result["failed_count"]

            except Exception as exc:
                failed += 1

                self.message_user(
                    request,
                    f"خطا در «{campaign.title}»: {exc}",
                    level=messages.ERROR,
                )

        if scheduled:
            self.message_user(
                request,
                f"{scheduled} ارسال برای زمان تعیین‌شده در صف قرار گرفت.",
                level=messages.SUCCESS,
            )

        self.message_user(
            request,
            f"نتیجه ارسال: موفق={success} | ناموفق={failed}",
            level=messages.SUCCESS if failed == 0 else messages.WARNING,
        )

    @admin.action(description="لغو پیش‌نویس‌های انتخاب‌شده")
    def cancel_drafts(self, request, queryset):
        changed = queryset.filter(
            status__in=[
                SmsCampaign.STATUS_DRAFT,
                SmsCampaign.STATUS_READY,
            ]
        ).update(
            status=SmsCampaign.STATUS_CANCELLED,
            updated_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{changed} ارسال لغو شد.",
            level=messages.SUCCESS,
        )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)


@admin.register(CommunicationLog)
class CommunicationLogAdmin(BaseModelAdmin):
    """گزارش ارسال؛ کاملاً فقط برای مشاهده."""

    list_display = (
        "id",
        "recipient",
        "status",
        "provider",
        "attempted_at",
        "sent_at",
    )

    list_filter = (
        "status",
        "provider",
    )

    search_fields = (
        "recipient",
        "provider_message_id",
        "customer__full_name",
        "customer__mobile",
        "message",
    )

    readonly_fields = (
        "queue",
        "customer",
        "vehicle",
        "template",
        "recipient",
        "message",
        "provider",
        "provider_message_id",
        "provider_status",
        "status",
        "error_message",
        "cost",
        "attempted_at",
        "sent_at",
        "delivered_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False