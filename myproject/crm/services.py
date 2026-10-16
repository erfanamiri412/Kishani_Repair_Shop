"""
CRM Business Services

تمام منطق تجاری CRM
در این فایل قرار می‌گیرد.
"""

from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from crm.builders import ReminderBuilder, NotificationBuilder, TimelineBuilder, AuditBuilder
from .models import (
    CustomerVehicle,
    CustomerAudit,
)
from .constants import CRMEvents

from crm.models import (
    Customer,
    CustomerServiceRequest,
)

from dataclasses import dataclass, field

@dataclass
class CRMContext:

    # ----------------------------
    # Main Objects
    # ----------------------------

    customer: Customer | None = None

    service_request: CustomerServiceRequest | None = None

    timeline = None

    audit = None

    transition = None


    # ----------------------------
    # Actor
    # ----------------------------

    performed_by: object | None = None


    # ----------------------------
    # Runtime
    # ----------------------------

    notifications: list = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )

    flags: dict = field(
        default_factory=dict
    )
    
class CRMService:

    @classmethod
    @transaction.atomic
    def register_service_request(
        cls,
        *,
        context=None,
        service_request,
        performed_by=None,
    ):
        context = CRMContext(
            customer=service_request.customer,
            service_request=service_request,
            performed_by=performed_by,
        )

        context.followup = cls._create_service_request_followup(
            service_request=service_request,
            performed_by=performed_by,
        )

        context.reminder = cls._create_service_request_reminder(
            service_request=service_request,
            followup=context.followup,
            performed_by=performed_by,
        )

        context.audit = cls._create_service_request_audit(
            service_request=service_request,
            followup=context.followup,
            reminder=context.reminder,
            performed_by=performed_by,
        )

        context.notifications = cls._create_service_request_notifications(
            service_request=service_request,
            followup=context.followup,
            reminder=context.reminder,
        )

        return context

    @classmethod
    def _create_service_request_timeline(
        cls,
        *,
        service_request,
        followup=None,
        reminder=None,
        performed_by=None,
    ):

        payload = (
            TimelineBuilder.build_payload(
                service_request=service_request,
                followup=followup,
                reminder=reminder,
                performed_by=performed_by,
            )
        )

        return payload

    @classmethod
    def _create_service_request_audit(
        cls,
        *,
        service_request,
        followup=None,
        reminder=None,
        performed_by=None,
    ):
        payload = AuditBuilder.build_payload(
            service_request=service_request,
            followup=followup,
            reminder=reminder,
            performed_by=performed_by,
        )

        return CustomerAudit.objects.create(
            **payload
        )

    @classmethod
    def _create_service_request_notifications(
        cls,
        *,
        service_request,
        followup=None,
        reminder=None,
    ):

        return NotificationBuilder.build(
            customer=service_request.customer,
            service_request=service_request,
            followup=followup,
            reminder=reminder,
            performed_by=None,
        )

    @classmethod
    def _run_service_request_automation(
        cls,
        *,
        service_request,
        followup=None,
        reminder=None,
    ):

        events = [

            {

                "customer_id":
                    service_request.customer_id,

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

        ]


        if followup:

            events.append(
                {
                    "event":
                        CRMEvents.FOLLOWUP_CREATED,

                    "customer_id":
                        service_request.customer_id,

                    "followup_id":
                        followup.id,
                }
            )


        if reminder:

            events.append(
                {
                    "event":
                        CRMEvents.REMINDER_CREATED,

                    "customer_id":
                        service_request.customer_id,

                    "reminder_id":
                        reminder.id,
                }
            )


        return events

class CustomerResolver:

    @classmethod
    def resolve(
        cls,
        *,
        validated_data,
    ):

        mobile = cls._normalize_mobile(
            validated_data["phone"]
        )

        customer = cls._find_customer(
            mobile=mobile
        )

        if customer:

            cls._update_customer(
                customer=customer,
                validated_data=validated_data,
            )

            return customer

        return cls._create_customer(
            validated_data=validated_data,
            mobile=mobile,
        )

    # -----------------------------------------------------
    # Normalize Mobile
    # -----------------------------------------------------

    @staticmethod
    def _normalize_mobile(
        mobile,
    ):

        mobile = str(mobile).strip()

        # Persian / Arabic digits -> English
        mobile = (
            mobile
            .translate(
                str.maketrans(
                    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
                    "01234567890123456789",
                )
            )
        )

        mobile = (
            mobile
            .replace(" ", "")
            .replace("-", "")
        )

        if mobile.startswith("+98"):

            mobile = (
                "0"
                + mobile[3:]
            )

        elif mobile.startswith("98"):

            mobile = (
                "0"
                + mobile[2:]
            )

        elif mobile.startswith("9"):

            mobile = (
                "0"
                + mobile
            )

        return mobile

    # -----------------------------------------------------
    # Find
    # -----------------------------------------------------

    @staticmethod
    def _find_customer(
        *,
        mobile,
    ):

        return (
            Customer.objects
            .filter(
                mobile=mobile
            )
            .first()
        )

    # -----------------------------------------------------
    # Update
    # -----------------------------------------------------

    @staticmethod
    def _update_customer(
        *,
        customer,
        validated_data,
    ):

        full_name = (
            validated_data.get(
                "full_name"
            )
            or ""
        ).strip()

        if (
            full_name
            and
            customer.full_name != full_name
        ):

            customer.full_name = full_name

            customer.save(
                update_fields=[
                    "full_name"
                ]
            )

    # -----------------------------------------------------
    # Create
    # -----------------------------------------------------

    @staticmethod
    def _create_customer(
        *,
        validated_data,
        mobile,
    ):

        return Customer.objects.create(
            full_name=(
                validated_data[
                    "full_name"
                ].strip()
            ),
            mobile=mobile,
        )

class ServiceRequestCreator:

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        customer,
        validated_data,
        performed_by=None,
    ):
        vehicle = cls._get_or_create_vehicle(
            customer=customer,
            validated_data=validated_data,
        )

        payload = cls._build_payload(
            customer=customer,
            vehicle=vehicle,
            validated_data=validated_data,
            performed_by=performed_by,
        )

        return CustomerServiceRequest.objects.create(
            **payload
        )

    # =====================================================
    # Customer Vehicle
    # =====================================================

    @classmethod
    def _get_or_create_vehicle(
        cls,
        *,
        customer,
        validated_data,
    ):

        plate_number = (
            validated_data.get(
                "plate_number"
            )
            or ""
        ).strip()

        brand = (
            validated_data.get(
                "vehicle_brand"
            )
            or ""
        ).strip()

        vehicle_model = (
            validated_data.get(
                "vehicle_model"
            )
            or ""
        ).strip()

        # -------------------------------------------------
        # جستجوی خودرو با پلاک
        # -------------------------------------------------

        vehicle = None

        if plate_number:

            vehicle = (
                CustomerVehicle.objects
                .filter(
                    customer=customer,
                    plate_number=plate_number,
                )
                .first()
            )

        # -------------------------------------------------
        # خودرو موجود است
        # -------------------------------------------------

        if vehicle:

            changed_fields = []

            if (
                brand
                and vehicle.company != brand
            ):
                vehicle.company = brand

                changed_fields.append(
                    "company"
                )

            if (
                vehicle_model
                and vehicle.model != vehicle_model
            ):
                vehicle.model = vehicle_model

                changed_fields.append(
                    "model"
                )

            if changed_fields:

                vehicle.save(
                    update_fields=changed_fields
                )

            return vehicle

        # -------------------------------------------------
        # خودرو جدید
        # -------------------------------------------------

        return CustomerVehicle.objects.create(

            customer=customer,

            plate_number=plate_number,

            brand=vehicle_model,

            company=brand,

            model=vehicle_model,

        )

    # =====================================================
    # Service Request Payload
    # =====================================================

    @staticmethod
    def _build_payload(
        *,
        customer,
        vehicle,
        validated_data,
        performed_by,
    ):

        return {

            "customer":
                customer,

            "service_type":
                validated_data[
                    "service_type"
                ],

            "vehicle":
                vehicle,

            "vehicle_year":
                validated_data.get(
                    "vehicle_year"
                ),

            "problem_description":
                validated_data[
                    "problem_description"
                ],

            "plate_number":
                validated_data.get(
                    "plate_number",
                    "",
                ),

            "extra_data":
                ServiceRequestCreator
                ._build_extra_data(
                    validated_data
                ),

            "created_by":
                performed_by,
        }

    # =====================================================
    # Extra Data
    # =====================================================

    @staticmethod
    def _build_extra_data(
        validated_data,
    ):

        return {

            "plate_city":
                validated_data.get(
                    "plate_city",
                    "",
                ),

            "plate_letter":
                validated_data.get(
                    "plate_letter",
                    "",
                ),

            "plate_middle":
                validated_data.get(
                    "plate_middle",
                    "",
                ),

            "plate_right":
                validated_data.get(
                    "plate_right",
                    "",
                ),

            "notify_whatsapp":
                validated_data.get(
                    "notify_whatsapp",
                    False,
                ),

            "whatsapp":
                validated_data.get(
                    "whatsapp"
                ),

            "client_ip":
                validated_data.get(
                    "client_ip"
                ),

            "user_agent":
                validated_data.get(
                    "user_agent"
                ),
        }
       
