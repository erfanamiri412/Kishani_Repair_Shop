from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from django.db import models, transaction
from django.template import Context, Template, TemplateSyntaxError
from django.utils import timezone

from crm.models import Customer

from communications.models import (
    CommunicationLog,
    CommunicationQueue,
    CommunicationTemplate,
    Reminder,
    SmsCampaign,
    SmsCampaignRecipient,
)
from communications.sms import SMSFactory


class CommunicationService:
    """هسته‌ی ساده‌ی پیامک: قالب، صف، ارسال و سابقه."""

    def __init__(self, sms_provider=None):
        self.sms_provider = sms_provider or SMSFactory.get_provider()

    @staticmethod
    def now():
        return timezone.now()

    @staticmethod
    def normalize_phone(phone: str | None) -> str:
        if not phone:
            return ""

        value = str(phone).strip()
        translation = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )
        value = value.translate(translation)
        value = re.sub(r"[\s\-()]+", "", value)

        if value.startswith("+98"):
            value = "0" + value[3:]
        elif value.startswith("98"):
            value = "0" + value[2:]

        return value

    @classmethod
    def validate_phone(cls, phone: str | None) -> bool:
        return bool(
            re.fullmatch(
                r"09\d{9}",
                cls.normalize_phone(phone),
            )
        )

    @staticmethod
    def validate_message(message: str | None) -> bool:
        return bool(message and message.strip())

    # ---------------------------------------------------------
    # Template
    # ---------------------------------------------------------

    def get_template(self, slug: str) -> CommunicationTemplate | None:
        return (
            CommunicationTemplate.objects
            .filter(
                slug=slug,
                is_active=True,
                channel="sms",
            )
            .first()
        )

    @staticmethod
    def render_template(
        template_obj: CommunicationTemplate,
        context: dict[str, Any],
    ) -> str:
        try:
            return Template(template_obj.body).render(
                Context(context)
            ).strip()
        except TemplateSyntaxError as exc:
            raise ValueError(
                f"ساختار قالب پیامک نامعتبر است: {exc}"
            ) from exc

    # ---------------------------------------------------------
    # Automatic send window
    # ---------------------------------------------------------

    @staticmethod
    def _automatic_rule_for_queue(queue: CommunicationQueue):
        if not queue.reminder_id:
            return None

        from maintenance.models import MaintenanceRule

        reminder = queue.reminder
        if not reminder.title or not reminder.reminder_type:
            return False

        rule = (
            MaintenanceRule.objects
            .filter(
                title=reminder.title,
                reminder_type__title=reminder.reminder_type,
            )
            .select_related("reminder_type")
            .first()
        )

        return rule or False

    @classmethod
    def _next_allowed_automatic_time(cls, rule, now=None):
        now = now or timezone.now()
        current = timezone.localtime(now)
        start = rule.send_window_start
        end = rule.send_window_end

        current_time = current.time()

        if start <= current_time <= end:
            return now

        if current_time < start:
            target_date = current.date()
        else:
            target_date = current.date() + timedelta(days=1)

        naive = datetime.combine(target_date, start)
        return timezone.make_aware(
            naive,
            timezone.get_current_timezone(),
        )

    @classmethod
    def _prepare_automatic_queue(cls, queue: CommunicationQueue, now=None):
        rule = cls._automatic_rule_for_queue(queue)
        if rule is None:
            return True
        if rule is False or not rule.is_active or not rule.automatic:
            queue.status = CommunicationQueue.STATUS_CANCELLED
            queue.last_error = "قاعده هوشمند مرتبط دیگر فعال نیست."
            queue.save(update_fields=["status", "last_error", "updated_at"])
            if queue.reminder_id:
                reminder = queue.reminder
                reminder.status = Reminder.STATUS_CANCELLED
                reminder.save(update_fields=["status", "updated_at"])
            return False

        now = now or timezone.now()
        current = timezone.localtime(now)
        start = rule.send_window_start
        end = rule.send_window_end

        if start <= current.time() <= end:
            return True

        next_time = cls._next_allowed_automatic_time(rule, now=now)
        if queue.scheduled_at != next_time or queue.status != CommunicationQueue.STATUS_PENDING:
            queue.scheduled_at = next_time
            queue.status = CommunicationQueue.STATUS_PENDING
            queue.save(
                update_fields=[
                    "scheduled_at",
                    "status",
                    "updated_at",
                ]
            )
        return False

    # ---------------------------------------------------------
    # Queue
    # ---------------------------------------------------------

    def create_custom_queue(
        self,
        *,
        customer=None,
        vehicle=None,
        phone: str,
        message: str,
        title: str = "",
        priority: int = 3,
        scheduled_at=None,
        max_retry: int = 3,
    ):
        phone = self.normalize_phone(phone)

        if not self.validate_phone(phone):
            raise ValueError("شماره موبایل معتبر نیست.")

        if not self.validate_message(message):
            raise ValueError("متن پیامک خالی است.")

        scheduled_at = scheduled_at or self.now()
        recipient_name = getattr(customer, "full_name", "") or ""

        return CommunicationQueue.objects.create(
            customer=customer,
            vehicle=vehicle,
            channel="sms",
            recipient_name=recipient_name,
            recipient_phone=phone,
            subject=title,
            body=message.strip(),
            priority=max(1, min(priority, 5)),
            max_retry=max(0, max_retry),
            scheduled_at=scheduled_at,
        )

    def cancel_queue(self, queue: CommunicationQueue):
        if queue.status not in {
            CommunicationQueue.STATUS_PENDING,
            CommunicationQueue.STATUS_FAILED,
        }:
            raise ValueError("این پیام در وضعیت قابل لغو نیست.")

        queue.status = CommunicationQueue.STATUS_CANCELLED
        queue.last_error = "به‌صورت دستی لغو شد."
        queue.save(update_fields=["status", "last_error", "updated_at"])

        if queue.reminder_id:
            reminder = queue.reminder
            reminder.status = Reminder.STATUS_CANCELLED
            reminder.save(update_fields=["status", "updated_at"])

        return queue

    # ---------------------------------------------------------
    # Sending
    # ---------------------------------------------------------

    @transaction.atomic
    def send_queue(self, queue: CommunicationQueue):
        if queue.status not in {
            CommunicationQueue.STATUS_PENDING,
            CommunicationQueue.STATUS_FAILED,
        }:
            raise ValueError("این پیام قابل ارسال نیست.")

        now = self.now()

        automatic_rule = self._automatic_rule_for_queue(queue)
        if queue.reminder_id:
            if automatic_rule is False or automatic_rule is None:
                self._prepare_automatic_queue(queue, now=now)
                return False
            if not self._prepare_automatic_queue(queue, now=now):
                return False

        if queue.scheduled_at > now:
            raise ValueError("زمان ارسال این پیام هنوز نرسیده است.")

        if not self.validate_phone(queue.recipient_phone):
            raise ValueError("شماره موبایل گیرنده معتبر نیست.")

        queue.status = CommunicationQueue.STATUS_PROCESSING
        queue.last_attempt_at = now
        queue.retry_count += 1
        queue.save(
            update_fields=[
                "status",
                "last_attempt_at",
                "retry_count",
                "updated_at",
            ]
        )

        try:
            provider_result = self.sms_provider.send(
                phone=queue.recipient_phone,
                message=queue.body,
            ) or {}

            success = bool(provider_result.get("success"))
            sent_at = self.now() if success else None

            queue.provider = provider_result.get("provider", "") or ""
            queue.provider_message_id = provider_result.get("message_id", "") or ""

            if success:
                queue.status = CommunicationQueue.STATUS_SENT
                queue.sent_at = sent_at
                queue.last_error = ""

                if queue.reminder_id:
                    reminder = queue.reminder
                    reminder.status = Reminder.STATUS_SENT
                    reminder.sent_at = sent_at
                    reminder.save(
                        update_fields=["status", "sent_at", "updated_at"]
                    )
            else:
                queue.status = CommunicationQueue.STATUS_FAILED
                queue.last_error = provider_result.get(
                    "error",
                    "خطای نامشخص در ارسال پیامک.",
                )

            queue.save()

            self.create_log(
                queue=queue,
                provider_result=provider_result,
                success=success,
                attempted_at=now,
                sent_at=sent_at,
            )

            return success

        except Exception as exc:
            queue.status = CommunicationQueue.STATUS_FAILED
            queue.last_error = str(exc)
            queue.save(
                update_fields=[
                    "status",
                    "last_error",
                    "updated_at",
                ]
            )

            self.create_log(
                queue=queue,
                provider_result={
                    "provider": "",
                    "message_id": "",
                    "status": "exception",
                    "error": str(exc),
                },
                success=False,
                attempted_at=now,
            )

            return False

    def send_pending_messages(self, limit: int = 50):
        from django.db.models import Q

        now = self.now()

        queues = list(
            CommunicationQueue.objects
            .select_related("reminder")
            .filter(
                Q(
                    status=CommunicationQueue.STATUS_PENDING,
                    scheduled_at__lte=now,
                )
                | Q(
                    status=CommunicationQueue.STATUS_FAILED,
                    retry_count__lt=models.F("max_retry"),
                    scheduled_at__lte=now,
                )
            )
            .order_by(
                "priority",
                "scheduled_at",
                "id",
            )[:limit]
        )

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for queue in queues:
            automatic_rule = self._automatic_rule_for_queue(queue)
            if queue.reminder_id:
                if automatic_rule is False or automatic_rule is None:
                    self._prepare_automatic_queue(queue, now=now)
                    skipped_count += 1
                    continue
                if not self._prepare_automatic_queue(queue, now=now):
                    skipped_count += 1
                    continue

            if self.send_queue(queue):
                success_count += 1
            else:
                failed_count += 1

        return {
            "total": len(queues),
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
        }

    # ---------------------------------------------------------
    # Logs
    # ---------------------------------------------------------

    def create_log(
        self,
        *,
        queue: CommunicationQueue,
        provider_result: dict[str, Any],
        success: bool,
        attempted_at,
        sent_at=None,
    ):
        return CommunicationLog.objects.create(
            queue=queue,
            customer=queue.customer,
            vehicle=queue.vehicle,
            template=queue.template,
            channel="sms",
            recipient=queue.recipient_phone,
            message=queue.body,
            provider=provider_result.get("provider", "") or "",
            provider_message_id=provider_result.get("message_id", "") or "",
            provider_status=provider_result.get("status", "") or "",
            status=(
                CommunicationLog.STATUS_SUCCESS
                if success
                else CommunicationLog.STATUS_FAILED
            ),
            error_message=provider_result.get("error", "") or "",
            attempted_at=attempted_at,
            sent_at=sent_at,
        )


