from django.core.exceptions import ValidationError
from django.db import models


class MaintenanceReminderType(models.Model):
    """نوع یادآوری قابل مدیریت از پنل ادمین."""

    title = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="عنوان نوع یادآوری",
    )

    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        verbose_name = "نوع یادآوری"
        verbose_name_plural = "انواع یادآوری"
        ordering = ["order", "title"]
        indexes = [
            models.Index(fields=["is_active", "order"]),
        ]

    def __str__(self):
        return self.title


class MaintenanceRule(models.Model):
    """قواعد زمان‌بندی نگهداری خودرو؛ تشخیص فقط بر اساس کلیدواژه است."""

    title = models.CharField(
        max_length=150,
        verbose_name="عنوان قاعده",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    reminder_type = models.ForeignKey(
        MaintenanceReminderType,
        on_delete=models.PROTECT,
        related_name="maintenance_rules",
        verbose_name="نوع یادآوری",
    )

    keywords = models.JSONField(
        default=list,
        blank=True,
        verbose_name="کلیدواژه‌ها",
        help_text="کلیدواژه‌ها با ویرگول جدا شوند. مقدار * یعنی هر مراجعه/رویداد.",
    )

    interval_months = models.PositiveSmallIntegerField(
        default=12,
        verbose_name="فاصله زمانی (ماه)",
    )

    lead_days = models.PositiveSmallIntegerField(
        default=14,
        verbose_name="یادآوری چند روز قبل",
    )

    grace_days = models.PositiveSmallIntegerField(
        default=45,
        verbose_name="مهلت ارسال بعد از موعد",
    )

    send_window_start = models.TimeField(
        default="09:00",
        verbose_name="شروع بازه ارسال",
    )

    send_window_end = models.TimeField(
        default="12:00",
        verbose_name="پایان بازه ارسال",
    )

    template = models.ForeignKey(
        "communications.CommunicationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_rules",
        verbose_name="قالب پیامک",
    )

    automatic = models.BooleanField(
        default=True,
        verbose_name="ارسال خودکار",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        verbose_name = "قاعده سرویس هوشمند"
        verbose_name_plural = "قواعد سرویس هوشمند"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["is_active", "automatic"]),
        ]

    def clean(self):
        super().clean()

        if self.interval_months <= 0:
            raise ValidationError(
                {"interval_months": "فاصله زمانی باید بیشتر از صفر باشد."}
            )

        if not self.keywords:
            raise ValidationError(
                {"keywords": "حداقل یک کلیدواژه وارد کنید. برای تطبیق همه رویدادها از * استفاده کنید."}
            )

        if not self.reminder_type_id:
            raise ValidationError(
                {"reminder_type": "نوع یادآوری را انتخاب کنید."}
            )

        if self.send_window_start >= self.send_window_end:
            raise ValidationError(
                "پایان بازه ارسال باید بعد از شروع بازه باشد."
            )

    def __str__(self):
        return self.title
