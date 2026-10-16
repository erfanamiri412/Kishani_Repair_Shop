"""
==========================================================
Customer History Services

تمام منطق تجاری مربوط به مشتریان در این فایل قرار می‌گیرد.

قوانین مهم:

• هیچ View مستقیماً با Model کار نمی‌کند.
• همه عملیات از طریق Serviceها انجام می‌شود.
• همه اپ‌های پروژه فقط Serviceها را صدا می‌زنند.
• تمام Queryهای پیچیده داخل این فایل قرار می‌گیرند.

این فایل قلب CRM پروژه است.
==========================================================
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import (
    Avg,
    Count,
    Max,
    Min,
    Q,
    Sum,
)
from django.utils import timezone

from audit.models import AuditLog
from crm.models import Invoice
from communications.models import CommunicationLog

from .models import (
    Customer,
    CustomerVehicle,
    CustomerVisit,
    CustomerStatistics,
    CustomerPreference,
    CustomerScore,
    Tag,
    CustomerTag,
    CustomerCommunication,
    CustomerNote,
)

class BaseCustomerService:
    """
    کلاس پایه تمام سرویس‌های customer_history

    تمام سرویس‌ها از این کلاس ارث‌بری می‌کنند.
    """

    model = None

    @classmethod
    def get_queryset(cls):

        if cls.model is None:

            raise NotImplementedError(
                "Model must be defined."
            )

        return cls.model.objects.all()

    @classmethod
    def get_by_id(cls, pk):

        return cls.get_queryset().filter(
            pk=pk
        ).first()

    @classmethod
    def exists(cls, pk):

        return cls.get_queryset().filter(
            pk=pk
        ).exists()

    @classmethod
    def delete(cls, pk):

        obj = cls.get_by_id(pk)

        if obj:

            obj.delete()

        return obj
    
# ==========================================================
# Customer Service
# ==========================================================

class CustomerService(BaseCustomerService):
    """
    سرویس مدیریت مشتریان
    """

    model = Customer

    @classmethod
    def create_customer(
        cls,
        **data
    ):
        """
        ایجاد مشتری جدید
        """

        with transaction.atomic():

            customer = cls.model.objects.create(
                **data
            )

            CustomerPreference.objects.create(
                customer=customer
            )

            CustomerStatistics.objects.create(
                customer=customer
            )

            CustomerScore.objects.create(
                customer=customer
            )

            return customer

    @classmethod
    def update_customer(
        cls,
        customer,
        **data
    ):
        """
        بروزرسانی اطلاعات مشتری
        """

        for key, value in data.items():

            setattr(
                customer,
                key,
                value
            )

        customer.save()

        return customer

    @classmethod
    def get_customer(
        cls,
        customer_id
    ):
        """
        دریافت مشتری
        """

        return (

            cls.get_queryset()

            .select_related(

                "preferences",
                "statistics",
                "score",

            )

            .prefetch_related(

                "vehicles",
                "customer_tags__tag",
                "notes",
                "communications",
                "visits",

            )

            .filter(
                pk=customer_id
            )

            .first()

        )

    @classmethod
    def get_by_phone(
        cls,
        phone
    ):
        """
        جستجو با شماره موبایل
        """

        return cls.get_queryset().filter(
            phone=phone
        ).first()

    @classmethod
    def get_by_national_code(
        cls,
        national_code
    ):
        """
        جستجو با کد ملی
        """

        return cls.get_queryset().filter(
            national_code=national_code
        ).first()
    
# ==========================================================
# Customer Vehicle Service
# ==========================================================

class CustomerVehicleService(BaseCustomerService):
    """
    سرویس مدیریت خودروهای مشتری
    """

    model = CustomerVehicle

    @classmethod
    def create_vehicle(
        cls,
        customer,
        **data
    ):
        """
        ثبت خودروی جدید برای مشتری
        """

        return cls.model.objects.create(

            customer=customer,

            **data

        )

    @classmethod
    def update_vehicle(
        cls,
        vehicle,
        **data
    ):
        """
        بروزرسانی اطلاعات خودرو
        """

        for key, value in data.items():

            setattr(

                vehicle,

                key,

                value

            )

        vehicle.save()

        return vehicle

    @classmethod
    def get_customer_vehicles(
        cls,
        customer
    ):
        """
        تمام خودروهای مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .order_by(

                "plate_number"

            )

        )

    @classmethod
    def get_main_vehicle(
        cls,
        customer
    ):
        """
        خودروی اصلی مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                is_primary=True

            )

            .first()

        )

    @classmethod
    def get_vehicle_by_plate(
        cls,
        plate_number
    ):
        """
        جستجو بر اساس پلاک
        """

        return (

            cls.get_queryset()

            .filter(

                plate_number=plate_number

            )

            .first()

        )

    @classmethod
    def set_primary_vehicle(
        cls,
        vehicle
    ):
        """
        تعیین خودروی اصلی مشتری
        """

        with transaction.atomic():

            cls.get_queryset().filter(

                customer=vehicle.customer

            ).update(

                is_primary=False

            )

            vehicle.is_primary = True

            vehicle.save()

        return vehicle

    @classmethod
    def vehicle_exists(
        cls,
        plate_number
    ):
        """
        بررسی وجود پلاک
        """

        return cls.get_queryset().filter(

            plate_number=plate_number

        ).exists()
    
# ==========================================================
# Customer Visit Service
# ==========================================================

class CustomerVisitService(BaseCustomerService):
    """
    سرویس مدیریت مراجعات مشتری
    """

    model = CustomerVisit

    @classmethod
    def create_visit(
        cls,
        customer,
        vehicle,
        **data
    ):
        """
        ثبت مراجعه جدید
        """

        with transaction.atomic():

            visit = cls.model.objects.create(

                customer=customer,

                vehicle=vehicle,

                **data

            )

            return visit

    @classmethod
    def update_visit(
        cls,
        visit,
        **data
    ):
        """
        بروزرسانی مراجعه
        """

        for key, value in data.items():

            setattr(

                visit,

                key,

                value

            )

        visit.save()

        return visit

    @classmethod
    def get_visit(
        cls,
        visit_id
    ):
        """
        دریافت یک مراجعه
        """

        return (

            cls.get_queryset()

            .select_related(

                "customer",

                "vehicle",

            )

            .prefetch_related(

                "communications",

            )

            .filter(

                pk=visit_id

            )

            .first()

        )

    @classmethod
    def get_customer_visits(
        cls,
        customer
    ):
        """
        تمام مراجعات مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .select_related(

                "vehicle",

            )

            .order_by(

                "-visit_date",

            )

        )

    @classmethod
    def get_vehicle_visits(
        cls,
        vehicle
    ):
        """
        تمام مراجعات خودرو
        """

        return (

            cls.get_queryset()

            .filter(

                vehicle=vehicle

            )

            .order_by(

                "-visit_date",

            )

        )

    @classmethod
    def get_last_visit(
        cls,
        customer
    ):
        """
        آخرین مراجعه مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .order_by(

                "-visit_date",

            )

            .first()

        )

    @classmethod
    def count_customer_visits(
        cls,
        customer
    ):
        """
        تعداد مراجعات مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .count()

        )

    @classmethod
    def has_open_visit(
        cls,
        customer
    ):
        """
        بررسی وجود مراجعه باز
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                status="in_progress",

            )

            .exists()

        )
    
# ==========================================================
# Customer Statistics Service
# ==========================================================

class CustomerStatisticsService(BaseCustomerService):
    """
    سرویس مدیریت آمار مشتری
    """

    model = CustomerStatistics

    @classmethod
    def get_statistics(
        cls,
        customer
    ):
        """
        دریافت آمار مشتری
        """

        statistics, _ = cls.model.objects.get_or_create(
            customer=customer
        )

        return statistics

    @classmethod
    def refresh(
        cls,
        customer
    ):
        """
        بروزرسانی کامل آمار مشتری
        """

        statistics = cls.get_statistics(customer)

        visits = CustomerVisit.objects.filter(
            customer=customer
        )

        invoices = Invoice.objects.filter(
            customer=customer
        )

        statistics.total_visits = visits.count()

        statistics.total_spent = (

            invoices.aggregate(

                total=Sum("total_amount")

            )["total"]

            or 0

        )

        statistics.total_paid = (

            invoices.aggregate(

                total=Sum("paid_amount")

            )["total"]

            or 0

        )

        statistics.total_unpaid = (

            statistics.total_spent
            -
            statistics.total_paid

        )

        statistics.last_visit = (

            visits.order_by(

                "-visit_date"

            ).first()

        )

        statistics.save()

        return statistics
    
    @classmethod
    def increase_visit(
        cls,
        customer
    ):
        """
        افزایش تعداد مراجعات
        """

        statistics = cls.get_statistics(customer)

        statistics.total_visits += 1

        statistics.save(
            update_fields=[
                "total_visits"
            ]
        )

        return statistics

    @classmethod
    def update_last_visit(
        cls,
        customer,
        visit
    ):
        """
        ثبت آخرین مراجعه
        """

        statistics = cls.get_statistics(customer)

        statistics.last_visit = visit

        statistics.save(
            update_fields=[
                "last_visit"
            ]
        )

        return statistics
    
    @classmethod
    def customer_rank(
        cls,
        customer
    ):
        """
        تعیین سطح مشتری
        """

        statistics = cls.get_statistics(customer)

        if statistics.total_spent >= 300_000_000:

            return "VIP"

        if statistics.total_spent >= 100_000_000:

            return "طلایی"

        if statistics.total_spent >= 30_000_000:

            return "نقره‌ای"

        return "عادی"
    
# ==========================================================
# Customer Score Service
# ==========================================================

class CustomerScoreService(BaseCustomerService):
    """
    سرویس امتیازدهی مشتری
    """

    model = CustomerScore

    @classmethod
    def get_score(
        cls,
        customer
    ):
        """
        دریافت رکورد امتیاز مشتری
        """

        score, _ = cls.model.objects.get_or_create(
            customer=customer
        )

        return score

    @classmethod
    def calculate_score(
        cls,
        customer
    ):
        """
        محاسبه امتیاز مشتری
        """

        statistics = CustomerStatisticsService.get_statistics(
            customer
        )

        score = cls.get_score(
            customer
        )

        value = 0

        # ----------------------------
        # تعداد مراجعات
        # ----------------------------

        value += statistics.total_visits * 5

        # ----------------------------
        # مجموع پرداختی
        # ----------------------------

        value += statistics.total_paid // 1_000_000
    
    @classmethod
    def level(
        cls,
        customer
    ):
        """
        تعیین سطح مشتری
        """

        score = cls.get_score(
            customer
        )

        if score.score >= 500:

            return "الماس"

        if score.score >= 300:

            return "طلایی"

        if score.score >= 150:

            return "نقره‌ای"

        return "عادی"
    
    @classmethod
    def is_vip(
        cls,
        customer
    ):
        """
        آیا مشتری VIP است؟
        """

        return cls.level(
            customer
        ) in [

            "طلایی",

            "الماس",

        ]
    
    @classmethod
    def refresh(
        cls,
        customer
    ):
        """
        بروزرسانی کامل امتیاز
        """

        cls.calculate_score(
            customer
        )

        return cls.get_score(
            customer
        )
    
    @classmethod
    def top_customers(
        cls,
        limit=20
    ):
        """
        بهترین مشتریان
        """

        return (

            cls.model.objects

            .select_related(

                "customer"

            )

            .order_by(

                "-score"

            )[:limit]

        )
    
# ==========================================================
# Customer Tag Service
# ==========================================================

class CustomerTagService(BaseCustomerService):
    """
    سرویس مدیریت برچسب‌های مشتری
    """

    model = CustomerTag

    @classmethod
    def add_tag(
        cls,
        customer,
        tag
    ):
        """
        افزودن برچسب
        """

        relation, _ = cls.model.objects.get_or_create(

            customer=customer,

            tag=tag

        )

        return relation

    @classmethod
    def remove_tag(
        cls,
        customer,
        tag
    ):
        """
        حذف برچسب
        """

        cls.model.objects.filter(

            customer=customer,

            tag=tag

        ).delete()

    @classmethod
    def get_customer_tags(
        cls,
        customer
    ):
        """
        لیست برچسب‌های مشتری
        """

        return (

            cls.get_queryset()

            .select_related(

                "tag"

            )

            .filter(

                customer=customer

            )

        )

    @classmethod
    def has_tag(
        cls,
        customer,
        slug
    ):
        """
        بررسی وجود برچسب
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                tag__slug=slug

            )

            .exists()

        )
    
    @classmethod
    def clear_tags(
        cls,
        customer
    ):
        """
        حذف تمام برچسب‌ها
        """

        cls.get_queryset().filter(

            customer=customer

        ).delete()

    @classmethod
    def refresh_auto_tags(
        cls,
        customer
    ):
        """
        بروزرسانی برچسب‌های هوشمند
        """

        cls.clear_tags(customer)

        statistics = CustomerStatisticsService.get_statistics(
            customer
        )

        score = CustomerScoreService.get_score(
            customer
        )

        tags = CustomerLabel.objects.all()

        for tag in tags:

            if tag.slug == "vip":

                if score.score >= 300:

                    cls.add_tag(

                        customer,

                        tag

                    )

            elif tag.slug == "debtor":

                if statistics.total_unpaid > 0:

                    cls.add_tag(

                        customer,

                        tag

                    )

            elif tag.slug == "loyal":

                if statistics.total_visits >= 10:

                    cls.add_tag(

                        customer,

                        tag

                    )

            elif tag.slug == "inactive":

                if (

                    statistics.last_visit

                    and

                    timezone.now().date()

                    -

                    statistics.last_visit.visit_date

                ).days > 180:

                    cls.add_tag(

                        customer,

                        tag

                    )

