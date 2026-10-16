from django.db import models
from django.core.validators import RegexValidator
from crm.validators import phone_validator
from crm.choices import ServiceType


from core.models import TimeStampedModel

class Customer(models.Model):
    """
    مرجع اصلی اطلاعات مشتری در کل سیستم
    """

    GENDER_CHOICES = [

        ("male", "آقا"),
        ("female", "خانم"),
        ("company", "شرکت"),

    ]

    STATUS_CHOICES = [

        ("active", "فعال"),
        ("inactive", "غیرفعال"),
        ("blocked", "مسدود شده"),

    ]

    full_name = models.CharField(
        max_length=200,
        verbose_name="نام و نام خانوادگی"
    )

    mobile = models.CharField(
        max_length=11,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$",
                message="شماره موبایل معتبر وارد کنید."
            )
        ],
        verbose_name="شماره موبایل"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        verbose_name="تلفن ثابت"
    )

    national_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="کد ملی"
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default="male",
        verbose_name="نوع مشتری"
    )

    birthday = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ تولد"
    )

    address = models.TextField(
        blank=True,
        verbose_name="آدرس"
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="شهر"
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="کد پستی"
    )

    email = models.EmailField(
        blank=True,
        verbose_name="ایمیل"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="وضعیت مشتری"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:

        verbose_name = "مشتری"

        verbose_name_plural = "مشتریان"

        ordering = [

            "full_name",

        ]

        indexes = [

            models.Index(

                fields=["mobile"],

            ),

            models.Index(

                fields=["full_name"],

            ),

        ]

    def __str__(self):

        return f"{self.full_name} - {self.mobile}"


class CustomerVehicle(models.Model):
    """
    خودروهای متعلق به مشتری
    هر مشتری می‌تواند چند خودرو داشته باشد.
    """

    FUEL_CHOICES = [

        ("gasoline", "بنزینی"),
        ("diesel", "دیزلی"),
        ("hybrid", "هیبرید"),
        ("electric", "برقی"),
        ("cng", "دوگانه سوز"),

    ]

    TRANSMISSION_CHOICES = [

        ("manual", "دنده‌ای"),
        ("automatic", "اتوماتیک"),
        ("cvt", "CVT"),
        ("dct", "دوکلاچه"),

    ]

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="مالک خودرو"
    )

    plate_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="شماره پلاک"
    )

    vin = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="شماره شاسی (VIN)"
    )

    brand = models.CharField(
        max_length=100,
        verbose_name="برند خودرو"
    )

    model = models.CharField(
        max_length=100,
        verbose_name="مدل خودرو"
    )

    production_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="سال ساخت"
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="رنگ"
    )

    engine_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="شماره موتور"
    )

    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_CHOICES,
        default="gasoline",
        verbose_name="نوع سوخت"
    )

    transmission = models.CharField(
        max_length=20,
        choices=TRANSMISSION_CHOICES,
        default="manual",
        verbose_name="نوع گیربکس"
    )

    insurance_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ پایان بیمه"
    )

    technical_inspection_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ پایان معاینه فنی"
    )

    active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:

        verbose_name = "خودرو"

        verbose_name_plural = "خودروهای مشتریان"

        ordering = [

            "-created_at",

        ]

        indexes = [

            models.Index(fields=["plate_number"]),

            models.Index(fields=["brand"]),

            models.Index(fields=["model"]),

        ]

    def __str__(self):

        return f"{self.brand} {self.model} | \u2066{self.formatted_plate}\u2069"


