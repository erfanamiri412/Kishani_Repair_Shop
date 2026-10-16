from datetime import timedelta

from django.utils import timezone
from crm.constants import (
    CRMEvents,
    CRMAuditActions,
)



# ==========================================================
# Base Builder
# ==========================================================

class BaseBuilder:

    @staticmethod
    def merge_extra_data(
        extra_data=None,
    ):
        """
        تضمین می‌کند extra_data همیشه dict باشد.
        """

        if not extra_data:
            return {}

        if not isinstance(extra_data, dict):
            raise ValueError(
                "extra_data must be a dictionary."
            )

        return extra_data

# ==========================================================
# Shared Service Request Data
# ==========================================================

class ServiceRequestDataBuilder(BaseBuilder):
    """
    اطلاعات مشترک درخواست خدمات
    برای جلوگیری از تکرار در Builderهای مختلف.
    """

    @staticmethod
    def get_vehicle(
        service_request,
    ):
        return getattr(
            service_request,
            "vehicle",
            None,
        )

    @classmethod
    def build_vehicle_data(
        cls,
        service_request,
    ):

        vehicle = cls.get_vehicle(
            service_request
        )

        if not vehicle:
            return {
                "vehicle_id": None,
                "vehicle_brand": "",
                "vehicle_model": "",
                "vehicle_year": (
                    service_request.vehicle_year
                    if hasattr(
                        service_request,
                        "vehicle_year",
                    )
                    else None
                ),
            }

        return {
            "vehicle_id": vehicle.id,

            "vehicle_brand": (
                vehicle.company or ""
            ),

            "vehicle_model": (
                vehicle.model or ""
            ),

            "vehicle_year": (
                service_request.vehicle_year
                if service_request.vehicle_year is not None
                else None
            ),
        }

    @staticmethod
    def build_plate_data(
        service_request,
    ):

        extra_data = (
            service_request.extra_data
            or {}
        )

        return {
            "plate_number": (
                getattr(
                    service_request,
                    "plate_number",
                    None,
                )
                or extra_data.get(
                    "plate_number",
                    "",
                )
            ),

            "plate_city": (
                extra_data.get(
                    "plate_city",
                    "",
                )
            ),

            "plate_letter": (
                extra_data.get(
                    "plate_letter",
                    "",
                )
            ),

            "plate_middle": (
                extra_data.get(
                    "plate_middle",
                    "",
                )
            ),

            "plate_right": (
                extra_data.get(
                    "plate_right",
                    "",
                )
            ),
        }

    @classmethod
    def build_context_data(
        cls,
        service_request,
    ):

        data = {}

        data.update(
            cls.build_vehicle_data(
                service_request
            )
        )

        data.update(
            cls.build_plate_data(
                service_request
            )
        )

        data.update(
            {
                "service_type":
                    service_request.service_type,
            }
        )

        return data
    

# ==========================================================
# Audit Builder
# ==========================================================
class AuditBuilder(
    ServiceRequestDataBuilder
):

    @classmethod
    def build_payload(
        cls,
        *,
        service_request,
        followup=None,
        reminder=None,
    ):
        new_value = cls.build_context_data(
            service_request
        )

        new_value.update(
            {
                "service_request_id": service_request.id,

                "followup_id": (
                    followup.id
                    if followup
                    else None
                ),

                "reminder_id": (
                    reminder.id
                    if reminder
                    else None
                ),
            }
        )

        vehicle = cls.get_vehicle(
            service_request
        )

        if vehicle:
            vehicle_name = (
                f"{vehicle.company or ''} "
                f"{vehicle.model or ''}"
            ).strip()
        else:
            vehicle_name = "بدون خودرو"

        return {
            "customer": service_request.customer,

            "action":
                CRMAuditActions.SERVICE_REQUEST_CREATED,

            "title":
                "ثبت درخواست خدمات",

            "description": (
                "درخواست خدمات برای "
                f"{vehicle_name} "
                "ثبت شد."
            ),

            "old_value": None,

            "new_value": new_value,

            "source":
                service_request.source,

            "is_system": True,
        }     