class SmsCampaignService:
    """مدیریت ارسال دستی پیامک به یک یا چند مشتری."""

    def __init__(self, communication_service=None):
        self.sms = communication_service or CommunicationService()

    @staticmethod
    def _customers_for_campaign(campaign: SmsCampaign):
        if campaign.target_type == SmsCampaign.TARGET_ALL:
            return Customer.objects.all()

        if campaign.target_type == SmsCampaign.TARGET_SINGLE:
            return (
                Customer.objects.filter(pk=campaign.customer_id)
                if campaign.customer_id
                else Customer.objects.none()
            )

        return campaign.selected_customers.all()

    @transaction.atomic
    def prepare(self, campaign: SmsCampaign):
        if campaign.status in {
            SmsCampaign.STATUS_SENDING,
            SmsCampaign.STATUS_COMPLETED,
            SmsCampaign.STATUS_FAILED,
        }:
            raise ValueError("این ارسال قبلاً اجرا شده و قابل آماده‌سازی مجدد نیست.")

        if not self.sms.validate_message(campaign.body):
            raise ValueError("متن پیامک خالی است.")

        # در حالت پیش‌نویس، گیرندگان قبلی را دوباره‌سازی می‌کنیم.
        if campaign.status == SmsCampaign.STATUS_DRAFT:
            campaign.recipients.all().delete()

        recipients = []
        seen_customers = set()

        for customer in self._customers_for_campaign(campaign).iterator():
            if customer.id in seen_customers:
                continue

            phone = self.sms.normalize_phone(customer.mobile)
            if not self.sms.validate_phone(phone):
                continue

            seen_customers.add(customer.id)
            recipient, _ = SmsCampaignRecipient.objects.get_or_create(
                campaign=campaign,
                customer=customer,
                defaults={
                    "phone": phone,
                },
            )

            if recipient.phone != phone:
                recipient.phone = phone
                recipient.save(update_fields=["phone"])

            recipients.append(recipient)

        if not recipients:
            raise ValueError("هیچ گیرنده دارای شماره موبایل معتبر پیدا نشد.")

        campaign.total_recipients = len(recipients)
        campaign.sent_count = 0
        campaign.failed_count = 0
        campaign.status = SmsCampaign.STATUS_READY
        campaign.save(
            update_fields=[
                "total_recipients",
                "sent_count",
                "failed_count",
                "status",
                "updated_at",
            ]
        )

        return recipients

    @transaction.atomic
    def enqueue(self, campaign: SmsCampaign):
        recipients = list(
            campaign.recipients
            .filter(status=SmsCampaignRecipient.STATUS_PENDING)
            .select_related("customer", "queue")
        )

        scheduled_at = campaign.scheduled_at or timezone.now()
        created = 0

        for recipient in recipients:
            if recipient.queue_id:
                continue

            queue = self.sms.create_custom_queue(
                customer=recipient.customer,
                phone=recipient.phone,
                title=campaign.title,
                message=campaign.body,
                scheduled_at=scheduled_at,
            )

            recipient.queue = queue
            recipient.save(update_fields=["queue"])
            created += 1

        campaign.status = SmsCampaign.STATUS_READY
        campaign.save(update_fields=["status", "updated_at"])

        return created

    @transaction.atomic
    def send_campaign(self, campaign: SmsCampaign):
        self.prepare(campaign)
        self.enqueue(campaign)

        scheduled_at = campaign.scheduled_at or timezone.now()
        if scheduled_at > timezone.now():
            return {
                "scheduled": True,
                "total": campaign.total_recipients,
                "success_count": 0,
                "failed_count": 0,
            }

        campaign.status = SmsCampaign.STATUS_SENDING
        campaign.save(update_fields=["status", "updated_at"])

        successful = 0
        failed = 0

        for recipient in campaign.recipients.select_related("queue").filter(
            status=SmsCampaignRecipient.STATUS_PENDING,
        ):
            if not recipient.queue_id:
                continue

            ok = self.sms.send_queue(recipient.queue)
            if ok:
                recipient.status = SmsCampaignRecipient.STATUS_SENT
                recipient.sent_at = recipient.queue.sent_at
                successful += 1
            else:
                recipient.status = SmsCampaignRecipient.STATUS_FAILED
                recipient.error_message = recipient.queue.last_error
                failed += 1

            recipient.save(
                update_fields=[
                    "status",
                    "sent_at",
                    "error_message",
                ]
            )

        campaign.sent_count = campaign.recipients.filter(
            status=SmsCampaignRecipient.STATUS_SENT
        ).count()
        campaign.failed_count = campaign.recipients.filter(
            status=SmsCampaignRecipient.STATUS_FAILED
        ).count()

        if campaign.sent_count == campaign.total_recipients:
            campaign.status = SmsCampaign.STATUS_COMPLETED
        elif campaign.failed_count:
            campaign.status = SmsCampaign.STATUS_FAILED
        else:
            campaign.status = SmsCampaign.STATUS_READY

        campaign.save(
            update_fields=[
                "sent_count",
                "failed_count",
                "status",
                "updated_at",
            ]
        )

        return {
            "scheduled": False,
            "total": campaign.total_recipients,
            "success_count": successful,
            "failed_count": failed,
        }
