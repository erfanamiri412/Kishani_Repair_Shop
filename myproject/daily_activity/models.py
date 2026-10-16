from django.db import models
from core.admin import BaseModelAdmin
from django.core.exceptions import ValidationError


class Attendance(models.Model):

    STATUS_CHOICES = [

        ('present', 'حاضر'),
        ('absent', 'غایب'),
        ('leave', 'مرخصی'),
        ('late', 'تاخیر'),
        ('half_day', 'نیمه وقت'),

    ]

    employee = models.ForeignKey(
        'users.EmployeeProfile',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='پرسنل'
    )

    date = models.DateField(
        verbose_name='تاریخ'
    )

    check_in = models.TimeField(
        null=True,
        blank=True,
        verbose_name='ساعت ورود'
    )

    check_out = models.TimeField(
        null=True,
        blank=True,
        verbose_name='ساعت خروج'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present',
        verbose_name='وضعیت حضور'
    )

    note = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def worked_hours(self):

        if not self.check_in or not self.check_out:
            return 0

        from datetime import datetime

        start = datetime.combine(
            self.date,
            self.check_in
        )

        end = datetime.combine(
            self.date,
            self.check_out
        )

        return round(
            (end - start).total_seconds() / 3600,
            2
        )

    def clean(self):

        if (
            self.check_in
            and
            self.check_out
            and
            self.check_out <= self.check_in
        ):

            raise ValidationError(
                "ساعت خروج باید بعد از ساعت ورود باشد."
            )


    class Meta:

        verbose_name = 'حضور و غیاب'
        verbose_name_plural = 'حضور و غیاب'
        ordering = ['-date']
        unique_together = ['employee', 'date']

    def __str__(self):

        return f'{self.employee} - {self.date}'


class DailyExpense(models.Model):

    title = models.CharField(
        max_length=200,
        verbose_name='عنوان هزینه'
    )

    amount = models.PositiveIntegerField(
        verbose_name='مبلغ'
    )

    expense_date = models.DateField(
        verbose_name='تاریخ'
    )

    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        verbose_name = 'هزینه روزانه'
        verbose_name_plural = 'هزینه‌های روزانه'
        ordering = ['-expense_date']

    def __str__(self):

        return self.title


class DailyIncome(models.Model):

    title = models.CharField(
        max_length=200,
        verbose_name='عنوان درآمد'
    )

    amount = models.PositiveIntegerField(
        verbose_name='مبلغ'
    )

    income_date = models.DateField(
        verbose_name='تاریخ'
    )

    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        verbose_name = 'درآمد روزانه'
        verbose_name_plural = 'درآمدهای روزانه'
        ordering = ['-income_date']

    def __str__(self):

        return self.title


class DailyNote(models.Model):

    note_date = models.DateField(
        verbose_name='تاریخ'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )

    description = models.TextField(
        verbose_name='متن یادداشت'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        verbose_name = 'یادداشت روزانه'
        verbose_name_plural = 'یادداشت‌های روزانه'
        ordering = ['-note_date']

    def __str__(self):

        return self.title