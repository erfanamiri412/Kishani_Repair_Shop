from django.core.management.base import BaseCommand

from reports.services import ReportsService


class Command(BaseCommand):

    help = "بررسی و تولید خودکار گزارش‌های دوره‌های تکمیل‌شده"

    def handle(self, *args, **options):

        reports = ReportsService.generate_scheduled_reports()

        if not reports:

            self.stdout.write(
                self.style.SUCCESS(
                    "گزارش جدیدی برای تولید وجود نداشت."
                )
            )

            return

        for report in reports:

            self.stdout.write(
                self.style.SUCCESS(
                    f"گزارش خودکار آماده شد: {report.title}"
                )
            )
