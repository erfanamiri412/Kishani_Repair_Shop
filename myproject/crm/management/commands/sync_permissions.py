from django.core.management.base import BaseCommand

from crm.permissions import PermissionSeeder


class Command(BaseCommand):

    help = "Sync CRM permissions"

    def handle(self, *args, **options):

        PermissionSeeder.sync()

        self.stdout.write(
            self.style.SUCCESS(
                "Permissions synchronized."
            )
        )