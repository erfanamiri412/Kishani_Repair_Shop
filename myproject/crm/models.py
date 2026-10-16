from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from crm.permissions import PermissionSeeder
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from .validators import iran_plate_validator, phone_validator
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from core.models import TimeStampedModel
from crm.choices import ServiceType

class Priority(models.TextChoices):
    """
    سطح اولویت
    """

    LOW = "low", "کم"

    NORMAL = "normal", "عادی"

    HIGH = "high", "زیاد"

    URGENT = "urgent", "فوری"

class Command(BaseCommand):

    help = "Synchronize CRM permissions."

    def handle(

        self,

        *args,

        **kwargs,

    ):

        PermissionSeeder.sync()

        self.stdout.write(

            self.style.SUCCESS(

                "Permissions synchronized."

            )

        )
        
class CRMBaseModel(models.Model):
    """
    کلاس پایه برای تمام مدل‌های CRM
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        abstract = True

class Customer(models.Model):
    """
    مرجع اصلی اطلاعات مشتری در کل سیستم
    """

    GENDER_CHOICES = [

        ("male", "آقا"),
        ("female", "خانم")

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

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default="male",
        verbose_name="جنسیت مشتری"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )


    class Meta:

        verbose_name = "مشتری"

        verbose_name_plural = "مشتری"

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

class CustomerAudit(CRMBaseModel):
    """
    ثبت تمام رویدادهای مهم مربوط به مشتری
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        verbose_name="مشتری"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_audits",
        verbose_name="انجام دهنده"
    )

    action = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="نوع عملیات"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان عملیات"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    old_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name="مقدار قبلی"
    )

    new_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name="مقدار جدید"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="آدرس IP"
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )

    source = models.CharField(
        max_length=50,
        default="system",
        verbose_name="منبع عملیات"
    )

    is_system = models.BooleanField(
        default=False,
        verbose_name="عملیات سیستمی"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="زمان ثبت"
    )

    class Meta:

        verbose_name = "لاگ تغییرات مشتری"

        verbose_name_plural = "لاگ تغییرات مشتری"

        ordering = [

            "-created_at",

        ]

        indexes = [

            models.Index(

                fields=[

                    "customer",

                    "created_at",

                ]

            ),

            models.Index(

                fields=[

                    "action",

                    "created_at",

                ]

            ),

        ]

    def __str__(self):

        return (

            f"{self.customer}"

            f" - "

            f"{self.action}"

        )

