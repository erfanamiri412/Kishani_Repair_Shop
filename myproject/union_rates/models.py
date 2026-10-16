from django.db import models



class Vehicle(models.Model):

    name = models.CharField(
        max_length=150,
        verbose_name="نام خودرو"
    )

    engine = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="نوع موتور"
    )


    class Meta:

        verbose_name = "خودرو"
        verbose_name_plural = "خودروها"



    def __str__(self):

        return self.name




class UnionService(models.Model):

    title = models.CharField(
        max_length=200,
        verbose_name="نام خدمت"
    )


    category = models.CharField(
        max_length=100,
        verbose_name="دسته‌بندی خدمت"
    )


    class Meta:

        verbose_name = "خدمت اتحادیه"
        verbose_name_plural = "خدمات اتحادیه"



    def __str__(self):

        return self.title





class UnionRate(models.Model):


    vehicle = models.ForeignKey(

        Vehicle,

        on_delete=models.CASCADE,

        verbose_name="خودرو"

    )


    service = models.ForeignKey(

        UnionService,

        on_delete=models.CASCADE,

        verbose_name="خدمت"

    )


    price = models.PositiveBigIntegerField(

        verbose_name="اجرت اتحادیه"

    )


    year = models.PositiveIntegerField(

        verbose_name="سال نرخ نامه"

    )


    pdf_source = models.CharField(

        max_length=255,

        blank=True,

        verbose_name="منبع نرخ"

    )


    description = models.TextField(

        blank=True,

        verbose_name="توضیحات"

    )



    class Meta:

        verbose_name = "نرخ اتحادیه"

        verbose_name_plural = "نرخ‌های اتحادیه"



    def __str__(self):

        return f"{self.vehicle} - {self.service}"