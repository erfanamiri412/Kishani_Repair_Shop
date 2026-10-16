from django.db import models
from django.contrib.auth.models import User
from crm.managers import *
from crm.validators import phone_validator

class Customer(models.Model):

    full_name = models.CharField(
        max_length=150,
        verbose_name="نام و نام خانوادگی"
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="شماره تماس",
        validators=[phone_validator],
    )

    address = models.TextField(
        blank=True,
        null=True,
        verbose_name="آدرس"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )


    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"


    def __str__(self):
        return self.full_name


class VehicleBrand(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name="برند خودرو"
    )


    class Meta:
        verbose_name = "برند خودرو"
        verbose_name_plural = "برندهای خودرو"


    def __str__(self):
        return self.name


class Vehicle(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="مالک خودرو"
    )


    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.PROTECT,
        verbose_name="برند خودرو"
    )


    model = models.CharField(
        max_length=100,
        verbose_name="مدل خودرو"
    )


    year = models.PositiveIntegerField(
        verbose_name="سال ساخت"
    )


    plate_number = models.CharField(
        max_length=50,
        verbose_name="شماره پلاک"
    )


    vin = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="شماره شاسی"
    )


    mileage = models.PositiveIntegerField(
        default=0,
        verbose_name="کارکرد خودرو"
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )



    class Meta:
        verbose_name="خودرو"
        verbose_name_plural="خودروها"



    def __str__(self):
        return f"{self.brand} {self.model} - \u2066{self.formatted_plate}\u2069"


class TimeStampedModel(models.Model):

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract = True


class Technician(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )


    expertise = models.CharField(
        max_length=200,
        verbose_name="تخصص"
    )


    active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )


    class Meta:
        verbose_name="تکنسین"
        verbose_name_plural="تکنسین‌ها"



    def __str__(self):
        return self.user.get_full_name()