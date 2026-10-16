from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from audit.models import AuditLog, CustomerPart, InventoryUsedPart, PurchasedPart
from communications.models import (
    CommunicationQueue,
    CommunicationTemplate,
    Reminder,
)
from communications.services import CommunicationService
from crm.models import CustomerVehicle, CustomerVisit, Repair, RepairPart

from .models import MaintenanceReminderType, MaintenanceRule
from .predictor import ServiceIntervalPredictor


DEFAULT_REMINDER_TYPES = [
    ("تعویض روغن", 10),
    ("فیلتر روغن", 20),
    ("فیلتر هوا", 30),
    ("فیلتر سوخت", 40),
    ("تسمه تایم", 50),
    ("روغن گیربکس", 60),
    ("مایع خنک‌کننده", 70),
    ("سرویس ترمز", 80),
    ("بررسی باتری", 90),
    ("جابجایی لاستیک", 100),
    ("معاینه فنی", 110),
    ("بازدید چهارچرخ", 120),
    ("عیب‌یابی", 130),
    ("سرویس دوره‌ای", 140),
    ("بازدید عمومی", 150),
    ("بیمه خودرو", 160),
    ("سفارشی", 170),
]


DEFAULT_TEMPLATES = {
    "maintenance_oil_change": (
        "یادآوری تعویض روغن",
        "maintenance_oil_change",
        "موعد تعویض روغن {{ vehicle }} نزدیک شده است. برای سرویس خودرو با تعمیرگاه کیشانی در تماس باشید.",
    ),
    "maintenance_four_wheel": (
        "یادآوری بازدید چهارچرخ",
        "maintenance_four_wheel",
        "زمان بازدید چهارچرخ {{ vehicle }} نزدیک شده است. برای بررسی خودرو با تعمیرگاه کیشانی هماهنگ کنید.",
    ),
    "maintenance_diagnostic": (
        "یادآوری عیب‌یابی",
        "maintenance_diagnostic",
        "برای بررسی دوره‌ای و عیب‌یابی {{ vehicle }} زمان سرویس نزدیک شده است. تعمیرگاه کیشانی آماده خدمت‌رسانی است.",
    ),
    "maintenance_periodic": (
        "یادآوری سرویس دوره‌ای",
        "maintenance_periodic",
        "زمان سرویس دوره‌ای {{ vehicle }} نزدیک شده است. برای نگهداری اصولی خودرو با تعمیرگاه کیشانی تماس بگیرید.",
    ),
    "maintenance_general": (
        "یادآوری مراجعه دوره‌ای",
        "maintenance_general",
        "حدود یک سال از آخرین مراجعه {{ vehicle }} گذشته است. برای بازدید دوره‌ای خودرو به تعمیرگاه کیشانی مراجعه کنید.",
    ),
    "maintenance_brake": (
        "یادآوری سرویس ترمز",
        "maintenance_brake",
        "زمان بازدید سیستم ترمز {{ vehicle }} نزدیک شده است. برای بررسی خودرو با تعمیرگاه کیشانی هماهنگ کنید.",
    ),
    "maintenance_battery": (
        "یادآوری بررسی باتری",
        "maintenance_battery",
        "زمان بررسی باتری {{ vehicle }} نزدیک شده است. برای سرویس خودرو با تعمیرگاه کیشانی تماس بگیرید.",
    ),
    "maintenance_gearbox": (
        "یادآوری روغن گیربکس",
        "maintenance_gearbox",
        "زمان بررسی و سرویس روغن گیربکس {{ vehicle }} نزدیک شده است.",
    ),
}


