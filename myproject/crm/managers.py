from django.db import models
from django.utils import timezone

class CustomerCRMQuerySet(models.QuerySet):
    """
    QuerySet اختصاصی CRM
    """

    def active(self):
        """
        مشتریان فعال
        """

        return self.filter(
            is_active=True
        )

    def inactive(self):
        """
        مشتریان غیرفعال
        """

        return self.filter(
            is_active=False
        )
    
    def blacklisted(self):
        """
        مشتریان لیست سیاه
        """

        return self.filter(
            blacklist_record__is_active=True
        )

    def not_blacklisted(self):
        """
        مشتریان عادی
        """

        return self.exclude(
            blacklist_record__is_active=True
        )
    
    def vip(self):
        """
        مشتریان VIP
        """

        return self.filter(
            segments__code="VIP"
        )

    def by_segment(self, code):
        """
        فیلتر بر اساس Segment
        """

        return self.filter(
            segments__code=code
        )

    def need_followup(self):
        """
        مشتریانی که پیگیری باز دارند
        """

        return self.filter(
            followups__is_completed=False
        ).distinct()
    
    def overdue_followups(self):
        """
        مشتریانی که پیگیری عقب افتاده دارند
        """

        return self.filter(
            followups__is_completed=False,
            followups__due_date__lt=timezone.now()
        ).distinct()


class CustomerCRMManager(models.Manager):
    """
    Manager اختصاصی مشتریان CRM
    """

    def get_queryset(self):
        return CustomerCRMQuerySet(
            self.model,
            using=self._db
        )

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()

    def vip(self):
        return self.get_queryset().vip()

    def blacklisted(self):
        return self.get_queryset().blacklisted()

    def not_blacklisted(self):
        return self.get_queryset().not_blacklisted()

    def by_segment(self, code):
        return self.get_queryset().by_segment(code)

    def need_followup(self):
        return self.get_queryset().need_followup()

    def overdue_followups(self):
        return self.get_queryset().overdue_followups()

    def recently_contacted(self):
        return self.get_queryset().recently_contacted()