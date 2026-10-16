from django.db import models
from django.contrib.auth.models import User

from crm.validators import phone_validator

class EmployeeProfile(models.Model):

    PAYMENT_PERIOD_CHOICES = [
        ("weekly", "هفتگی"),
        ("monthly", "ماهانه"),
    ]

    ROLE_CHOICES = [
        ("manager", "مدیر"),
        ("mechanic", "مکانیک"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="کاربر",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="mechanic",
        verbose_name="سمت",
    )

    phone = models.CharField(
        max_length=11,
        blank=True,
        validators=[phone_validator],
        verbose_name="شماره تماس",
    )

    fixed_salary = models.PositiveIntegerField(
        default=0,
        verbose_name="پایه حقوق",
    )

    payment_period = models.CharField(
        max_length=20,
        choices=PAYMENT_PERIOD_CHOICES,
        default="monthly",
        verbose_name="بازه پرداخت",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @classmethod
    def sync_profiles(cls):

        for user in User.objects.all():

            cls.objects.get_or_create(
                user=user,
                defaults={
                    "role": "mechanic",
                },
            )

    def __str__(self):

        return (
            f"{self.user.get_full_name()} "
        )

    class Meta:

        verbose_name = "پرسنل"
        verbose_name_plural = "پرسنل"

class SalaryRevision(models.Model):

    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name="salary_revisions",
        verbose_name="پرسنل",
    )

    previous_salary = models.PositiveIntegerField(
        default=0,
        verbose_name="حقوق قبلی",
    )

    new_salary = models.PositiveIntegerField(
        verbose_name="حقوق جدید",
    )

    effective_date = models.DateField(
        verbose_name="تاریخ اجرا",
    )

    reason = models.TextField(
        blank=True,
        verbose_name="علت افزایش حقوق",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "تغییر حقوق"
        verbose_name_plural = "تغییرات حقوق"
        ordering = (
            "-effective_date",
            "-id",
        )

    def __str__(self):

        return (
            f"{self.employee} - "
            f"{self.new_salary:,}"
        )

class SalaryAdvance(models.Model):

    STATUS_CHOICES = [
        ("open", "باز"),
        ("partial", "تسویه ناقص"),
        ("paid", "تسویه شده"),
    ]

    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.PROTECT,
        related_name="salary_advances",
        verbose_name="پرسنل",
    )

    date = models.DateField(
        verbose_name="تاریخ",
    )

    amount = models.PositiveIntegerField(
        verbose_name="مبلغ قرض / علی‌الحساب",
    )

    paid_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="مبلغ تسویه شده",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        verbose_name="وضعیت",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "قرض / علی‌الحساب"
        verbose_name_plural = "قرض و علی‌الحساب پرسنل"

        ordering = (
            "-date",
            "-id",
        )

    @property
    def remaining_amount(self):

        amount = self.amount or 0
        paid_amount = self.paid_amount or 0

        return max(
            amount - paid_amount,
            0,
        )

    def refresh_status(self):

        amount = self.amount or 0
        paid_amount = self.paid_amount or 0

        if paid_amount <= 0:

            self.status = "open"

        elif paid_amount < amount:

            self.status = "partial"

        else:

            self.paid_amount = amount
            self.status = "paid"

        self.save(
            update_fields=[
                "paid_amount",
                "status",
            ]
        )
            
    def __str__(self):

        return (
            f"{self.employee} - "
            f"{self.amount:,}"
        )

class SalaryBonus(models.Model):

    BONUS_TYPE_CHOICES = [
        ("bonus", "پاداش"),
        ("tip", "انعام"),
        ("performance", "پاداش عملکرد"),
        ("other", "سایر"),
    ]

    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name="salary_bonuses",
        verbose_name="پرسنل",
    )

    date = models.DateField(
        verbose_name="تاریخ",
    )

    bonus_type = models.CharField(
        max_length=20,
        choices=BONUS_TYPE_CHOICES,
        default="bonus",
        verbose_name="نوع",
    )

    amount = models.PositiveIntegerField(
        verbose_name="مبلغ",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "پاداش / انعام"
        verbose_name_plural = "پاداش و انعام"
        ordering = (
            "-date",
            "-id",
        )

    def __str__(self):

        return (
            f"{self.employee} - "
            f"{self.amount:,}"
        )

class PayrollSnapshot(models.Model):

    STATUS_CHOICES = [
        ("draft", "پیش‌نویس"),
        ("approved", "تأیید شده"),
        ("paid", "تسویه شده"),
    ]

    PERFORMANCE_LEVEL_CHOICES = [
        ("excellent", "عالی"),
        ("good", "خوب"),
        ("average", "متوسط"),
        ("weak", "ضعیف"),
    ]

    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.PROTECT,
        related_name="payroll_snapshots",
        verbose_name="پرسنل",
    )

    start_date = models.DateField(
        verbose_name="از تاریخ",
    )

    end_date = models.DateField(
        verbose_name="تا تاریخ",
    )

    # ------------------------------------------------------
    # Operational performance
    # ------------------------------------------------------

    repair_count = models.PositiveIntegerField(
        default=0,
        verbose_name="تعداد تعمیرات",
    )

    total_labor_income = models.PositiveIntegerField(
        default=0,
        verbose_name="کل درآمد اجرت",
    )

    average_labor_income = models.PositiveIntegerField(
        default=0,
        verbose_name="میانگین اجرت",
    )

    average_repair_duration = models.PositiveIntegerField(
        default=0,
        verbose_name="میانگین زمان تعمیر",
    )


    # ------------------------------------------------------
    # Performance scores
    # ------------------------------------------------------

    income_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="امتیاز درآمد",
    )

    repair_count_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="امتیاز تعداد تعمیر",
    )

    satisfaction_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="امتیاز رضایت مشتری",
    )

    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="امتیاز کیفیت",
    )

    performance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="امتیاز عملکرد",
    )

    performance_level = models.CharField(
        max_length=20,
        choices=PERFORMANCE_LEVEL_CHOICES,
        default="average",
        verbose_name="سطح عملکرد",
    )

    # ------------------------------------------------------
    # Payroll
    # ------------------------------------------------------

    fixed_salary = models.PositiveIntegerField(
        default=0,
        verbose_name="حقوق ثابت",
    )

    commission_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="پورسانت",
    )

    bonus_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="پاداش و انعام",
    )

    advance_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="کسر قرض / علی‌الحساب",
    )

    payable_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="حقوق قابل پرداخت",
    )

    paid_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="پرداخت شده",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name="وضعیت",
    )

    manager_note = models.TextField(
        blank=True,
        verbose_name="یادداشت مدیر",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        verbose_name = "گزارش حقوق"
        verbose_name_plural = "گزارش حقوق"
        ordering = (
            "-end_date",
            "-id",
        )

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "employee",
                    "start_date",
                    "end_date",
                ),
                name="unique_employee_payroll_period",
            ),
        ]

    @property
    def remaining_amount(self):

        return max(
            self.payable_amount - self.paid_amount,
            0,
        )

    def __str__(self):

        return (
            f"{self.employee} | "
            f"{self.start_date} - "
            f"{self.end_date}"
        )

class SalaryPayment(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("pending", "در انتظار پرداخت"),
        ("partial", "پرداخت ناقص"),
        ("paid", "تسویه شده"),
    ]

    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="پرسنل",
    )

    payroll = models.ForeignKey(
        PayrollSnapshot,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
        verbose_name="دوره حقوق",
    )

    start_date = models.DateField(
        verbose_name="از تاریخ",
    )

    end_date = models.DateField(
        verbose_name="تا تاریخ",
    )

    amount = models.PositiveIntegerField(
        default=0,
        verbose_name="مبلغ پرداختی",
    )

    payment_date = models.DateField(
        verbose_name="تاریخ پرداخت",
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت",
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        verbose_name = "پرداخت حقوق"
        verbose_name_plural = "پرداخت حقوق"
        ordering = (
            "-payment_date",
            "-id",
        )

    def __str__(self):

        return (
            f"{self.employee} - "
            f"{self.amount:,}"
        )