DEFAULT_RULES = [
    {
        "title": "تعویض روغن",
        "reminder_type": "تعویض روغن",
        "keywords": [
            "تعویض روغن",
            "تعویض روغن موتور",
            "روغن موتور",
            "oil change",
        ],
        "interval_months": 6,
        "lead_days": 14,
        "grace_days": 45,
        "template_slug": "maintenance_oil_change",
    },
    {
        "title": "بازدید چهارچرخ",
        "reminder_type": "بازدید چهارچرخ",
        "keywords": [
            "بازدید چهارچرخ",
            "بازدید چهار چرخ",
            "چهارچرخ",
            "چهار چرخ",
            "میزان فرمان",
            "چرخ ها",
            "چرخ‌ها",
        ],
        "interval_months": 12,
        "lead_days": 21,
        "grace_days": 60,
        "template_slug": "maintenance_four_wheel",
    },
    {
        "title": "عیب‌یابی دوره‌ای",
        "reminder_type": "عیب‌یابی",
        "keywords": ["عیب یابی", "عیب‌یابی", "دیاگ", "diagnostic"],
        "interval_months": 12,
        "lead_days": 14,
        "grace_days": 45,
        "template_slug": "maintenance_diagnostic",
    },
    {
        "title": "سرویس دوره‌ای",
        "reminder_type": "سرویس دوره‌ای",
        "keywords": ["سرویس دوره‌ای", "سرویس دوره ای", "سرویس دوره"],
        "interval_months": 6,
        "lead_days": 14,
        "grace_days": 45,
        "template_slug": "maintenance_periodic",
    },
    {
        "title": "یادآوری سالانه مراجعه",
        "reminder_type": "بازدید عمومی",
        "keywords": ["*"],
        "interval_months": 12,
        "lead_days": 7,
        "grace_days": 30,
        "template_slug": "maintenance_general",
    },
    {
        "title": "بازدید ترمز",
        "reminder_type": "سرویس ترمز",
        "keywords": ["ترمز", "لنت", "سرویس ترمز"],
        "interval_months": 12,
        "lead_days": 14,
        "grace_days": 45,
        "template_slug": "maintenance_brake",
    },
    {
        "title": "بررسی باتری",
        "reminder_type": "بررسی باتری",
        "keywords": ["باتری", "باطری"],
        "interval_months": 12,
        "lead_days": 14,
        "grace_days": 45,
        "template_slug": "maintenance_battery",
    },
    {
        "title": "روغن گیربکس",
        "reminder_type": "روغن گیربکس",
        "keywords": ["روغن گیربکس", "تعویض روغن گیربکس"],
        "interval_months": 24,
        "lead_days": 21,
        "grace_days": 60,
        "template_slug": "maintenance_gearbox",
    },
]


class ServiceEvent:
    __slots__ = (
        "date",
        "text",
        "source",
        "source_id",
        "timestamp",
    )

    def __init__(self, *, event_date, text="", source="", source_id=None, timestamp=None):
        self.date = event_date
        self.text = (text or "").strip().lower()
        self.source = source
        self.source_id = source_id
        self.timestamp = timestamp or datetime.combine(event_date, time.min)


class VehicleHistoryService:
    """تبدیل سوابق تعمیرگاه به تاریخچه متنی سرویس، بدون استفاده از کارکرد."""

    @staticmethod
    def _normalize_text(value):
        return (
            str(value or "")
            .strip()
            .lower()
            .replace("ي", "ی")
            .replace("ك", "ک")
        )

    @classmethod
    def events_for_vehicle(cls, vehicle):
        events = []

        visits = (
            CustomerVisit.objects
            .filter(vehicle=vehicle)
            .only(
                "id",
                "complaint",
                "diagnosis",
                "performed_services",
                "recommendation",
                "arrived_at",
                "status",
            )
        )

        for visit in visits:
            if visit.status == "cancelled":
                continue
            timestamp = visit.arrived_at
            events.append(
                ServiceEvent(
                    event_date=timestamp.date(),
                    timestamp=timestamp,
                    text=" ".join(
                        [
                            visit.complaint or "",
                            visit.diagnosis or "",
                            visit.performed_services or "",
                            visit.recommendation or "",
                        ]
                    ),
                    source="customer_visit",
                    source_id=visit.id,
                )
            )

        audits = (
            AuditLog.objects
            .filter(vehicle=vehicle)
            .select_related("service_request")
            .prefetch_related(
                Prefetch(
                    "inventory_parts",
                    queryset=InventoryUsedPart.objects.select_related("part"),
                ),
                "purchased_parts",
                "customer_parts",
            )
            .only(
                "id",
                "work_description",
                "manager_note",
                "service_date",
                "created_at",
                "service_request_id",
            )
        )

        for audit in audits:
            part_text = []
            part_text.extend(
                str(item.part.title)
                for item in audit.inventory_parts.all()
                if getattr(item.part, "title", None)
            )
            part_text.extend(
                item.part_name
                for item in audit.purchased_parts.all()
                if item.part_name
            )
            part_text.extend(
                item.part_name
                for item in audit.customer_parts.all()
                if item.part_name
            )

            events.append(
                ServiceEvent(
                    event_date=audit.service_date,
                    timestamp=audit.created_at,
                    text=" ".join(
                        [
                            audit.work_description or "",
                            audit.manager_note or "",
                            " ".join(part_text),
                        ]
                    ),
                    source="audit",
                    source_id=audit.id,
                )
            )

        repairs = (
            Repair.objects
            .filter(vehicle=vehicle)
            .select_related("service_request")
            .prefetch_related(
                Prefetch(
                    "parts",
                    queryset=RepairPart.objects.select_related("inventory_item"),
                )
            )
            .only(
                "id",
                "created_at",
                "delivered_at",
                "customer_problem",
                "mechanic_report",
                "service_request_id",
            )
        )

        for repair in repairs:
            repair_part_text = [
                str(part.inventory_item.title)
                for part in repair.parts.all()
                if getattr(part.inventory_item, "title", None)
            ]

            timestamp = repair.delivered_at or repair.created_at
            events.append(
                ServiceEvent(
                    event_date=timestamp.date(),
                    timestamp=timestamp,
                    text=" ".join(
                        [
                            repair.customer_problem or "",
                            repair.mechanic_report or "",
                            " ".join(repair_part_text),
                        ]
                    ),
                    source="repair",
                    source_id=repair.id,
                )
            )

        return sorted(events, key=lambda item: item.timestamp)

    @classmethod
    def last_event(cls, vehicle):
        events = cls.events_for_vehicle(vehicle)
        return events[-1] if events else None


