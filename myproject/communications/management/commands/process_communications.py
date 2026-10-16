from django.core.management.base import BaseCommand

from communications.services import CommunicationService


class Command(BaseCommand):
    help = "پردازش صف پیامک‌های آماده ارسال"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
        )

    def handle(self, *args, **options):
        result = CommunicationService().send_pending_messages(
            limit=options["limit"]
        )

        self.stdout.write(
            self.style.SUCCESS(
                "پردازش صف پیامک انجام شد: "
                f"کل={result['total']}، "
                f"موفق={result['success_count']}، "
                f"ناموفق={result['failed_count']}، "
                f"منتظر بازه مجاز={result['skipped_count']}"
            )
        )
