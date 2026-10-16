from django.db.models.signals import post_save
from django.dispatch import receiver
from crm.models import (
    Repair,
    Invoice,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from users.models import EmployeeProfile


@receiver(
    post_save,
    sender=EmployeeProfile,
)
def assign_role_group(
    sender,
    instance,
    created,
    **kwargs,
):
    role_map = {
        "manager": "مدیر",
        "mechanic": "مکانیک",
    }

    group_name = role_map.get(instance.role)

    if not group_name:
        return

    try:
        group = Group.objects.get(
            name=group_name
        )

    except Group.DoesNotExist:
        return

    user = instance.user

    user.groups.clear()

    user.groups.add(group)
    
@receiver(
    post_save,
    sender=Repair,
)
def create_invoice_for_repair(

    sender,

    instance,

    created,

    **kwargs,

):

    if not created:

        return

    Invoice.objects.get_or_create(

        repair=instance,

    )