class MaintenanceTemplateService:
    @staticmethod
    def ensure_defaults():
        result = {}
        for slug, (title, template_slug, body) in DEFAULT_TEMPLATES.items():
            template, _ = CommunicationTemplate.objects.get_or_create(
                slug=template_slug,
                defaults={
                    "title": title,
                    "template_type": "maintenance_due",
                    "body": body,
                    "description": "قالب سیستمی یادآوری نگهداری خودرو",
                    "is_active": True,
                },
            )
            result[template_slug] = template
        return result


class MaintenanceRuleSeedService:
    @classmethod
    def seed(cls):
        types = {}
        for title, order in DEFAULT_REMINDER_TYPES:
            reminder_type, _ = MaintenanceReminderType.objects.update_or_create(
                title=title,
                defaults={
                    "order": order,
                    "is_active": True,
                },
            )
            types[title] = reminder_type

        templates = MaintenanceTemplateService.ensure_defaults()
        created = 0
        updated = 0

        for item in DEFAULT_RULES:
            defaults = {
                "description": "",
                "reminder_type": types[item["reminder_type"]],
                "keywords": item["keywords"],
                "interval_months": item["interval_months"],
                "lead_days": item["lead_days"],
                "grace_days": item["grace_days"],
                "send_window_start": time(9, 0),
                "send_window_end": time(12, 0),
                "template": templates.get(item["template_slug"]),
                "automatic": True,
                "is_active": True,
            }

            rule, was_created = MaintenanceRule.objects.get_or_create(
                title=item["title"],
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                for field, value in defaults.items():
                    setattr(rule, field, value)
                rule.save()
                updated += 1

        return {
            "created": created,
            "updated": updated,
            "templates": len(templates),
            "reminder_types": len(types),
        }


class MaintenanceEngine:
    """موتور تشخیص موعد سرویس؛ تصمیم‌گیری فقط بر اساس تاریخ و کلیدواژه."""

    MAX_AUTOMATIC_PER_DAY = 1

    def __init__(self, communication_service=None):
        self.communication = communication_service or CommunicationService()

    @staticmethod
    def add_months(value, months):
        months = int(months or 0)
        if months <= 0:
            return value
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        return date(year, month, min(value.day, last_day))

    @staticmethod
    def customer_allows_sms(customer):
        try:
            preferences = customer.preferences
        except Exception:
            preferences = None

        if preferences is None:
            return True
        if preferences.preferred_contact_method == "none":
            return False
        if preferences.preferred_contact_method not in {"sms", ""}:
            return False
        return bool(preferences.receive_service_reminders)

    @staticmethod
    def active_phone(customer):
        phone = CommunicationService.normalize_phone(
            getattr(customer, "mobile", None)
        )
        if not CommunicationService.validate_phone(phone):
            return ""
        return phone

    def already_scheduled_for_today(self, customer_id, as_of):
        day_start = timezone.make_aware(
            datetime.combine(as_of, time.min),
            timezone.get_current_timezone(),
        )
        day_end = day_start + timedelta(days=1)
        limit = max(
            1,
            int(
                getattr(
                    settings,
                    "MAINTENANCE_MAX_AUTOMATIC_SMS_PER_DAY",
                    self.MAX_AUTOMATIC_PER_DAY,
                )
            ),
        )
        return (
            CommunicationQueue.objects
            .filter(
                customer_id=customer_id,
                channel="sms",
                reminder__isnull=False,
                scheduled_at__gte=day_start,
                scheduled_at__lt=day_end,
            )
            .exclude(status=CommunicationQueue.STATUS_CANCELLED)
            .count()
            >= limit
        )

    @staticmethod
    def event_matches(rule, event):
        normalized = VehicleHistoryService._normalize_text(event.text)
        for keyword in rule.keywords or []:
            normalized_keyword = VehicleHistoryService._normalize_text(keyword)
            if not normalized_keyword:
                continue
            if normalized_keyword == "*":
                return True
            if normalized_keyword in normalized:
                return True
        return False

    def find_matching_events(self, rule, events):
        return [
            event
            for event in events
            if self.event_matches(rule, event)
        ]

    def build_context(
        self,
        *,
        customer,
        vehicle,
        rule,
        event,
        due_date,
        as_of,
        prediction=None,
    ):
        days_remaining = (due_date - as_of).days if due_date else None
        return {
            "customer_name": customer.full_name,
            "customer_phone": customer.mobile,
            "vehicle": str(vehicle),
            "vehicle_brand": vehicle.brand,
            "vehicle_company": vehicle.company,
            "vehicle_model": vehicle.model,
            "plate_number": vehicle.plate_number,
            "service_name": rule.title,
            "service_type": rule.reminder_type.title,
            "due_date": due_date.strftime("%Y/%m/%d") if due_date else "",
            "last_service_date": event.date.strftime("%Y/%m/%d"),
            "days_remaining": days_remaining,
            "reason": f"بر اساس آخرین سابقه مرتبط با {rule.title}",
            "prediction_source": (prediction or {}).get("source", "rule"),
            "prediction_confidence": (prediction or {}).get("confidence", 0),
        }

    def cancel_stale_reminders(self, *, vehicle, rule, latest_event):
        stale = (
            Reminder.objects
            .filter(
                vehicle=vehicle,
                customer=vehicle.customer,
                reminder_type=rule.reminder_type.title,
                title=rule.title,
                status__in=[
                    Reminder.STATUS_PENDING,
                    Reminder.STATUS_SCHEDULED,
                ],
            )
            .exclude(last_event_date__gte=latest_event.date)
        )

        for reminder in stale:
            for queue in reminder.queue_items.filter(
                status__in=[
                    CommunicationQueue.STATUS_PENDING,
                    CommunicationQueue.STATUS_FAILED,
                ]
            ):
                queue.status = CommunicationQueue.STATUS_CANCELLED
                queue.last_error = "یادآوری به دلیل ثبت سرویس جدید لغو شد."
                queue.save(
                    update_fields=[
                        "status",
                        "last_error",
                        "updated_at",
                    ]
                )

            reminder.status = Reminder.STATUS_CANCELLED
            reminder.save(update_fields=["status", "updated_at"])

    def create_reminder(self, *, customer, vehicle, rule, event, due_date, as_of):
        reminder, created = Reminder.objects.get_or_create(
            vehicle=vehicle,
            customer=customer,
            reminder_type=rule.reminder_type.title,
            title=rule.title,
            due_date=due_date,
            defaults={
                "description": f"بر اساس رویداد {event.date.strftime('%Y/%m/%d')}",
                "status": Reminder.STATUS_PENDING,
                "auto_generated": True,
                "last_event_date": event.date,
            },
        )
        return reminder, created

    def _send_time(self, *, rule, as_of):
        now = timezone.now()
        current_local = timezone.localtime(now)
        start = rule.send_window_start
        end = rule.send_window_end

        if as_of == timezone.localdate():
            if current_local.time() < start:
                target_date = as_of
            elif current_local.time() <= end:
                return now
            else:
                target_date = as_of + timedelta(days=1)
        else:
            target_date = as_of

        return timezone.make_aware(
            datetime.combine(target_date, start),
            timezone.get_current_timezone(),
        )

    def evaluate(self, as_of=None, *, dry_run=False):
        as_of = as_of or timezone.localdate()
        rules = list(
            MaintenanceRule.objects
            .filter(is_active=True, automatic=True)
            .select_related("reminder_type", "template")
            .order_by("title", "id")
        )
        vehicles = list(
            CustomerVehicle.objects
            .select_related("customer")
            .all()
        )

        stats = {
            "vehicles": len(vehicles),
            "rules": len(rules),
            "matched": 0,
            "created": 0,
            "queued": 0,
            "skipped": 0,
            "errors": 0,
        }

        histories = {
            vehicle.id: VehicleHistoryService.events_for_vehicle(vehicle)
            for vehicle in vehicles
        }

        for vehicle in vehicles:
            customer = vehicle.customer
            if not self.customer_allows_sms(customer):
                continue
            if not self.active_phone(customer):
                continue

            events = histories[vehicle.id]
            if not events:
                continue

            for rule in rules:
                matching_events = self.find_matching_events(rule, events)
                if not matching_events:
                    continue

                event = matching_events[-1]
                stats["matched"] += 1

                if not dry_run:
                    self.cancel_stale_reminders(
                        vehicle=vehicle,
                        rule=rule,
                        latest_event=event,
                    )

                fallback_days = max(1, rule.interval_months) * 30
                prediction = ServiceIntervalPredictor.predict(
                    matching_events,
                    fallback_days=fallback_days,
                )

                if prediction["source"] == "history":
                    due_date = event.date + timedelta(
                        days=prediction["interval_days"]
                    )
                else:
                    due_date = self.add_months(
                        event.date,
                        rule.interval_months,
                    )

                date_due = as_of >= (due_date - timedelta(days=rule.lead_days))
                date_expired = as_of > (due_date + timedelta(days=rule.grace_days))

                if date_expired or not date_due:
                    stats["skipped"] += 1 if date_expired else 0
                    continue

                if Reminder.objects.filter(
                    vehicle=vehicle,
                    customer=customer,
                    reminder_type=rule.reminder_type.title,
                    title=rule.title,
                    due_date=due_date,
                ).exists():
                    stats["skipped"] += 1
                    continue

                if self.already_scheduled_for_today(customer.id, as_of):
                    stats["skipped"] += 1
                    continue

                context = self.build_context(
                    customer=customer,
                    vehicle=vehicle,
                    rule=rule,
                    event=event,
                    due_date=due_date,
                    as_of=as_of,
                    prediction=prediction,
                )

                template = rule.template
                if template is not None and template.is_active:
                    message = self.communication.render_template(template, context)
                else:
                    message = (
                        f"{customer.full_name} عزیز، زمان {rule.title} "
                        f"خودروی {vehicle.brand} {vehicle.model} نزدیک شده است."
                    )
                    template = None

                if dry_run:
                    stats["created"] += 1
                    continue

                try:
                    with transaction.atomic():
                        reminder, created = self.create_reminder(
                            customer=customer,
                            vehicle=vehicle,
                            rule=rule,
                            event=event,
                            due_date=due_date,
                            as_of=as_of,
                        )

                        if not created:
                            stats["skipped"] += 1
                            continue

                        stats["created"] += 1
                        send_at = self._send_time(rule=rule, as_of=as_of)

                        queue = self.communication.create_custom_queue(
                            customer=customer,
                            vehicle=vehicle,
                            phone=self.active_phone(customer),
                            title=rule.title,
                            message=message,
                            scheduled_at=send_at,
                        )
                        queue.template = template
                        queue.reminder = reminder
                        queue.save(
                            update_fields=[
                                "template",
                                "reminder",
                                "updated_at",
                            ]
                        )

                        reminder.status = Reminder.STATUS_SCHEDULED
                        reminder.save(update_fields=["status", "updated_at"])
                        stats["queued"] += 1
                except Exception:
                    stats["errors"] += 1

        return stats
