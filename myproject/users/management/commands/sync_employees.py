from django.core.management.base import BaseCommand

from users.models import EmployeeProfile


class Command(BaseCommand):

    help = "Create missing employee profiles"

    def handle(self, *args, **kwargs):

        before = EmployeeProfile.objects.count()

        EmployeeProfile.sync_profiles()

        after = EmployeeProfile.objects.count()

        self.stdout.write(

            self.style.SUCCESS(

                f"Employee profiles synced. {before} -> {after}"

            )

        )