# ==========================================================
# Customer Preference Service
# ==========================================================

class CustomerPreferenceService(BaseCustomerService):
    """
    سرویس مدیریت تنظیمات و ترجیحات مشتری
    """

    model = CustomerPreference

    @classmethod
    def get_preferences(
        cls,
        customer
    ):
        """
        دریافت تنظیمات مشتری
        """

        preference, _ = cls.model.objects.get_or_create(
            customer=customer
        )

        return preference

    @classmethod
    def update_preferences(
        cls,
        customer,
        **data
    ):
        """
        بروزرسانی تنظیمات
        """

        preference = cls.get_preferences(
            customer
        )

        for key, value in data.items():

            setattr(
                preference,
                key,
                value
            )

        preference.save()

        return preference
    
        tags = CustomerLabel.objects.all()

        for tag in tags:

            if tag.slug == "vip":

                if score.score >= 300:

                    cls.add_tag(

                        customer,

                        tag

                    )

            elif tag.slug == "debtor":

                if statistics.total_unpaid > 0:

                    cls.add_tag(

                        customer,

                        tag

                    )

            elif tag.slug == "loyal":

                if statistics.total_visits >= 10:

                    cls.add_tag(

                        customer,

                        tag

                    )

            elif tag.slug == "inactive":

                if (

                    statistics.last_visit

                    and

                    timezone.now().date()

                    -

                    statistics.last_visit.visit_date

                ).days > 180:

                    cls.add_tag(

                        customer,

                        tag

                    )

    @classmethod
    def enable_whatsapp(
        cls,
        customer
    ):
        """
        فعال کردن واتساپ
        """

        preference = cls.get_preferences(
            customer
        )

        preference.whatsapp_enabled = True

        preference.save(
            update_fields=[
                "whatsapp_enabled"
            ]
        )

        return preference

    @classmethod
    def disable_whatsapp(
        cls,
        customer
    ):
        """
        غیرفعال کردن واتساپ
        """

        preference = cls.get_preferences(
            customer
        )

        preference.whatsapp_enabled = False

        preference.save(
            update_fields=[
                "whatsapp_enabled"
            ]
        )

        return preference
    
    @classmethod
    def preferred_channel(
        cls,
        customer
    ):
        """
        بهترین روش ارتباط
        """

        preference = cls.get_preferences(
            customer
        )

        if preference.whatsapp_enabled:

            return "whatsapp"

        if preference.sms_enabled:

            return "sms"

        return None
    
    @classmethod
    def can_receive_marketing(
        cls,
        customer
    ):
        """
        آیا تبلیغات دریافت کند؟
        """

        preference = cls.get_preferences(
            customer
        )

        return preference.marketing_notifications
    
