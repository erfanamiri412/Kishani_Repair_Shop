from django.test import TestCase
from django.utils import timezone

from .models import (
    CommunicationLog,
    CommunicationQueue,
    CommunicationTemplate,
)
from .services import CommunicationService


class CommunicationServiceTests(TestCase):

    def setUp(self):
        self.template = CommunicationTemplate.objects.create(
            title="فاکتور",
            slug="invoice_created",
            template_type="invoice_created",
            channel="sms",
            body=(
                "{{ customer_name }}، فاکتور "
                "{{ invoice_number }} صادر شد."
            ),
        )

        self.service = CommunicationService()

    def test_phone_normalization(self):
        self.assertEqual(
            self.service.normalize_phone(
                "+989123456789"
            ),
            "09123456789",
        )

        self.assertTrue(
            self.service.validate_phone(
                "09123456789"
            )
        )

    def test_template_rendering(self):
        result = self.service.preview_template(
            "invoice_created",
            {
                "customer_name": "احمدی",
                "invoice_number": "INV-TEST",
            },
        )

        self.assertTrue(result["success"])
        self.assertIn("احمدی", result["body"])
        self.assertIn("INV-TEST", result["body"])

    def test_create_queue(self):
        result = self.service.create_queue(
            template_slug="invoice_created",
            phone="09123456789",
            context={
                "customer_name": "احمدی",
                "invoice_number": "INV-TEST",
            },
        )

        self.assertTrue(result["success"])

        queue = result["queue"]

        self.assertEqual(
            queue.recipient_phone,
            "09123456789",
        )

        self.assertEqual(
            queue.status,
            CommunicationQueue.STATUS_PENDING,
        )

    def test_console_send_creates_log(self):
        result = self.service.create_custom_queue(
            phone="09123456789",
            message="پیام تستی",
            scheduled_at=timezone.now(),
        )

        queue = result["queue"]

        send_result = self.service.send_queue(
            queue
        )

        self.assertTrue(send_result["success"])

        queue.refresh_from_db()

        self.assertEqual(
            queue.status,
            CommunicationQueue.STATUS_SENT,
        )

        self.assertEqual(
            CommunicationLog.objects.filter(
                queue=queue
            ).count(),
            1,
        )
