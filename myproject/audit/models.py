from django.db import models
from inventory.models import Supplier
from django.core.exceptions import ValidationError
from django.utils import timezone

class AuditLog(models.Model):

    SERVICE_CHOICES = [

        ('diagnostic', 'عیب‌یابی '),
        ('periodic_service', 'سرویس دوره‌ای'),
        ('engine_tuning', 'تنظیم موتور'),
        ('engine_repair', 'تعمیر اساسی موتور'),
        ('gearbox_repair', 'تعمیر گیربکس'),
        ('clutch', 'تعویض کیت کلاچ'),
        ('other', 'سایر موارد'),

    ]

    # SOURCE_CHOICES = [

    #     ('inventory', 'انبار'),
    #     ('external', 'لوازم یدکی'),
    #     ('customer', 'مشتری'),

    # ]

    # SHOPPING_CHOICES = [
    #     ('kianush','کیانوش'),        
    #     ('moein','معین'),        
    #     ('siavash','سیاوش'),        
    #     ('akhavan','اخوان'),        
    #     ('japonyadak','ژاپن یدک'),        
    #     ('binici','بی‌نی‌سی'),        
    #     ('madu','مادو'),        
    #     ('ataie','عطایی'),        
    #     ('tanha','تنها'),        
    # ]


    mechanic = models.ForeignKey(
        'users.EmployeeProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تکنسین مسئول'
    )

    service_request = models.ForeignKey(
        'crm.CustomerServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='خدمات درخواستی'
    )
    customer_name = models.CharField(
        max_length=100,
        verbose_name='نام مشتری'

    )

    customer_phone = models.CharField(
        blank=True,
        max_length=11,
        verbose_name='شماره تماس'

    )

    vehicle = models.CharField(

        max_length=150,
        verbose_name='ماشین'

    )

    # plate_number = models.CharField(

    #     max_length=30,
    #     verbose_name='شماره پلاک'

    # )

    service_type = models.CharField(

        max_length=50,
        choices=SERVICE_CHOICES,
        verbose_name='نوع خدمات انجام شده'

    )

    work_description = models.TextField(

        verbose_name='شرح عملیات'

    )

    # parts_source = models.CharField(

    #     max_length=20,
    #     choices=SOURCE_CHOICES,
    #     default='inventory',
    #     verbose_name='تهیه لوازم'

    # )

    # supplier_name = models.CharField(
    #     max_length=100,
    #     verbose_name='لوازم یدکی'

    # )

    work_start = models.DateTimeField(

        verbose_name='شروع کار'

    )

    work_end = models.DateTimeField(

        verbose_name='پایان کار'

    )

    manager_note = models.TextField(

        blank=True,
        verbose_name='یادداشت مدیریتی'

    )

    created_at = models.DateTimeField(

        auto_now_add=True,
        verbose_name='زمان ثبت گزارش'

    )

    updated_at = models.DateTimeField(

        auto_now=True,
        verbose_name='آخرین ویرایش'

    )

    service_date = models.DateField(
        default=timezone.localdate,
        verbose_name="تاریخ خدمت",
    )


    class Meta:

        verbose_name = 'گزارش فعالیت تعمیرکار'
        verbose_name_plural = 'گزارش فعالیت تعمیرکاران'
        ordering = ['-created_at']

    def __str__(self):

        return f'{self.vehicle} - {self.customer_name}'

from django.db import models, transaction
from django.core.exceptions import ValidationError


class BaseUsedPart(models.Model):

    audit = models.ForeignKey(
        "AuditLog",
        on_delete=models.CASCADE,
        verbose_name="گزارش تعمیر",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="تعداد",
    )

    unit_price = models.PositiveIntegerField(
        default=0,
        verbose_name="قیمت واحد",
    )

    total_price = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="جمع قیمت",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="توضیحات",
    )

    class Meta:

        abstract = True

    def save(
        self,
        *args,
        **kwargs,
    ):

        self.total_price = (
            self.quantity *
            self.unit_price
        )

        super().save(
            *args,
            **kwargs,
        )