class CustomerVisit(models.Model):
    """
    ثبت هر مراجعه مشتری به تعمیرگاه
    """

    VISIT_TYPE_CHOICES = [

        ("diagnostic", "عیب‌یابی"),
        ("service", "سرویس دوره‌ای"),
        ("repair", "تعمیر"),
        ("inspection", "بازدید"),
        ("warranty", "گارانتی"),
        ("other", "سایر"),

    ]

    STATUS_CHOICES = [

        ("waiting", "در انتظار"),
        ("in_progress", "در حال انجام"),
        ("completed", "تکمیل شده"),
        ("cancelled", "لغو شده"),

    ]

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name="مشتری"
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name="خودرو"
    )

    audit_report = models.OneToOneField(
        "audit.AuditLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_visit",
        verbose_name="گزارش تعمیر"
    )

    invoice = models.OneToOneField(
        "crm.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_visit",
        verbose_name="فاکتور"
    )

    visit_type = models.CharField(
        max_length=30,
        choices=VISIT_TYPE_CHOICES,
        default="repair",
        verbose_name="نوع مراجعه"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="waiting",
        verbose_name="وضعیت"
    )

    arrival_mileage = models.PositiveIntegerField(
        default=0,
        verbose_name="کارکرد هنگام ورود"
    )

    complaint = models.TextField(
        verbose_name="شرح مشکل اعلام شده توسط مشتری"
    )

    diagnosis = models.TextField(
        blank=True,
        verbose_name="نتیجه عیب‌یابی"
    )

    performed_services = models.TextField(
        blank=True,
        verbose_name="خدمات انجام شده"
    )

    recommendation = models.TextField(
        blank=True,
        verbose_name="توصیه برای مراجعات بعدی"
    )

    next_service_km = models.PositiveIntegerField(
        default=0,
        verbose_name="کارکرد سرویس بعدی"
    )

    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ پیشنهادی سرویس بعدی"
    )

    arrived_at = models.DateTimeField(
        verbose_name="زمان ورود خودرو"
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان تحویل خودرو"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:

        verbose_name = "مراجعه مشتری"

        verbose_name_plural = "مراجعات مشتریان"

        ordering = [

            "-arrived_at",

        ]

        indexes = [

            models.Index(fields=["arrived_at"]),

            models.Index(fields=["status"]),

            models.Index(fields=["visit_type"]),

        ]

    def __str__(self):

        return f"{self.customer.full_name} | {self.vehicle.plate_number}"


class CustomerPreference(models.Model):
    """
    تنظیمات و ترجیحات ارتباطی مشتری
    """

    CONTACT_METHOD_CHOICES = [

        ("sms", "پیامک"),
        ("call", "تماس تلفنی"),
        ("whatsapp", "واتساپ"),
        ("none", "عدم دریافت پیام"),

    ]

    CONTACT_TIME_CHOICES = [

        ("morning", "صبح"),
        ("afternoon", "بعدازظهر"),
        ("evening", "عصر"),
        ("anytime", "فرقی ندارد"),

    ]

    customer = models.OneToOneField(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="preferences",
        verbose_name="مشتری"
    )

    preferred_contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default="sms",
        verbose_name="روش ارتباطی ترجیحی"
    )

    preferred_contact_time = models.CharField(
        max_length=20,
        choices=CONTACT_TIME_CHOICES,
        default="anytime",
        verbose_name="زمان مناسب برای ارتباط"
    )

    receive_service_reminders = models.BooleanField(
        default=True,
        verbose_name="دریافت یادآوری سرویس"
    )

    receive_promotional_sms = models.BooleanField(
        default=True,
        verbose_name="دریافت پیامک‌های تبلیغاتی"
    )

    receive_birthday_sms = models.BooleanField(
        default=True,
        verbose_name="دریافت پیام تبریک تولد"
    )

    receive_invoice_sms = models.BooleanField(
        default=True,
        verbose_name="دریافت پیامک صدور فاکتور"
    )

    receive_vehicle_status_sms = models.BooleanField(
        default=True,
        verbose_name="دریافت پیامک وضعیت خودرو"
    )

    receive_survey_sms = models.BooleanField(
        default=True,
        verbose_name="دریافت نظرسنجی پس از تعمیر"
    )

    preferred_language = models.CharField(
        max_length=20,
        default="fa",
        verbose_name="زبان پیام‌ها"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:

        verbose_name = "ترجیحات مشتری"

        verbose_name_plural = "ترجیحات مشتریان"

    def __str__(self):

        return self.customer.full_name


class Tag(models.Model):
    """
    برچسب‌های قابل استفاده در کل سیستم
    """

    COLOR_CHOICES = [

        ("gray", "خاکستری"),
        ("blue", "آبی"),
        ("green", "سبز"),
        ("yellow", "زرد"),
        ("orange", "نارنجی"),
        ("red", "قرمز"),
        ("purple", "بنفش"),

    ]

    title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="عنوان برچسب"
    )

    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="blue",
        verbose_name="رنگ"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:

        verbose_name = "برچسب"

        verbose_name_plural = "برچسب‌ها"

        ordering = [

            "title",

        ]

    def __str__(self):

        return self.title
    

class CustomerTag(models.Model):
    """
    اتصال مشتری به برچسب
    """

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="customer_tags",
        verbose_name="مشتری"
    )

    tag = models.ForeignKey(
        "customer_history.Tag",
        on_delete=models.CASCADE,
        related_name="customers",
        verbose_name="برچسب"
    )

    assigned_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ثبت کننده"
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="یادداشت"
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )

    class Meta:

        verbose_name = "برچسب مشتری"

        verbose_name_plural = "برچسب‌های مشتری"

        constraints = [

            models.UniqueConstraint(
                fields=["customer", "tag"],
                name="unique_customer_tag"
            )

        ]

    def __str__(self):

        return f"{self.customer.full_name} - {self.tag.title}"