class CustomerVehicle(models.Model):
    """
    خودروهای متعلق به مشتری
    هر مشتری می‌تواند چند خودرو داشته باشد.
    """
    TRANSMISSION_CHOICES = [

        ("manual", "دنده‌ای"),
        ("automatic", "اتوماتیک")

    ]
  
    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="مالک خودرو"
    )

    plate_number = models.CharField(
        max_length=20,
        db_index=True,
        validators=[iran_plate_validator],
        verbose_name=" شماره پلاک"
    )
    
    def clean(self):
        super().clean()

        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"

        table = str.maketrans(
            persian_digits,
            english_digits
        )

        self.plate_number = (
            str(self.plate_number)
            .translate(table)
            .replace(" ", "")
            .replace("-", "")
            .strip()
        )

    brand = models.CharField(
        max_length=100,
        verbose_name="مدل خودرو"
    )

    company = models.CharField(
        max_length=100,
        verbose_name="شرکت سازنده"
    )

    model = models.CharField(
        max_length=100,
        verbose_name="سال ساخت"
    )

    transmission = models.CharField(
        max_length=50,
        choices = TRANSMISSION_CHOICES,
        default='manual',
        verbose_name='گیربکس'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    @property
    def formatted_plate(self):

        import re

        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"

        translation = str.maketrans(
            persian_digits,
            english_digits,
        )

        plate = (
            str(self.plate_number or "")
            .translate(translation)
            .strip()
        )

        # حذف جداکننده‌های احتمالی
        plate = re.sub(
            r"[\s\-/|]+",
            "",
            plate,
        )

        match = re.fullmatch(
            r"(\d{2})([آ-ی])(\d{3})(\d{2})",
            plate,
        )

        if not match:
            return str(
                self.plate_number or ""
            ).strip()

        return (
            f"{match.group(1)}-"
            f"{match.group(2)}-"
            f"{match.group(3)}-"
            f"{match.group(4)}ایران"
        )


    def __str__(self):

        return (
            f"{self.brand} {self.model} | "
            f"{self.formatted_plate}"
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
        name = " ".join(
            str(value).strip()
            for value in (self.brand, self.model)
            if value
        )

        raw_plate = str(self.formatted_plate or "")
        raw_plate = raw_plate.replace("ایران", "").strip()

        parts = [part.strip() for part in raw_plate.split("-")]

        if len(parts) == 4 and all(parts):
            city, letter, middle, right = parts
            plate = f"ایران {right} / {middle} / {letter} / {city}"
        else:
            plate = self.formatted_plate or "-"

        return f"{name} ({plate})" if name else plate

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

    class Meta:

        verbose_name = "درخواست خدمات"

        verbose_name_plural = "درخواست‌های خدمات"

        ordering = ("-created_at",)

        indexes = [

            models.Index(
                fields=("customer",),
            ),

            models.Index(
                fields=("service_type",),
            ),

        ]

    def clean(self):

        super().clean()

        if self.vehicle_id and self.customer_id:

            if self.vehicle.customer_id != self.customer_id:

                from django.core.exceptions import ValidationError

                raise ValidationError({
                    "vehicle": (
                        "خودروی انتخاب‌شده متعلق به این مشتری نیست."
                    )
                })

    def __str__(self):

        if self.vehicle_id:

            return (
                f"{self.customer.full_name} - "
                f"{self.vehicle.brand} "
                f"{self.vehicle.model} - "
                f"{self.get_service_type_display()}"
            )

        return (
            f"{self.customer.full_name} - "
            f"{self.get_service_type_display()}"
        )
    
class Repair(
    TimeStampedModel,
):

    class Media:
        js = (
            "assets/js/audit_inline.js",
            "assets/js/admin_number_formatter.js",
            "assets/js/admin_time_picker.js",
            "assets/js/audit_inventory_parts.js",
            "assets/js/admin_dependent_fields.js",
        )

        css = {
            "all": (
                "assets/css/admin_time_picker.css",
            ),
        }

    repair_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="شماره پذیرش",
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="repairs",
        verbose_name="مشتری",
    )

    vehicle = models.ForeignKey(
        "crm.CustomerVehicle",
        on_delete=models.PROTECT,
        related_name="repairs",
        verbose_name="خودرو",
        null=True,
        blank=True,
    )

    service_request = models.OneToOneField(
        "crm.CustomerServiceRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair",
        verbose_name="درخواست خدمات",
    )

    mechanic = models.ForeignKey(
        "users.EmployeeProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="repairs",
        verbose_name="مکانیک",
    )



    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تحویل خودرو",
    )

    class Meta:
        verbose_name = "تعمیر"
        verbose_name_plural = "تعمیرات"
        ordering = (
            "-created_at",
        )

    def save(
        self,
        *args,
        **kwargs,
    ):

        if not self.repair_number:
            self.repair_number = (
                f"R-{uuid.uuid4().hex[:8].upper()}"
            )

        super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return self.repair_number

    @property
    def parts_total(self):
        return sum(
            (
                part.total_price
                for part in self.parts.all()
            ),
            Decimal("0"),
        )

    @property
    def services_total(self):
        return sum(
            (
                service.total_price
                for service in self.services.all()
            ),
            Decimal("0"),
        )

    @property
    def total_amount(self):
        return (
            self.parts_total
            + self.services_total
        )

class RepairPart(
    TimeStampedModel,
):

    repair = models.ForeignKey(
        Repair,
        on_delete=models.CASCADE,
        related_name="parts",
        verbose_name="تعمیر",
    )

    part_name = models.CharField(
        max_length=200,
        verbose_name="نام قطعه",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد",
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="قیمت واحد",
    )

    class Meta:
        verbose_name = "قطعه مصرفی"
        verbose_name_plural = "قطعات مصرفی"

    def __str__(self):
        return self.part_name

    @property
    def total_price(self):
        return (
            self.quantity
            * self.unit_price
        )