class CRMConnector:

    @staticmethod
    def attach(
        *,
        service_request,
        performed_by=None,
    ):

        return (
            CRMService
            .register_service_request(
                service_request=service_request,
                performed_by=performed_by,
            )
        )
        
class NotificationDispatcher:

    @classmethod
    def dispatch(
        cls,
        *,
        context,
    ):

        for notification in context.notifications:

            cls._dispatch_notification(
                notification=notification,
            )

    @classmethod
    def _dispatch_notification(
            cls,
            *,
            notification,
        ):

            event = notification["event"]

            payload = notification["payload"]

            priority = notification["priority"]

            # فعلاً فقط Log

            print(

                f"[{priority}] "

                f"{event} "

                f"{payload}"

            )

class AutomationEngine:

    @classmethod
    def run(
        cls,
        *,
        context,
    ):

        cls._handle_followup(
            context=context,
        )

        cls._handle_reminder(
            context=context,
        )

        cls._handle_notification(
            context=context,
        )

    @classmethod
    def _handle_followup(
        cls,
        *,
        context,
    ):

        transition = context.transition

        if not transition:
            return

        if not transition.create_followup:
            return

        followup = CRMService._create_followup(
            context=context,
        )

        context.followup = followup
            
    @classmethod
    def _handle_reminder(
        cls,
        *,
        context,
    ):

        transition = context.transition

        if not transition:
            return

        if not transition.auto_transition:
            return

        reminder = CRMService._create_reminder(
            context=context,
        )

        context.reminder = reminder

    @classmethod
    def _handle_notification(
        cls,
        *,
        context,
    ):

        transition = context.transition

        if not transition:
            return

        if transition.send_sms:

            NotificationDispatcher.dispatch(
                context=context,
            )

class CustomerServiceRequestService:

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        validated_data,
        performed_by=None,
    ):

        customer = CustomerResolver.resolve(
            validated_data=validated_data,
        )

        service_request = ServiceRequestCreator.create(
            customer=customer,
            validated_data=validated_data,
            performed_by=performed_by,
        )

        print(
            "======================================"
        )

        print(
            "SERVICE REQUEST CREATED:",
            service_request.pk,
        )

        try:

            CRMConnector.attach(
                service_request=service_request,
                performed_by=performed_by,
            )

            print(
                "CRM CONNECTOR: SUCCESS"
            )

        except Exception as exc:

            print(
                "CRM CONNECTOR ERROR:",
                type(exc).__name__,
                str(exc),
            )

            raise

        print(
            "======================================"
        )

        return service_request