# ==========================================================
# Customer Communication Service
# ==========================================================

class CustomerCommunicationService(BaseCustomerService):
    """
    سرویس مدیریت ارتباطات مشتری
    """

    model = CustomerCommunication

    @classmethod
    def create(
        cls,
        customer,
        **data
    ):
        """
        ثبت ارتباط جدید
        """

        return cls.model.objects.create(

            customer=customer,

            **data

        )

    @classmethod
    def get_customer_history(
        cls,
        customer
    ):
        """
        تاریخچه ارتباطات مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .order_by(

                "-created_at"

            )

        )

    @classmethod
    def latest(
        cls,
        customer
    ):
        """
        آخرین ارتباط
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .order_by(

                "-created_at"

            )

            .first()

        )
    
    @classmethod
    def sent_messages(
        cls,
        customer
    ):
        """
        پیام‌های ارسال شده
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                direction="outgoing"

            )

            .order_by(

                "-created_at"

            )

        )

    @classmethod
    def received_messages(
        cls,
        customer
    ):
        """
        پیام‌های دریافتی
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                direction="incoming"

            )

            .order_by(

                "-created_at"

            )

        )
    
    @classmethod
    def sms_history(
        cls,
        customer
    ):
        """
        تاریخچه پیامک‌ها
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                channel="sms"

            )

            .order_by(

                "-created_at"

            )

        )

    @classmethod
    def whatsapp_history(
        cls,
        customer
    ):
        """
        تاریخچه واتساپ
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer,

                channel="whatsapp"

            )

            .order_by(

                "-created_at"

            )

        )
    
    @classmethod
    def count_messages(
        cls,
        customer
    ):
        """
        تعداد ارتباطات
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .count()

        )

    @classmethod
    def delete_history(
        cls,
        customer
    ):
        """
        حذف تاریخچه ارتباطات
        """

        cls.get_queryset().filter(

            customer=customer

        ).delete()

# ==========================================================
# Customer Search Service
# ==========================================================

class CustomerSearchService(BaseCustomerService):
    """
    سرویس جستجو و فیلتر مشتریان
    """

    model = Customer

    @classmethod
    def search(
        cls,
        keyword
    ):
        """
        جستجو بر اساس نام، موبایل و پلاک
        """

        return (

            cls.get_queryset()

            .filter(

                Q(full_name__icontains=keyword)

                |

                Q(phone__icontains=keyword)

                |

                Q(

                    vehicles__license_plate__icontains=keyword

                )

            )

            .distinct()

        )

    @classmethod
    def get_by_phone(
        cls,
        phone
    ):
        """
        جستجو بر اساس شماره موبایل
        """

        return (

            cls.get_queryset()

            .filter(

                phone=phone

            )

            .first()

        )

    @classmethod
    def get_by_vehicle(
        cls,
        plate
    ):
        """
        پیدا کردن مشتری از روی پلاک
        """

        return (

            cls.get_queryset()

            .filter(

                vehicles__license_plate=plate

            )

            .distinct()

            .first()

        )
    
    @classmethod
    def active_customers(
        cls
    ):
        """
        مشتریان فعال
        """

        return (

            cls.get_queryset()

            .filter(

                is_active=True

            )

        )

    @classmethod
    def inactive_customers(
        cls
    ):
        """
        مشتریان غیرفعال
        """

        return (

            cls.get_queryset()

            .filter(

                is_active=False

            )

        )
    
    @classmethod
    def vip_customers(
        cls
    ):
        """
        مشتریان VIP
        """

        return (

            cls.get_queryset()

            .filter(

                score__score__gte=300

            )

            .order_by(

                "-score__score"

            )

        )

    @classmethod
    def debtors(
        cls
    ):
        """
        مشتریان بدهکار
        """

        return (

            cls.get_queryset()

            .filter(

                statistics__total_unpaid__gt=0

            )

        )
    
    @classmethod
    def latest(
        cls,
        limit=20
    ):
        """
        آخرین مشتریان ثبت شده
        """

        return (

            cls.get_queryset()

            .order_by(

                "-created_at"

            )[:limit]

        )

    @classmethod
    def count(
        cls
    ):
        """
        تعداد مشتریان
        """

        return cls.get_queryset().count()
    
    @classmethod
    def autocomplete(
        cls,
        keyword,
        limit=10
    ):
        """
        جستجوی سریع برای AutoComplete
        """

        return (

            cls.search(keyword)

            [:limit]

        )
    
# ==========================================================
# Customer Note Service
# ==========================================================

class CustomerNoteService(BaseCustomerService):
    """
    سرویس مدیریت یادداشت‌های مشتری
    """

    model = CustomerNote

    @classmethod
    def create_note(
        cls,
        customer,
        author,
        title,
        note,
        **extra
    ):
        """
        ثبت یادداشت جدید
        """

        return cls.model.objects.create(

            customer=customer,

            author=author,

            title=title,

            note=note,

            **extra

        )

    @classmethod
    def update_note(
        cls,
        note,
        **data
    ):
        """
        بروزرسانی یادداشت
        """

        for key, value in data.items():

            setattr(

                note,

                key,

                value

            )

        note.save()

        return note

    @classmethod
    def get_note(
        cls,
        note_id
    ):
        """
        دریافت یک یادداشت
        """

        return (

            cls.get_queryset()

            .select_related(

                "customer",

                "author",

            )

            .filter(

                pk=note_id

            )

            .first()

        )
    
    @classmethod
    def customer_notes(
        cls,
        customer
    ):
        """
        تمام یادداشت‌های مشتری
        """

        return (

            cls.get_queryset()

            .filter(

                customer=customer

            )

            .select_related(

                "author"

            )

            .order_by(

                "-created_at"

            )

        )

    @classmethod
    def latest_note(
        cls,
        customer
    ):
        """
        آخرین یادداشت
        """

        return (

            cls.customer_notes(

                customer

            ).first()

        )
    
    @classmethod
    def important_notes(
        cls,
        customer
    ):
        """
        یادداشت‌های مهم
        """

        return (

            cls.customer_notes(

                customer

            ).filter(

                is_important=True

            )

        )

    @classmethod
    def pinned_notes(
        cls,
        customer
    ):
        """
        یادداشت‌های سنجاق شده
        """

        return (

            cls.customer_notes(

                customer

            ).filter(

                is_pinned=True

            )

        )
    
    @classmethod
    def delete_note(
        cls,
        note
    ):
        """
        حذف یادداشت
        """

        note.delete()

    @classmethod
    def count_notes(
        cls,
        customer
    ):
        """
        تعداد یادداشت‌ها
        """

        return cls.customer_notes(

            customer

        ).count()
    
# ==========================================================
# Customer Analytics Service
# ==========================================================

class CustomerAnalyticsService(BaseCustomerService):
    """
    سرویس تحلیل مشتریان
    """

    @classmethod
    def total_customers(
        cls
    ):
        """
        تعداد کل مشتریان
        """

        return Customer.objects.count()

    @classmethod
    def active_customers(
        cls
    ):
        """
        تعداد مشتریان فعال
        """

        return Customer.objects.filter(

            is_active=True

        ).count()

    @classmethod
    def inactive_customers(
        cls
    ):
        """
        تعداد مشتریان غیرفعال
        """

        return Customer.objects.filter(

            is_active=False

        ).count()

    @classmethod
    def vip_customers(
        cls
    ):
        """
        تعداد مشتریان VIP
        """

        return CustomerScore.objects.filter(

            score__gte=300

        ).count()
    
    @classmethod
    def total_debt(
        cls
    ):
        """
        مجموع بدهی مشتریان
        """

        return (

            CustomerStatistics.objects.aggregate(

                total=Sum(

                    "total_unpaid"

                )

            )["total"]

            or 0

        )

    @classmethod
    def total_income(
        cls
    ):
        """
        مجموع پرداختی مشتریان
        """

        return (

            CustomerStatistics.objects.aggregate(

                total=Sum(

                    "total_paid"

                )

            )["total"]

            or 0

        )
    
    @classmethod
    def average_customer_score(
        cls
    ):
        """
        میانگین امتیاز مشتریان
        """

        return (

            CustomerScore.objects.aggregate(

                avg=Avg(

                    "score"

                )

            )["avg"]

            or 0

        )

    @classmethod
    def average_visits(
        cls
    ):
        """
        میانگین مراجعات
        """

        return (

            CustomerStatistics.objects.aggregate(

                avg=Avg(

                    "total_visits"

                )

            )["avg"]

            or 0

        )
    
    @classmethod
    def top_customers(
        cls,
        limit=10
    ):
        """
        بهترین مشتریان
        """

        return (

            CustomerScore.objects

            .select_related(

                "customer"

            )

            .order_by(

                "-score"

            )[:limit]

        )

    @classmethod
    def most_active_customers(
        cls,
        limit=10
    ):
        """
        بیشترین مراجعات
        """

        return (

            CustomerStatistics.objects

            .select_related(

                "customer"

            )

            .order_by(

                "-total_visits"

            )[:limit]

        )
    
    @classmethod
    def debtors(
        cls,
        limit=10
    ):
        """
        بیشترین بدهکارها
        """

        return (

            CustomerStatistics.objects

            .select_related(

                "customer"

            )

            .filter(

                total_unpaid__gt=0

            )

            .order_by(

                "-total_unpaid"

            )[:limit]

        )

    @classmethod
    def newest_customers(
        cls,
        limit=10
    ):
        """
        جدیدترین مشتریان
        """

        return (

            Customer.objects

            .order_by(

                "-created_at"

            )[:limit]

        )

    # ==========================================================
# Customer Insight Service
# ==========================================================

class CustomerInsightService(BaseCustomerService):
    """
    سرویس تحلیل هوشمند مشتری
    """

    @classmethod
    def customer_profile(
        cls,
        customer
    ):
        """
        پروفایل کامل مشتری
        """

        statistics = CustomerStatisticsService.get_statistics(
            customer
        )

        score = CustomerScoreService.get_score(
            customer
        )

        preferences = CustomerPreferenceService.get_preferences(
            customer
        )

        tags = CustomerTagService.get_customer_tags(
            customer
        )

        return {

            "customer": customer,

            "statistics": statistics,

            "score": score,

            "preferences": preferences,

            "tags": tags,

        }
    
    @classmethod
    def customer_summary(
        cls,
        customer
    ):
        """
        خلاصه وضعیت مشتری
        """

        statistics = CustomerStatisticsService.get_statistics(
            customer
        )

        return {

            "visits": statistics.total_visits,

            "paid": statistics.total_paid,

            "unpaid": statistics.total_unpaid,

            "last_visit": statistics.last_visit,

            "level": CustomerScoreService.level(
                customer
            ),

            "vip": CustomerScoreService.is_vip(
                customer
            ),

        }
    
    @classmethod
    def customer_health(
        cls,
        customer
    ):
        """
        وضعیت سلامت ارتباط با مشتری
        """

        statistics = CustomerStatisticsService.get_statistics(
            customer
        )

        if not statistics.last_visit:

            return "new"

        days = (

            timezone.now().date()

            -

            statistics.last_visit.visit_date

        ).days

        if days <= 30:

            return "excellent"

        if days <= 90:

            return "good"

        if days <= 180:

            return "warning"

        return "critical"
    
    @classmethod
    def need_followup(
        cls,
        customer
    ):
        """
        آیا مشتری نیاز به پیگیری دارد؟
        """

        health = cls.customer_health(
            customer
        )

        return health in [

            "warning",

            "critical",

        ]
    
    @classmethod
    def customer_value(
        cls,
        customer
    ):
        """
        ارزش مشتری
        """

        statistics = CustomerStatisticsService.get_statistics(
            customer
        )

        if statistics.total_paid >= 300_000_000:

            return "high"

        if statistics.total_paid >= 100_000_000:

            return "medium"

        return "low"
    
    @classmethod
    def dashboard_card(
        cls,
        customer
    ):
        """
        اطلاعات آماده برای داشبورد
        """

        return {

            "summary":

                cls.customer_summary(customer),

            "health":

                cls.customer_health(customer),

            "value":

                cls.customer_value(customer),

            "followup":

                cls.need_followup(customer),

        }
    
# ==========================================================
# Customer Facade Service
# ==========================================================

class CustomerFacadeService:
    """
    درگاه اصلی سرویس‌های مشتری
    """

    customer = CustomerService

    vehicle = CustomerVehicleService

    visit = CustomerVisitService

    statistics = CustomerStatisticsService

    score = CustomerScoreService

    tags = CustomerTagService

    preferences = CustomerPreferenceService

    communications = CustomerCommunicationService

    notes = CustomerNoteService

    search = CustomerSearchService

    analytics = CustomerAnalyticsService

    insight = CustomerInsightService

    @classmethod
    def full_profile(
        cls,
        customer
    ):
        """
        پروفایل کامل مشتری
        """

        return {

            "customer":

                customer,

            "vehicles":

                cls.vehicle.customer_vehicles(

                    customer

                ),

            "statistics":

                cls.statistics.get_statistics(

                    customer

                ),

            "score":

                cls.score.get_score(

                    customer

                ),

            "notes":

                cls.notes.customer_notes(

                    customer

                ),

            "tags":

                cls.tags.get_customer_tags(

                    customer

                ),

            "preferences":

                cls.preferences.get_preferences(

                    customer

                ),

        }
    
    @classmethod
    def dashboard(
        cls,
        customer
    ):
        """
        داده آماده داشبورد
        """

        return {

            "summary":

                cls.insight.customer_summary(

                    customer

                ),

            "dashboard":

                cls.insight.dashboard_card(

                    customer

                ),

            "latest_note":

                cls.notes.latest_note(

                    customer

                ),

            "latest_message":

                cls.communications.latest(

                    customer

                ),

        }

    @classmethod
    def quick_search(
        cls,
        keyword
    ):
        """
        جستجوی سریع
        """

        return cls.search.search(

            keyword

        )
    
    @classmethod
    def customer_overview(
        cls,
        customer
    ):
        """
        نمای کلی مشتری
        """

        return {

            "profile":

                cls.full_profile(

                    customer

                ),

            "dashboard":

                cls.dashboard(

                    customer

                ),

            "health":

                cls.insight.customer_health(

                    customer

                ),

            "value":

                cls.insight.customer_value(

                    customer

                ),

        }
    
# ==========================================================
# Service Shortcuts
# ==========================================================

customer_service = CustomerService

vehicle_service = CustomerVehicleService

visit_service = CustomerVisitService

statistics_service = CustomerStatisticsService

score_service = CustomerScoreService

tag_service = CustomerTagService

preference_service = CustomerPreferenceService

communication_service = CustomerCommunicationService

note_service = CustomerNoteService

search_service = CustomerSearchService

analytics_service = CustomerAnalyticsService

insight_service = CustomerInsightService

customer_facade = CustomerFacadeService