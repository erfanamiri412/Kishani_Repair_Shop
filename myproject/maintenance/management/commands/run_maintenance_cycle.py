from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from communications.services import CommunicationService
from maintenance.services import MaintenanceEngine


class Command(BaseCommand):
    help = "اجرای چرخه روزانه هوشمندی سرویس و پردازش صف پیامک"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="فقط تحلیل؛ بدون ساخت یادآوری و صف پیام",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
        )
        parser.add_argument(
            "--as-of",
            help="تاریخ تحلیل به فرمت YYYY-MM-DD برای تست",
        )

    def handle(self, *args, **options):
        engine = MaintenanceEngine()
        as_of = None
        if options["as_of"]:
            try:
                as_of = datetime.strptime(
                    options["as_of"],
                    "%Y-%m-%d",
                ).date()
            except ValueError as exc:
                raise CommandError(
                    "--as-of باید با فرمت YYYY-MM-DD باشد."
                ) from exc

        evaluation = engine.evaluate(
            as_of=as_of,
            dry_run=options["dry_run"],
        )

        if options["dry_run"]:
            sending = {
                "total": 0,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
            }
        else:
            sending = CommunicationService().send_pending_messages(
                limit=options["limit"],
            )

        self.stdout.write(
            self.style.SUCCESS(
                "چرخه نگهداری اجرا شد: "
                f"خودرو={evaluation['vehicles']} | "
                f"تطبیق={evaluation['matched']} | "
                f"یادآوری جدید={evaluation['created']} | "
                f"صف={evaluation['queued']} | "
                f"خطا={evaluation['errors']} | "
                f"ارسال موفق={sending['success_count']} | "
                f"ارسال ناموفق={sending['failed_count']} | "
                f"منتظر بازه مجاز={sending['skipped_count']}"
            )
        )
