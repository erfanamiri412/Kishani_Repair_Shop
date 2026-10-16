from django.db import models



class SiteSetting(models.Model):

    shop_name = models.CharField(
        max_length=200,
        default="تعمیرگاه تخصصی کیشانی",
        verbose_name="نام تعمیرگاه"
    )


    logo = models.ImageField(
        upload_to="settings/",
        blank=True,
        null=True,
        verbose_name="لوگو"
    )


    about_text = models.TextField(
        blank=True,
        verbose_name="متن معرفی کوتاه"
    )


    phone_mobile = models.CharField(
        max_length=20,
        verbose_name="شماره همراه"
    )


    phone_fixed = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره ثابت"
    )


    address = models.TextField(
        verbose_name="آدرس"
    )


    working_hours = models.TextField(
        blank=True,
        verbose_name="ساعات کاری"
    )


    instagram = models.URLField(
        blank=True,
        verbose_name="اینستاگرام"
    )


    whatsapp = models.URLField(
        blank=True,
        verbose_name="واتساپ"
    )


    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )


    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )


    class Meta:

        verbose_name = "تنظیمات سایت"

        verbose_name_plural = "تنظیمات سایت"



    def __str__(self):

        return self.shop_name





class Notification(models.Model):


    title = models.CharField(
        max_length=200,
        verbose_name="عنوان اعلان"
    )


    message = models.TextField(
        verbose_name="متن اعلان"
    )


    start_date = models.DateTimeField(
        verbose_name="شروع نمایش"
    )


    end_date = models.DateTimeField(
        verbose_name="پایان نمایش"
    )


    active = models.BooleanField(
        default=True,
        verbose_name="نمایش داده شود"
    )


    class Meta:

        verbose_name = "اعلان"

        verbose_name_plural = "اعلان‌ها"



    def __str__(self):

        return self.title