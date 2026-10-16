from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import MaintenanceReminderType, MaintenanceRule
from .services import MaintenanceEngine, ServiceEvent


class MaintenanceEngineLogicTests(TestCase):

    def setUp(self):
        self.reminder_type = MaintenanceReminderType.objects.create(
            title="نوع تست",
            order=1,
            is_active=True,
        )

    def test_add_months_handles_end_of_month(self):
        self.assertEqual(
            MaintenanceEngine.add_months(date(2026, 1, 31), 1),
            date(2026, 2, 28),
        )

    def test_rule_matches_only_keywords(self):
        rule = MaintenanceRule(
            title="تست",
            reminder_type=self.reminder_type,
            keywords=["تعویض روغن"],
            interval_months=6,
        )
        event = ServiceEvent(
            event_date=date(2026, 1, 1),
            text="تعویض روغن موتور",
        )
        self.assertTrue(MaintenanceEngine.event_matches(rule, event))

    def test_non_keyword_text_does_not_match(self):
        rule = MaintenanceRule(
            title="تست",
            reminder_type=self.reminder_type,
            keywords=["تعویض روغن"],
            interval_months=6,
        )
        event = ServiceEvent(
            event_date=date(2026, 1, 1),
            text="تعویض لنت ترمز",
        )
        self.assertFalse(MaintenanceEngine.event_matches(rule, event))

    def test_wildcard_keyword_matches_every_event(self):
        rule = MaintenanceRule(
            title="تست",
            reminder_type=self.reminder_type,
            keywords=["*"],
            interval_months=12,
        )
        event = ServiceEvent(
            event_date=date(2026, 1, 1),
            text="بازدید خودرو",
        )
        self.assertTrue(MaintenanceEngine.event_matches(rule, event))

    def test_empty_keywords_are_invalid(self):
        rule = MaintenanceRule(
            title="تست",
            reminder_type=self.reminder_type,
            keywords=[],
            interval_months=6,
        )
        with self.assertRaises(ValidationError):
            rule.full_clean()
