from django.db import models
from django.conf import settings

class CommunicationTemplate(models.Model):

    CHANNEL_CHOICES = [
        ("sms", "پیامک"),
        ("email", "ایمیل"),
        ("notification", "اعلان داخلی"),
        ("whatsapp", "واتساپ"),
    ]

    TEMPLATE_TYPE_CHOICES = [
        ("vehicle_entry", "ورود خودرو"),
        ("vehicle_delivery", "تحویل خودرو"),
        ("thank_you", "تشکر از مشتری"),
        ("service_reminder", "یادآوری سرویس"),
        ("maintenance_due", "یادآوری سرویس دوره‌ای"),
        ("invoice_created", "صدور فاکتور"),
        ("invoice_paid", "تسویه فاکتور"),
        ("birthday", "تبریک تولد"),
        ("custom", "سفارشی"),
    ]

    title = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="عنوان قالب",
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="شناسه سیستمی",
    )

    template_type = models.CharField(
        max_length=30,
        choices=TEMPLATE_TYPE_CHOICES,
        verbose_name="نوع قالب",
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default="sms",
        verbose_name="کانال ارسال",
    )

    subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="عنوان پیام",
    )

    body = models.TextField(
        verbose_name="متن پیام",
        help_text=(
            "متغیرهای نمونه: "
            "{{ customer_name }}، "
            "{{ vehicle }}، "
            "{{ plate_number }}، "
            "{{ invoice_number }}"
        ),
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
    )

    version = models.PositiveIntegerField(
        default=1,
        verbose_name="نسخه قالب",
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
        verbose_name = "قالب پیام"
        verbose_name_plural = "قالب‌های پیام"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["template_type"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.title


class Reminder(models.Model):

    STATUS_PENDING = "pending"
    STATUS_SCHEDULED = "scheduled"
    STATUS_SENT = "sent"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("scheduled", "زمان‌بندی شده"),
        ("sent", "ارسال شده"),
        ("cancelled", "لغو شده"),
        ("expired", "منقضی شده"),
    ]

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="communication_reminders",
        verbose_name="مشتری",
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.CASCADE,
        related_name="communication_reminders",
        verbose_name="خودرو",
    )

    audit = models.ForeignKey(
        "audit.AuditLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communication_reminders",
        verbose_name="گزارش تعمیر مرتبط",
    )

    reminder_type = models.CharField(
        max_length=120,
        verbose_name="نوع یادآوری",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    due_date = models.DateField(
        verbose_name="تاریخ یادآوری",
    )

    last_event_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ مبنای محاسبه",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت",
    )

    auto_generated = models.BooleanField(
        default=True,
        verbose_name="تولید خودکار",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ارسال",
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
        verbose_name = "یادآوری سرویس"
        verbose_name_plural = "یادآوری‌های سرویس"
        ordering = ["due_date"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["vehicle"]),
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["reminder_type"]),
        ]

    def __str__(self):
        return f"{self.customer} - {self.title}"


class CommunicationQueue(models.Model):

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار"),
        (STATUS_PROCESSING, "در حال پردازش"),
        (STATUS_SENT, "ارسال شده"),
        (STATUS_FAILED, "ناموفق"),
        (STATUS_CANCELLED, "لغو شده"),
    ]

    CHANNEL_CHOICES = [
        ("sms", "پیامک"),
        ("email", "ایمیل"),
        ("notification", "اعلان داخلی"),
        ("whatsapp", "واتساپ"),
    ]

    recipient_name = models.CharField(
        max_length=150,
        verbose_name="نام گیرنده",
    )

    recipient_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره موبایل",
    )

    recipient_email = models.EmailField(
        blank=True,
        verbose_name="ایمیل",
    )

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communication_queue_items",
        verbose_name="مشتری",
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communication_queue_items",
        verbose_name="خودرو",
    )

    template = models.ForeignKey(
        "communications.CommunicationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queue_items",
        verbose_name="قالب پیام",
    )

    reminder = models.ForeignKey(
        "communications.Reminder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queue_items",
        verbose_name="یادآوری مرتبط",
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default="sms",
        verbose_name="روش ارسال",
    )

    subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="عنوان پیام",
    )

    body = models.TextField(
        verbose_name="متن پیام",
    )

    scheduled_at = models.DateTimeField(
        verbose_name="زمان برنامه‌ریزی ارسال",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="وضعیت",
    )

    priority = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="اولویت",
    )

    retry_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد تلاش",
    )

    max_retry = models.PositiveSmallIntegerField(
        default=3,
        verbose_name="حداکثر تلاش",
    )

    last_error = models.TextField(
        blank=True,
        verbose_name="آخرین خطا",
    )

    provider = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="سامانه ارسال",
    )

    provider_message_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="شناسه پیام سامانه",
    )

    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخرین تلاش",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ارسال موفق",
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
        verbose_name = "صف ارسال پیام"
        verbose_name_plural = "صف ارسال پیام‌ها"
        ordering = ["priority", "scheduled_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["priority", "scheduled_at"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["provider"]),
        ]

    def __str__(self):
        return f"{self.recipient_name} - {self.get_status_display()}"