class InventoryUsedPart(
    BaseUsedPart,
):

    audit = models.ForeignKey(
        "AuditLog",
        on_delete=models.CASCADE,
        related_name="inventory_parts",
        verbose_name="گزارش تعمیر",
    )

    part = models.ForeignKey(
        "inventory.Part",
        on_delete=models.PROTECT,
        related_name="inventory_used_parts",
        verbose_name="نام قطعه",
    )

    class Meta:

        verbose_name = "قطعه مصرفی انبار"

        verbose_name_plural = "قطعات مصرفی انبار"

    def clean(self):

        if self.quantity <= 0:

            raise ValidationError(
                {
                    "quantity":
                    "تعداد باید بیشتر از صفر باشد."
                }
            )

    def save(
        self,
        *args,
        **kwargs,
    ):

        self.full_clean()

        from inventory.models import Part

        with transaction.atomic():

            current_part = (
                Part.objects
                .select_for_update()
                .get(
                    pk=self.part_id
                )
            )

            # ==========================================
            # قیمت فروش فعلی قطعه
            # ==========================================

            self.unit_price = int(
                current_part.sale_price or 0
            )

            # ==========================================
            # ثبت جدید
            # ==========================================

            if not self.pk:

                if (
                    self.quantity >
                    current_part.stock
                ):

                    raise ValidationError(
                        {
                            "quantity":
                            "موجودی قطعه کافی نیست."
                        }
                    )

                current_part.stock -= (
                    self.quantity
                )

                current_part.save(
                    update_fields=[
                        "stock",
                    ]
                )

            # ==========================================
            # ویرایش رکورد قبلی
            # ==========================================

            else:

                old = (
                    InventoryUsedPart.objects
                    .select_for_update()
                    .select_related("part")
                    .get(
                        pk=self.pk
                    )
                )

                # --------------------------------------
                # همان قطعه
                # --------------------------------------

                if old.part_id == self.part_id:

                    difference = (
                        self.quantity -
                        old.quantity
                    )

                    if (
                        difference > 0
                        and
                        difference >
                        current_part.stock
                    ):

                        raise ValidationError(
                            {
                                "quantity":
                                "موجودی قطعه کافی نیست."
                            }
                        )

                    current_part.stock -= (
                        difference
                    )

                    current_part.save(
                        update_fields=[
                            "stock",
                        ]
                    )

                # --------------------------------------
                # قطعه عوض شده
                # --------------------------------------

                else:

                    old_part = (
                        Part.objects
                        .select_for_update()
                        .get(
                            pk=old.part_id
                        )
                    )

                    # برگشت موجودی قطعه قبلی
                    old_part.stock += (
                        old.quantity
                    )

                    old_part.save(
                        update_fields=[
                            "stock",
                        ]
                    )

                    # بررسی موجودی قطعه جدید
                    if (
                        self.quantity >
                        current_part.stock
                    ):

                        raise ValidationError(
                            {
                                "quantity":
                                "موجودی قطعه جدید کافی نیست."
                            }
                        )

                    # کم کردن موجودی قطعه جدید
                    current_part.stock -= (
                        self.quantity
                    )

                    current_part.save(
                        update_fields=[
                            "stock",
                        ]
                    )

            # ==========================================
            # قیمت کل
            # ==========================================

            self.total_price = (
                self.quantity *
                self.unit_price
            )

            super().save(
                *args,
                **kwargs,
            )

    def delete(
        self,
        *args,
        **kwargs,
    ):

        from inventory.models import Part

        with transaction.atomic():

            current_part = (
                Part.objects
                .select_for_update()
                .get(
                    pk=self.part_id
                )
            )

            current_part.stock += (
                self.quantity
            )

            current_part.save(
                update_fields=[
                    "stock",
                ]
            )

            super().delete(
                *args,
                **kwargs,
            )


class PurchasedPart(
    BaseUsedPart,
):

    audit = models.ForeignKey(
        "AuditLog",
        on_delete=models.CASCADE,
        related_name="purchased_parts",
        verbose_name="گزارش تعمیر",
    )

    part_name = models.CharField(
        max_length=200,
        verbose_name="نام قطعه",
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchased_parts",
        verbose_name="فروشنده",
    )

    class Meta:

        verbose_name = "قطعه خریداری شده"

        verbose_name_plural = "قطعات خریداری شده"

    def __str__(self):

        return self.part_name


class CustomerPart(
    BaseUsedPart,
):

    audit = models.ForeignKey(
        "AuditLog",
        on_delete=models.CASCADE,
        related_name="customer_parts",
        verbose_name="گزارش تعمیر",
    )

    part_name = models.CharField(
        max_length=200,
        verbose_name="نام قطعه",
    )

    class Meta:

        verbose_name = "قطعه مشتری"

        verbose_name_plural = "قطعات مشتری"

    def __str__(self):

        return self.part_name