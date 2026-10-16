from django.db import models
from crm.validators import phone_validator


class ServiceRequest(models.Model):

    name = models.CharField(

        max_length=150,

        verbose_name="نام و نام خانوادگی مشتری"

    )



    phone = models.CharField(

        max_length=20,
        validators=[phone_validator],
        verbose_name="شماره تماس"

    )



    vehicle = models.CharField(

        max_length=150,

        verbose_name="مدل خودرو"

    )



    description = models.TextField(

        verbose_name="شرح درخواست مشتری"

    )


    admin_note = models.TextField(

        blank=True,

        verbose_name="یادداشت داخلی تعمیرگاه"

    )



    created_at = models.DateTimeField(

        auto_now_add=True,

        verbose_name="تاریخ ثبت درخواست"

    )



    updated_at = models.DateTimeField(

        auto_now=True,

        verbose_name="آخرین بروزرسانی"

    )



    class Meta:


        verbose_name = "درخواست خدمات"


        verbose_name_plural = "درخواست‌های خدمات"

        ordering = [

            "-created_at"

        ]



    def __str__(self):

        return f"{self.name} - {self.vehicle}"