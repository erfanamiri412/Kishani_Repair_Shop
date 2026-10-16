from django.contrib import admin, messages
from django.utils.html import format_html
from core.admin import BaseModelAdmin
from crm.admin import CustomerServiceRequestAdminForm
from crm.models import (
    CustomerServiceRequest,
    Repair,
)
from django.utils.html import format_html
from crm.admin import format_plate_admin

@admin.register(CustomerServiceRequest)
class CustomerServiceRequestAdmin(
    BaseModelAdmin,
):

    form = CustomerServiceRequestAdminForm
            
    list_display = (
        "customer_name_display",
        "customer_phone_display",
        "vehicle_brand_display",
        "vehicle_model_display",
        "vehicle_year_display",
        "vehicle_plate_display",
        "service_type_display",
        "created_at",
    )

    list_display_links = ("customer_name_display",)


    @admin.display(description="نام و نام خانوادگی", ordering="customer__full_name")
    def customer_name_display(self, obj):
        return obj.customer.full_name if obj.customer else "-"


    @admin.display(description="شماره تماس")
    def customer_phone_display(self, obj):
        if not obj.customer:
            return "-"

        return obj.customer.mobile or obj.customer.phone or "-"


    @admin.display(description="برند خودرو", ordering="vehicle__company")
    def vehicle_brand_display(self, obj):
        return obj.vehicle.company or "-" if obj.vehicle else "-"


    @admin.display(description="مدل خودرو", ordering="vehicle__brand")
    def vehicle_model_display(self, obj):
        return obj.vehicle.brand or "-" if obj.vehicle else "-"


    @admin.display(description="سال ساخت", ordering="vehicle__model")
    def vehicle_year_display(self, obj):
        return obj.vehicle.model or "-" if obj.vehicle else "-"


    @admin.display(description="شماره پلاک")
    def vehicle_plate_display(self, obj):
        if not obj.vehicle:
            return "-"

        return obj.vehicle.formatted_plate or obj.vehicle.plate_number or "-"

    list_filter = (

        "service_type",

        "created_at",

    )

    search_fields = (

        "customer__full_name",

        "customer__mobile",

        "customer__phone",

        "vehicle__plate_number",

        "vehicle__brand",

        "vehicle__model",

        "problem_description",

        "plate_number",

    )

    readonly_fields = (

        "created_at",

        "updated_at",

    )

    ordering = (

        "-created_at",

    )

    list_per_page = 30

    autocomplete_fields = (

        "customer",

        "vehicle",

    )

    list_select_related = (

        "customer",

        "vehicle",

    )

    exclude = (
        "vehicle_year",
    )

    actions = (

        "convert_to_repair",

    )

    # =====================================================
    # Display
    # =====================================================


    @admin.display(
        description="نوع خدمت",
        ordering="service_type",
    )
    def service_type_display(
        self,
        obj,
    ):

        return (
            obj.get_service_type_display()
        )


    # =====================================================
    # Vehicle Autocomplete Filter
    # =====================================================

    def get_search_results(
        self,
        request,
        queryset,
        search_term,
    ):

        queryset, use_distinct = (
            super().get_search_results(
                request,
                queryset,
                search_term,
            )
        )

        customer_id = request.GET.get(
            "customer_id"
        )

        vehicle_id = request.GET.get(
            "vehicle_id"
        )

        if customer_id:

            queryset = queryset.filter(
                customer_id=customer_id
            )

        if vehicle_id:

            queryset = queryset.filter(
                vehicle_id=vehicle_id
            )

        return (
            queryset,
            use_distinct,
        )

    # =====================================================
    # Convert To Repair
    # =====================================================

    @admin.action(
        description="تبدیل به پذیرش تعمیر"
    )
    def convert_to_repair(
        self,
        request,
        queryset,
    ):

        if queryset.count() != 1:

            self.message_user(
                request,
                "فقط یک درخواست را انتخاب کنید.",
                level=messages.ERROR,
            )

            return

        service_request = (
            queryset.first()
        )

        if hasattr(
            service_request,
            "repair",
        ):

            self.message_user(
                request,
                "برای این درخواست قبلاً پذیرش ایجاد شده است.",
                level=messages.WARNING,
            )

            return

        repair = Repair.objects.create(

            customer=(
                service_request.customer
            ),

            vehicle=(
                service_request.vehicle
            ),

            service_request=(
                service_request
            ),

        )

        self.message_user(
            request,
            (
                f"پذیرش "
                f"{repair.repair_number} "
                "ایجاد شد."
            ),
            level=messages.SUCCESS,
        )

    @admin.display(description="خودرو")
    def vehicle_display(self, obj):
        vehicle = obj.vehicle

        if not vehicle:
            return "-"

        vehicle_name = " ".join(
            str(value).strip()
            for value in (
                vehicle.brand,
                vehicle.model,
            )
            if value
        )

        plate = format_plate_admin(
            vehicle.plate_number
        )

        return format_html(
            "{} | {}",
            vehicle_name or "-",
            plate,
        )

    @admin.display(description="شماره پلاک")
    def vehicle_plate_display(self, obj):
        if not obj.vehicle or not obj.vehicle.plate_number:
            return "-"

        return format_plate_admin(obj.vehicle.plate_number)