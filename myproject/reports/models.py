from django.db import models
from django.contrib.auth.models import User


class BackupHistory(models.Model):

    STATUS_CHOICES = [
        ("success", "موفق"),
        ("failed", "ناموفق"),
    ]

    BACKUP_TYPE_CHOICES = [
        ("manual", "دستی"),
        ("automatic", "خودکار"),
    ]

    file_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="نام فایل بکاپ",
    )

    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="مسیر فایل",
    )

    size = models.CharField(
        max_length=50,
        verbose_name="حجم فایل",
    )

    backup_type = models.CharField(
        max_length=20,
        choices=BACKUP_TYPE_CHOICES,
        default="automatic",
        db_index=True,
        verbose_name="نوع بکاپ",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="success",
        db_index=True,
        verbose_name="وضعیت",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان ایجاد",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_backups",
        verbose_name="ایجاد کننده",
    )

    class Meta:

        verbose_name = "تاریخچه پشتیبان‌گیری"

        verbose_name_plural = "تاریخچه پشتیبان‌گیری"

        ordering = [
            "-created_at",
        ]

        indexes = [

            models.Index(
                fields=[
                    "created_at",
                ]
            ),

            models.Index(
                fields=[
                    "status",
                ]
            ),

            models.Index(
                fields=[
                    "backup_type",
                ]
            ),

            models.Index(
                fields=[
                    "created_by",
                ]
            ),

        ]

    def __str__(self):

        return (
            f"{self.file_name} "
            f"({self.get_status_display()})"
        )

    @property
    def has_file(self):

        return bool(
            self.file_path
        )

    @property
    def is_successful(self):

        return self.status == "success"

    @property
    def is_failed(self):

        return self.status == "failed"

    @property
    def is_manual(self):

        return self.backup_type == "manual"

    @property
    def is_automatic(self):

        return self.backup_type == "automatic"

    @property
    def backup_filename(self):

        return self.file_name or ""

    @property
    def backup_extension(self):

        if not self.file_name:
            return ""

        return self.file_name.split(".")[-1].lower()

    @property
    def backup_basename(self):

        if not self.file_name:
            return ""

        return self.file_name.rsplit(".", 1)[0]

    def file_exists(self):

        return bool(
            self.file_path
        )

    def summary(self):

        return {
            "file_name": self.file_name,
            "backup_type": self.get_backup_type_display(),
            "status": self.get_status_display(),
            "size": self.size,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }


class ReportHistory(models.Model):

    REPORT_TYPE_CHOICES = [

        ("financial", "گزارش مالی"),

        ("inventory", "گزارش انبار"),

        ("invoice", "گزارش فاکتورها"),

        ("employee", "گزارش پرسنل"),

        ("monthly", "گزارش ماهانه"),

        ("yearly", "گزارش سالانه"),

        ("management", "گزارش مدیریتی"),

        ("analytics", "تحلیل هوشمند"),

    ]

    REPORT_FORMAT_CHOICES = [

        ("pdf", "PDF"),

        ("excel", "Excel"),

        ("csv", "CSV"),

    ]

    title = models.CharField(

        max_length=200,

        db_index=True,

        verbose_name="عنوان گزارش",

    )

    report_type = models.CharField(

        max_length=30,

        choices=REPORT_TYPE_CHOICES,

        db_index=True,

        verbose_name="نوع گزارش",

    )

    report_format = models.CharField(

        max_length=20,

        choices=REPORT_FORMAT_CHOICES,

        db_index=True,

        verbose_name="فرمت گزارش",

        default="pdf",

    )

    file_name = models.CharField(

        max_length=255,

        blank=True,

        verbose_name="نام فایل",

    )

    file_path = models.CharField(

        max_length=500,

        blank=True,

        verbose_name="مسیر فایل",

    )

    file_size = models.CharField(

        max_length=50,

        blank=True,

        verbose_name="حجم فایل",

    )

    description = models.TextField(

        blank=True,

        verbose_name="توضیحات",

    )

    period_year = models.PositiveSmallIntegerField(

        null=True,

        blank=True,

        db_index=True,

        verbose_name="سال دوره",

    )

    period_month = models.PositiveSmallIntegerField(

        null=True,

        blank=True,

        db_index=True,

        verbose_name="ماه دوره",

    )

    period_start = models.DateField(

        null=True,

        blank=True,

        db_index=True,

        verbose_name="شروع دوره",

    )

    period_end = models.DateField(

        null=True,

        blank=True,

        db_index=True,

        verbose_name="پایان دوره",

    )

    generation_key = models.CharField(

        max_length=80,

        unique=True,

        null=True,

        blank=True,

        db_index=True,

        verbose_name="کلید تولید گزارش",

    )

    snapshot = models.JSONField(

        default=dict,

        blank=True,

        verbose_name="نسخه ثابت داده گزارش",

    )

    chart_data = models.JSONField(

        default=dict,

        blank=True,

        verbose_name="داده نمودارها",

    )

    created_at = models.DateTimeField(

        auto_now_add=True,

        db_index=True,

        verbose_name="تاریخ ایجاد",

    )

    created_by = models.ForeignKey(

        User,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="created_reports",

        verbose_name="ایجاد کننده",

    )

    class Meta:

        verbose_name = "تاریخچه گزارش"

        verbose_name_plural = "تاریخچه گزارش‌ها"

        ordering = [

            "-created_at",

        ]

        indexes = [

            models.Index(

                fields=[

                    "created_at",

                ]

            ),

            models.Index(

                fields=[

                    "report_type",

                ]

            ),

            models.Index(

                fields=[

                    "report_format",

                ]

            ),

            models.Index(

                fields=[

                    "period_year",

                    "period_month",

                ]

            ),

            models.Index(

                fields=[

                    "period_start",

                    "period_end",

                ]

            ),

        ]

    def __str__(self):

        return (

            f"{self.title} "

            f"({self.get_report_format_display()})"

        )

    @property
    def has_file(self):

        return bool(
            self.file_path
        )

    @property
    def file_extension(self):

        if not self.file_name:
            return ""

        return (
            self.file_name
            .split(".")[-1]
            .lower()
        )

    @property
    def file_basename(self):

        if not self.file_name:
            return ""

        return (
            self.file_name
            .rsplit(".", 1)[0]
        )

    @property
    def is_pdf(self):

        return self.report_format == "pdf"

    @property
    def is_excel(self):

        return self.report_format == "excel"

    @property
    def is_csv(self):

        return self.report_format == "csv"

    @property
    def is_financial(self):

        return self.report_type == "financial"

    @property
    def is_inventory(self):

        return self.report_type == "inventory"

    @property
    def is_invoice(self):

        return self.report_type == "invoice"

    @property
    def is_employee(self):

        return self.report_type == "employee"

    @property
    def is_monthly(self):

        return self.report_type == "monthly"

    @property
    def is_yearly(self):

        return self.report_type == "yearly"

    @property
    def is_management(self):

        return self.report_type == "management"

    @property
    def is_analytics(self):

        return self.report_type == "analytics"

    def file_exists(self):

        return bool(
            self.file_path
        )

    def get_download_name(self):

        if self.file_name:
            return self.file_name

        extension = self.file_extension or "pdf"

        return f"{self.title}.{extension}"

    def summary(self):

        return {

            "title": self.title,

            "report_type":
                self.get_report_type_display(),

            "report_format":
                self.get_report_format_display(),

            "file_name": self.file_name,

            "file_size": self.file_size,

            "period_start": self.period_start,

            "period_end": self.period_end,

            "created_at": self.created_at,

            "created_by": self.created_by,

            "has_file": self.has_file,

        }

    def to_dict(self):

        return {

            "title": self.title,

            "type": self.report_type,

            "format": self.report_format,

            "file": self.file_name,

            "size": self.file_size,

            "path": self.file_path,

            "period_year": self.period_year,

            "period_month": self.period_month,

            "period_start": self.period_start,

            "period_end": self.period_end,

            "created_at": self.created_at,

        }