class CommunicationLog(models.Model):

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "موفق"),
        (STATUS_FAILED, "ناموفق"),
        (STATUS_CANCELLED, "لغو شده"),
    ]

    queue = models.ForeignKey(
        "communications.CommunicationQueue",
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="پیام صف",
    )

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communication_logs",
        verbose_name="مشتری",
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communication_logs",
        verbose_name="خودرو",
    )

    template = models.ForeignKey(
        "communications.CommunicationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name="قالب پیام",
    )

    channel = models.CharField(
        max_length=20,
        verbose_name="کانال ارسال",
    )

    recipient = models.CharField(
        max_length=200,
        verbose_name="گیرنده",
    )

    message = models.TextField(
        verbose_name="متن ارسال شده",
    )

    provider = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="سامانه ارسال",
    )

    provider_message_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="شناسه پیام سامانه",
    )

    provider_status = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="وضعیت برگشتی سامانه",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="وضعیت نهایی",
    )

    error_message = models.TextField(
        blank=True,
        verbose_name="شرح خطا",
    )

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="هزینه ارسال",
    )

    attempted_at = models.DateTimeField(
        verbose_name="زمان تلاش",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ارسال موفق",
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان تحویل",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت",
    )

    class Meta:
        verbose_name = "گزارش تلاش ارسال"
        verbose_name_plural = "گزارش تلاش‌های ارسال"
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["channel"]),
            models.Index(fields=["attempted_at"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["customer"]),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.get_status_display()}"


class SmsCampaign(models.Model):

    TARGET_ALL = "all"
    TARGET_GROUP = "group"
    TARGET_SINGLE = "single"

    TARGET_CHOICES = [
        (TARGET_ALL, "همه مشتریان"),
        (TARGET_GROUP, "مشتریان انتخابی"),
        (TARGET_SINGLE, "یک مشتری"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_READY = "ready"
    STATUS_SENDING = "sending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "پیش‌نویس"),
        (STATUS_READY, "آماده ارسال"),
        (STATUS_SENDING, "در حال ارسال"),
        (STATUS_COMPLETED, "تکمیل شده"),
        (STATUS_FAILED, "دارای خطا"),
        (STATUS_CANCELLED, "لغو شده"),
    ]

    title = models.CharField(
        max_length=150,
        verbose_name="عنوان پیام",
    )

    body = models.TextField(
        verbose_name="متن پیام",
    )

    target_type = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default=TARGET_SINGLE,
        verbose_name="گیرندگان",
    )

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_campaigns",
        verbose_name="مشتری",
    )

    selected_customers = models.ManyToManyField(
        "crm.Customer",
        blank=True,
        related_name="selected_sms_campaigns",
        verbose_name="مشتریان انتخابی",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name="وضعیت",
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ارسال",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_sms_campaigns",
        verbose_name="ایجادکننده",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    total_recipients = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد گیرندگان",
    )

    sent_count = models.PositiveIntegerField(
        default=0,
        verbose_name="ارسال موفق",
    )

    failed_count = models.PositiveIntegerField(
        default=0,
        verbose_name="ارسال ناموفق",
    )

    class Meta:
        verbose_name = "ارسال پیامک"
        verbose_name_plural = "ارسال پیامک"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["target_type"]),
        ]

    def __str__(self):
        return self.title


class SmsCampaignRecipient(models.Model):

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار"),
        (STATUS_SENT, "ارسال شده"),
        (STATUS_FAILED, "ناموفق"),
        (STATUS_CANCELLED, "لغو شده"),
    ]

    campaign = models.ForeignKey(
        SmsCampaign,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="کمپین",
    )

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="sms_campaign_recipients",
        verbose_name="مشتری",
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="شماره موبایل",
    )

    queue = models.OneToOneField(
        CommunicationQueue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_recipient",
        verbose_name="پیام صف",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="وضعیت",
    )

    error_message = models.TextField(
        blank=True,
        verbose_name="شرح خطا",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان ارسال",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )

    class Meta:
        verbose_name = "گیرنده پیامک"
        verbose_name_plural = "گیرندگان پیامک"
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "customer"],
                name="unique_sms_campaign_customer",
            )
        ]
        indexes = [
            models.Index(fields=["campaign", "status"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self):
        return f"{self.campaign} - {self.customer}"


class SmartSmsRecommendation(models.Model):

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_SCHEDULED = "scheduled"
    STATUS_SENT = "sent"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_PENDING, "در انتظار بررسی"),
        (STATUS_ACCEPTED, "تأیید شده"),
        (STATUS_REJECTED, "رد شده"),
        (STATUS_SCHEDULED, "زمان‌بندی شده"),
        (STATUS_SENT, "ارسال شده"),
        (STATUS_EXPIRED, "منقضی شده"),
    ]

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="smart_sms_recommendations",
        verbose_name="مشتری",
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="smart_sms_recommendations",
        verbose_name="خودرو",
    )

    template = models.ForeignKey(
        CommunicationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="smart_recommendations",
        verbose_name="قالب پیامک",
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="امتیاز مدل",
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="دلیل پیشنهاد",
    )

    suggested_at = models.DateTimeField(
        verbose_name="زمان پیشنهادی",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="وضعیت",
    )

    feature_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Snapshot ویژگی‌ها",
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
        verbose_name = "پیشنهاد پیامک هوشمند"
        verbose_name_plural = "پیشنهادهای پیامک هوشمند"
        ordering = ["suggested_at"]
        indexes = [
            models.Index(fields=["status", "suggested_at"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["score"]),
        ]

    def __str__(self):
        return f"{self.customer} - {self.reason or 'پیشنهاد هوشمند'}"