class RepairServiceItem(
    TimeStampedModel,
):

    repair = models.ForeignKey(
        Repair,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="تعمیر",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="شرح خدمت",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد",
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(
                Decimal("0")
            )
        ],
        verbose_name="دستمزد",
    )

    mechanic = models.ForeignKey(
        "users.EmployeeProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="repair_service_items",
        verbose_name="تعمیرکار",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    class Meta:
        verbose_name = "خدمت انجام‌شده"
        verbose_name_plural = "خدمات انجام‌شده"

    @property
    def total_price(self):
        return (
            self.quantity
            * self.unit_price
        )

    def __str__(self):
        return self.title

class Invoice(
    TimeStampedModel,
):

    repair = models.OneToOneField(
        Repair,
        on_delete=models.CASCADE,
        related_name="invoice",
        verbose_name="تعمیر",
    )

    invoice_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="شماره فاکتور",
    )

    tracking_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="کد پیگیری",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ صدور",
    )

    @property
    def customer(self):
        return self.repair.customer

    @property
    def vehicle(self):
        return self.repair.vehicle

    @property
    def vehicle_name(self):
        if not self.repair or not self.repair.vehicle:
            return "-"

        return self.repair.vehicle.brand or "-"

    @property
    def plate_number(self):
        if not self.repair or not self.repair.vehicle:
            return ""

        return (
            self.repair.vehicle.plate_number
            or ""
        )

    @property
    def repair_number(self):
        return self.repair.repair_number

    @property
    def services_total(self):
        value = sum(
            (
                item.total_price
                for item in self.items.all()
                if item.item_type == "service"
            ),
            Decimal("0"),
        )

        return value or Decimal("0")

    @property
    def parts_total(self):
        value = sum(
            (
                item.total_price
                for item in self.items.all()
                if item.item_type == "part"
            ),
            Decimal("0"),
        )

        return value or Decimal("0")

    @property
    def subtotal(self):
        return (
            self.services_total
            + self.parts_total
        )

    @property
    def total_amount(self):
        return self.subtotal

    @property
    def paid_amount(self):
        return (
            self.payments.aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0")
        )

    @property
    def remaining_amount(self):
        return (
            self.total_amount
            - self.paid_amount
        )

    @property
    def is_paid(self):
        return self.remaining_amount <= 0

    @property
    def payment_status(self):
        if self.paid_amount <= 0:
            return "پرداخت نشده"

        if self.remaining_amount <= 0:
            return "تسویه شده"

        return "بخشی پرداخت شده"

    def save(
        self,
        *args,
        **kwargs,
    ):
        if not self.invoice_number:
            self.invoice_number = (
                f"INV-{uuid.uuid4().hex[:10].upper()}"
            )

        if not self.tracking_code:
            self.tracking_code = (
                f"TRK-{uuid.uuid4().hex[:10].upper()}"
            )

        super().save(
            *args,
            **kwargs,
        )

    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"
        ordering = (
            "-issued_at",
        )

    def __str__(self):
        return self.invoice_number
    
class InvoiceItem(
    TimeStampedModel,
):

    ITEM_TYPE_CHOICES = [
        ("service", "خدمات"),
        ("part", "قطعات"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="فاکتور",
    )

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        verbose_name="نوع",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="شرح",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد",
    )

    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(
                Decimal("0")
            )
        ],
        verbose_name="قیمت واحد",
    )

    mechanic = models.ForeignKey(
        "users.EmployeeProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_items",
        verbose_name="تعمیرکار",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    @property
    def category_name(self):

        mapping = {
            "service": "خدمات",
            "part": "قطعات",
        }

        return mapping.get(
            self.item_type,
            "سایر",
        )

    @property
    def total_price(self):
        return (
            self.quantity
            * self.unit_price
        )

    def __str__(self):
        return self.title

class InvoicePayment(TimeStampedModel):
    PAYMENT_METHOD_CHOICES = [
        ("cash", "نقدی"),
        ("card", "کارتخوان"),
        ("transfer", "واریز بانکی"),
        ("cheque", "چک"),
        ("credit", "نسیه"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="فاکتور",
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="مبلغ پرداختی",
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="cash",
        verbose_name="روش پرداخت",
    )

    paid_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ",
    )

    note = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    def clean(self):
        super().clean()

        if self.amount is None:
            return

        if self.amount < 0:
            raise ValidationError({
                "amount": "مبلغ پرداختی نمی‌تواند منفی باشد."
            })

    def __str__(self):
        return f"پرداخت فاکتور {self.invoice.invoice_number}"