class CustomerScore(models.Model):
    """
    امتیاز وفاداری و ارزش مشتری
    این مدل توسط سرویس‌های تحلیلی بروزرسانی می‌شود.
    """

    LEVEL_CHOICES = [

        ("bronze", "برنزی"),
        ("silver", "نقره‌ای"),
        ("gold", "طلایی"),
        ("platinum", "پلاتینیوم"),

    ]

    customer = models.OneToOneField(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="score",
        verbose_name="مشتری"
    )

    score = models.PositiveIntegerField(
        default=0,
        verbose_name="امتیاز مشتری"
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="bronze",
        verbose_name="سطح مشتری"
    )

    loyalty_percent = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="درصد وفاداری"
    )

    predicted_return_days = models.PositiveIntegerField(
        default=0,
        verbose_name="پیش‌بینی مراجعه بعدی (روز)"
    )

    risk_of_churn = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="احتمال ریزش مشتری (%)"
    )

    lifetime_value = models.PositiveBigIntegerField(
        default=0,
        verbose_name="ارزش طول عمر مشتری ( تومان)"
    )

    ai_comment = models.TextField(
        blank=True,
        verbose_name="تحلیل هوش مصنوعی"
    )

    calculated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین محاسبه"
    )

    class Meta:

        verbose_name = "امتیاز مشتری"

        verbose_name_plural = "امتیاز مشتریان"

    def __str__(self):

        return f"{self.customer.full_name} ({self.score})"


class CustomerCommunication(models.Model):
    """
    تاریخچه ارتباطات مشتری با تعمیرگاه
    """

    TYPE_CHOICES = [

        ("sms", "پیامک"),
        ("call", "تماس"),
        ("whatsapp", "واتساپ"),
        ("system", "سیستمی"),
        ("manual", "ثبت دستی"),

    ]

    DIRECTION_CHOICES = [

        ("outgoing", "ارسال شده"),
        ("incoming", "دریافت شده"),

    ]

    STATUS_CHOICES = [

        ("pending", "در انتظار"),
        ("sent", "ارسال شده"),
        ("delivered", "تحویل شده"),
        ("read", "خوانده شده"),
        ("failed", "ناموفق"),
        ("cancelled", "لغو شده"),

    ]

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="communications",
        verbose_name="مشتری"
    )

    communication_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="نوع ارتباط"
    )

    direction = models.CharField(
        max_length=20,
        choices=DIRECTION_CHOICES,
        default="outgoing",
        verbose_name="جهت ارتباط"
    )

    subject = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان"
    )

    message = models.TextField(
        verbose_name="متن پیام"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت"
    )

    related_visit = models.ForeignKey(
        "crm.CustomerVisit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name="مراجعه مرتبط"
    )

    related_invoice = models.ForeignKey(
        "crm.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name="فاکتور مرتبط"
    )

    sent_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ارسال کننده"
    )

    external_reference = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="شناسه خارجی پیام"
    )

    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان تحویل"
    )

    class Meta:

        verbose_name = "ارتباط با مشتری"

        verbose_name_plural = "ارتباطات مشتری"

        ordering = [

            "-sent_at",

        ]

        indexes = [

            models.Index(fields=["status"]),

            models.Index(fields=["communication_type"]),

            models.Index(fields=["sent_at"]),

        ]

    def __str__(self):

        return f"{self.customer.full_name} - {self.communication_type}"


class CustomerNote(models.Model):
    """
    یادداشت‌های داخلی مربوط به مشتری
    """

    NOTE_TYPE_CHOICES = [

        ("general", "عمومی"),
        ("warning", "هشدار"),
        ("financial", "مالی"),
        ("technical", "فنی"),
        ("crm", "ارتباط با مشتری"),

    ]

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="مشتری"
    )

    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPE_CHOICES,
        default="general",
        verbose_name="نوع یادداشت"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان"
    )

    content = models.TextField(
        verbose_name="متن یادداشت"
    )

    important = models.BooleanField(
        default=False,
        verbose_name="یادداشت مهم"
    )

    visible_to_all = models.BooleanField(
        default=True,
        verbose_name="قابل مشاهده برای همه کارکنان"
    )

    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ثبت کننده"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش"
    )

    class Meta:

        verbose_name = "یادداشت مشتری"

        verbose_name_plural = "یادداشت‌های مشتری"

        ordering = [

            "-important",

            "-created_at",

        ]

    def __str__(self):

        return f"{self.customer.full_name} | {self.title}"


class CustomerServiceRequest(TimeStampedModel):

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="service_requests",
        verbose_name="مشتری",
    )

    service_type = models.CharField(
        max_length=50,
        choices=ServiceType.choices,
        verbose_name="نوع خدمت",
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.PROTECT,
        related_name="service_requests",
        verbose_name="خودرو",
        null=True,
        blank=True,
    )

    vehicle_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="سال ساخت",
    )

    problem_description = models.TextField(
        verbose_name="شرح مشکل",
    )

    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="اطلاعات تکمیلی",
    )

    class Meta:

        verbose_name = "درخواست خدمات"

        verbose_name_plural = "درخواست‌های خدمات"

        ordering = ("-created_at",)

        indexes = [

            models.Index(
                fields=("customer"),
            ),

            models.Index(
                fields=("service_type",),
            ),

        ]

    def __str__(self):

        return f"{self.customer} - {self.get_service_type_display()}"