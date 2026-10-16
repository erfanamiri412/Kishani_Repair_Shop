from django.core.management.base import BaseCommand

from maintenance.services import MaintenanceRuleSeedService


class Command(BaseCommand):
    help = "ساخت/به‌روزرسانی انواع یادآوری، قالب‌ها و قواعد پیش‌فرض سرویس هوشمند"

    def handle(self, *args, **options):
        result = MaintenanceRuleSeedService.seed()
        self.stdout.write(
            self.style.SUCCESS(
                "راه‌اندازی سرویس هوشمند انجام شد: "
                f"قواعد جدید={result['created']}، "
                f"قواعد بروزشده={result['updated']}، "
                f"انواع یادآوری={result['reminder_types']}، "
                f"قالب‌ها={result['templates']}"
            )
        )