# ==========================================================
# Timeline Builder
# ==========================================================

class TimelineBuilder(
        ServiceRequestDataBuilder
    ):


        @classmethod
        def build_payload(
            cls,
            *,
            service_request,
            followup=None,
            reminder=None,
            performed_by=None,
        ):

            extra_data = (
                cls.build_context_data(
                    service_request
                )
            )

            extra_data.update(
                {
                    "service_request_id":
                        service_request.id,

                    "followup_id": (
                        followup.id
                        if followup
                        else None
                    ),

                    "reminder_id": (
                        reminder.id
                        if reminder
                        else None
                    ),
                }
            )


            return {

                "entity":
                    "service_request",

                "entity_id":
                    service_request.id,

                "title":
                    "ثبت درخواست خدمات",

                "description":
                    service_request.problem_description,

                "customer_id":
                    service_request.customer_id,

                "performed_by":
                    (
                        performed_by.id
                        if performed_by
                        else None
                    ),

                "extra_data":
                    extra_data,
            }


# ==========================================================
# Notification Builder
# ==========================================================

class NotificationBuilder(
    ServiceRequestDataBuilder
):

    @classmethod
    def build(
        cls,
        *,
        customer,
        service_request,
        followup=None,
        reminder=None,
        performed_by=None,
    ):

        vehicle_data = (
            cls.build_vehicle_data(
                service_request
            )
        )

        plate_data = (
            cls.build_plate_data(
                service_request
            )
        )

        base_payload = {

            "customer_id":
                customer.id,

            "service_request_id":
                service_request.id,

            "vehicle_brand":
                vehicle_data.get(
                    "vehicle_brand",
                    "",
                ),

            "vehicle_model":
                vehicle_data.get(
                    "vehicle_model",
                    "",
                ),

            "vehicle_year":
                vehicle_data.get(
                    "vehicle_year"
                ),

            "service_type":
                service_request.service_type,

            "plate_number":
                plate_data.get(
                    "plate_number",
                    "",
                ),
        }

        notifications = [

            {
                "payload":
                    base_payload,
            }
        ]

        if followup:

            notifications.append(
                {
                    "event":
                        CRMEvents.FOLLOWUP_CREATED,


                    "payload": {
                        **base_payload,

                        "followup_id":
                            followup.id,
                    },
                }
            )

        if reminder:

            notifications.append(
                {
                    "event":
                        CRMEvents.REMINDER_CREATED,

                    "payload": {
                        **base_payload,

                        "reminder_id":
                            reminder.id,
                    },
                }
            )

        return notifications

# ==========================================================
# Reminder Builder
# ==========================================================

class ReminderBuilder(
    ServiceRequestDataBuilder
):

    @classmethod
    def build_payload(
        cls,
        *,
        service_request,
        followup=None,
        performed_by=None,
    ):

        return {

            "customer":
                service_request.customer,

            "followup":
                followup,

            "title":
                cls.build_title(
                    service_request
                ),

            "description":
                cls.build_description(
                    service_request
                ),

            "remind_at":
                cls.build_remind_at(
                    service_request
                ),

            "priority":
                service_request.priority,

            "is_sent":
                False,

            "auto_created":
                True,

            "send_sms":
                True,

            "send_notification":
                True,

            "repeatable":
                False,

            "repeat_days":
                0,
        }

    @staticmethod
    def build_title(
        service_request,
    ):

        vehicle = (
            ServiceRequestDataBuilder
            .get_vehicle(
                service_request
            )
        )

        if not vehicle:
            return "پیگیری درخواست خدمات"

        return (
            "پیگیری درخواست خدمات | "
            f"{vehicle.company or ''} "
            f"{vehicle.model or ''}"
        ).strip()

    @staticmethod
    def build_description(
        service_request,
    ):

        return (
            service_request
            .problem_description
            or ""
        )


    @staticmethod
    def build_remind_at(
        service_request,
    ):

        return (
            timezone.now()
            + timedelta(days=1)
        )