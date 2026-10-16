from django.db import models
from crm.validators import phone_validator

class PartCategory(models.Model):

    title = models.CharField(
        max_length=100,
        verbose_name="نام دسته‌بندی"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    class Meta:

        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.title

class Supplier(models.Model):

    name = models.CharField(
        max_length=150,
        verbose_name="نام فروشنده"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
        verbose_name="شماره تماس"
    )

    address = models.TextField(
        blank=True,
        verbose_name="آدرس"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات تکمیلی"
    )

    class Meta:

        verbose_name = "فروشنده"
        verbose_name_plural = "فروشندگان"

    def __str__(self):
        return self.name

class Part(models.Model):

    title = models.CharField(
        max_length=200,
        verbose_name="نام قطعه"
    )

    category = models.CharField(
        verbose_name="دسته‌بندی"
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="فروشنده اصلی"
    )

    brand = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="برند"
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی فعلی"
    )

    minimum_stock = models.PositiveIntegerField(
        default=5,
        verbose_name="حداقل موجودی مجاز"
    )

    purchase_price = models.PositiveBigIntegerField(
        default=0,
        verbose_name="قیمت خرید"
    )

    sale_price = models.PositiveBigIntegerField(
        default=0,
        verbose_name="قیمت فروش"
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

        verbose_name = "قطعه"
        verbose_name_plural = "لوازم انبار"

        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def need_restock(self):

        return self.stock <= self.minimum_stock