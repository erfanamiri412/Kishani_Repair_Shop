from django.contrib import admin, messages
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget
from django.utils import timezone
from datetime import datetime
from django import forms
from django.db import transaction
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .admin_utils import format_plate_admin
from crm.widgets import IranianPlateWidget
from core.admin import (
    BaseModelAdmin,
    BaseTabularInline,
    BaseAdminForm,
)
from .models import (
    Customer,
    CustomerVehicle,
    Repair,
    RepairPart,
    RepairServiceItem,
    Invoice,
    InvoiceItem,
    InvoicePayment,
    CustomerServiceRequest
)

class CustomerVehicleAdminForm(forms.ModelForm):

    class Meta:
        model = CustomerVehicle
        fields = "__all__"

        labels = {
            "brand": "نام خودرو",
            "company": "شرکت سازنده",
            "model": "سال ساخت",
            "plate_number": "شماره پلاک",
            "transmission": "گیربکس",
        }

        widgets = {
            "plate_number": IranianPlateWidget(),
        }

class CustomerVehicleInline(BaseTabularInline):


    model = CustomerVehicle
    form = CustomerVehicleAdminForm

    extra = 0
    show_change_link = False
    can_delete = True

    fields = (
        "plate_number",
        "brand",
        "company",
        "model",
        "transmission",
    )

    verbose_name = "خودرو"
    verbose_name_plural = "خودروهای مشتری"

@admin.register(CustomerVehicle)
class CustomerVehicleAdmin(BaseModelAdmin):

    form = CustomerVehicleAdminForm

    list_display = (
        "customer_name",
        "formatted_plate_admin",
        "vehicle_name",
        "company",
        "model",
        "transmission",
    )

    search_fields = (
        "plate_number",
        "brand",
        "company",
        "model",
        "transmission",
        "customer__full_name",
        "customer__mobile",
    )

    list_filter = (
        "company",
        "transmission",
    )

    autocomplete_fields = (
        "customer",
    )

    @admin.display(description="مالک خودرو")
    def customer_name(self, obj):
        if not obj.customer:
            return "-"
        return obj.customer.full_name

    @admin.display(description="نام خودرو", ordering="brand")
    def vehicle_name(self, obj):
        return obj.brand or "-"

    @admin.display(description="پلاک")
    def formatted_plate_admin(self, obj):
        return format_plate_admin(obj.plate_number)

    def get_search_results(
        self,
        request,
        queryset,
        search_term,
    ):
        queryset, use_distinct = super().get_search_results(
            request,
            queryset,
            search_term,
        )

        if request.GET.get("field_name") == "vehicle":
            customer_id = request.GET.get("customer_id")

            if customer_id:
                queryset = queryset.filter(
                    customer_id=customer_id
                )
            else:
                queryset = queryset.none()

        return queryset, use_distinct

@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):

    list_display = (
        "full_name",
        "mobile",
        "vehicles_count",
        "vehicles_list",
    )

    search_fields = (
        "full_name",
        "mobile",
    )

    inlines = [
        CustomerVehicleInline,
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("vehicles")
        )

    @admin.display(description="خودروها")
    def vehicles_list(self, obj):
        vehicles = list(obj.vehicles.all()[:4])

        names = [
            (vehicle.brand or "").strip() or "-"
            for vehicle in vehicles[:3]
        ]

        if len(vehicles) > 3:
            names.append("...")

        return " | ".join(names) or "-"

    @admin.display(description="تعداد خودرو")
    def vehicles_count(self, obj):
        return obj.vehicles.count()

class CustomerServiceRequestAdminForm(forms.ModelForm):

    class Meta:
        model = CustomerServiceRequest
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "vehicle" not in self.fields:
            return

        if self.is_bound:
            customer_id = self.data.get(
                self.add_prefix("customer")
            )
        else:
            customer_id = (
                self.initial.get("customer")
                or self.instance.customer_id
            )

        if hasattr(customer_id, "pk"):
            customer_id = customer_id.pk

        if customer_id:
            self.fields["vehicle"].queryset = (
                CustomerVehicle.objects.filter(
                    customer_id=customer_id
                )
            )
        else:
            self.fields["vehicle"].queryset = (
                CustomerVehicle.objects.none()
            )

import crm.admin_permissions

class RepairPartInlineForm(
    forms.ModelForm,
):

    class Meta:
        model = RepairPart

        fields = (
            "part_name",
            "quantity",
            "unit_price",
        )

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        # حذف اعشار از نمایش قیمت
        if (
            self.instance
            and self.instance.pk
            and self.instance.unit_price is not None
        ):

            self.initial["unit_price"] = int(
                self.instance.unit_price
            )

        self.fields["quantity"].label = "تعداد"
        self.fields["unit_price"].label = "قیمت واحد"

    def save(
        self,
        commit=True,
    ):

        instance = super().save(
            commit=False
        )

        quantity = int(
            instance.quantity or 0
        )

        unit_price = int(
            instance.unit_price or 0
        )

        # توجه:
        # total_price در مدل Property است،
        # پس نیازی به instance.total_price = ... نیست.

        if commit:
            instance.save()

        return instance

class RepairPartInline(
    BaseTabularInline,
):

    model = RepairPart

    form = RepairPartInlineForm

    extra = 0

    can_delete = True
    show_change_link = False

    classes = (
        "repair-part-inline",
    )

    fields = (
        "part_name",
        "quantity",
        "unit_price",
    )

    verbose_name = "قطعه مصرفی"
    verbose_name_plural = "قطعات مصرفی"

class RepairServiceItemInlineForm(
    forms.ModelForm,
):

    class Meta:
        model = RepairServiceItem

        fields = (
            "title",
            "unit_price",
        )

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields["title"].label = "شرح خدمت"
        self.fields["unit_price"].label = "دستمزد"

        if (
            self.instance
            and self.instance.pk
            and self.instance.unit_price is not None
        ):
            self.initial["unit_price"] = int(
                self.instance.unit_price
            )

class RepairServiceItemInline(
    BaseTabularInline,
):

    model = RepairServiceItem

    form = RepairServiceItemInlineForm

    extra = 0

    can_delete = True
    show_change_link = False

    fields = (
        "title",
        "unit_price",
    )

    classes = (
        "repair-service-inline",
    )

    verbose_name = "خدمت انجام‌شده"
    verbose_name_plural = "خدمات انجام‌شده"     

@admin.register(Repair)
class RepairAdmin(
    BaseModelAdmin,
):

    form = BaseAdminForm

    class Media:
        js = (
            "assets/js/audit_inline.js",
            "assets/js/admin_dependent_fields.js",
            "assets/js/admin_number_formatter.js",
            "assets/js/admin_time_picker.js",
        )

        css = {
            "all": (
                "assets/css/admin_time_picker.css",
            ),
        }
    actions = (
        "create_invoice_action",
    )

    list_display = (
        "repair_number",
        "customer_name_display",
        "vehicle_name_display",
        "plate_number_display",
        "parts_total_display",
        "services_total_display",
        "total_amount_display",
        "created_date_display",
    )

    list_filter = (
        "delivered_at",
        "created_at",
    )

    search_fields = (
        "repair_number",
        "customer__full_name",
        "customer__mobile",
        "vehicle__plate_number",
        "vehicle__brand",
        "vehicle__company",
        "vehicle__model",
    )

    readonly_fields = (
        "repair_number",
        "created_at",
        "updated_at",
        "parts_total_display",
        "services_total_display",
        "total_amount_display",
    )

    inlines = (
        RepairServiceItemInline,
        RepairPartInline,
    )

    autocomplete_fields = (
        "customer",
        "vehicle",
        "service_request",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "customer",
        "vehicle",
        "service_request",
        "mechanic",
    )

    list_per_page = 30

    fieldsets = (
        (
            "اطلاعات پذیرش",
            {
                "fields": (
                    "repair_number",
                    "customer",
                    "vehicle",
                    "service_request",
                    "mechanic",
                ),
            },
        ),

        (
            "زمان تحویل",
            {
                "fields": (
                    "delivered_at",
                ),
            },
        ),

        (
            "خلاصه مالی",
            {
                "fields": (
                    "parts_total_display",
                    "services_total_display",
                    "total_amount_display",
                ),
            },
        ),

        (
            "اطلاعات سیستمی",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="مشتری",
        ordering="customer__full_name",
    )
    def customer_name_display(
        self,
        obj,
    ):

        if not obj.customer_id:
            return "-"

        return obj.customer.full_name

    @admin.display(
        description="خودرو",
        ordering="vehicle__brand",
    )
    def vehicle_name_display(
        self,
        obj,
    ):

        if not obj.vehicle_id:
            return "-"

        return obj.vehicle.brand

    @admin.display(
        description="پلاک",
    )
    def plate_number_display(
        self,
        obj,
    ):

        if not obj.vehicle_id:
            return "-"

        plate = (
            obj.vehicle.plate_number
            .strip()
        )

        import re

        match = re.match(
            r"^(\d{2})([آ-ی])(\d{3})(\d{2})$",
            plate,
        )

        if not match:
            return format_html(
                '<span dir="ltr" '
                'style="'
                'direction:ltr;'
                'unicode-bidi:isolate;'
                'white-space:nowrap;'
                '">'
                '{}'
                '</span>',
                plate,
            )

        first_two = match.group(1)
        letter = match.group(2)
        middle_three = match.group(3)
        iran_code = match.group(4)

        return format_html(
            '<span dir="ltr" '
            'style="'
            'direction:ltr;'
            'unicode-bidi:isolate;'
            'white-space:nowrap;'
            'display:inline-flex;'
            'align-items:center;'
            '">'
            '<span>{}</span>'
            '<span>&nbsp;/&nbsp;</span>'
            '<span>{}</span>'
            '<span>&nbsp;/&nbsp;</span>'
            '<span>{}</span>'
            '<span>&nbsp;/&nbsp;</span>'
            '<span dir="ltr">'
            'ایران&nbsp;{}'
            '</span>'
            '</span>',
            first_two,
            letter,
            middle_three,
            iran_code,
        )

    @admin.display(
        description="جمع قطعات",
    )
    def parts_total_display(
        self,
        obj,
    ):

        return f"{obj.parts_total:,.0f}"

    @admin.display(
        description="جمع خدمات",
    )
    def services_total_display(
        self,
        obj,
    ):

        return f"{obj.services_total:,.0f}"

    @admin.display(
        description="مبلغ نهایی",
    )
    def total_amount_display(
        self,
        obj,
    ):

        return f"{obj.total_amount:,.0f}"

    @admin.display(
        description="تاریخ ثبت",
        ordering="created_at",
    )
    def created_date_display(
        self,
        obj,
    ):

        if not obj.created_at:
            return "-"

        return obj.created_at.strftime(
            "%Y/%m/%d"
        )

    @admin.action(
        description="فاکتورگیری",
    )
    def create_invoice_action(
        self,
        request,
        queryset,
    ):

        selected_count = queryset.count()
        target_invoice = None

        for repair in queryset.select_related(
            "customer",
            "vehicle",
            "mechanic",
        ).prefetch_related(
            "services",
            "parts",
        ):

            if (
                not repair.services.exists()
                and not repair.parts.exists()
            ):
                self.message_user(
                    request,
                    (
                        f"برای تعمیر "
                        f"{repair.repair_number} "
                        f"هیچ خدمت یا قطعه‌ای "
                        f"ثبت نشده است."
                    ),
                    messages.ERROR,
                )
                continue

            with transaction.atomic():

                invoice, created = (
                    Invoice.objects.get_or_create(
                        repair=repair,
                    )
                )

                invoice.items.all().delete()

                for service in repair.services.all():

                    InvoiceItem.objects.create(
                        invoice=invoice,
                        item_type="service",
                        title=service.title,
                        quantity=service.quantity,
                        unit_price=service.unit_price,
                        mechanic=(
                            service.mechanic
                            or repair.mechanic
                        ),
                    )

                for part in repair.parts.all():

                    InvoiceItem.objects.create(
                        invoice=invoice,
                        item_type="part",
                        title=part.part_name,
                        quantity=part.quantity,
                        unit_price=part.unit_price,
                    )

                target_invoice = invoice

                self.message_user(
                    request,
                    (
                        f"فاکتور "
                        f"{invoice.invoice_number} "
                        f"برای تعمیر "
                        f"{repair.repair_number} "
                        f"آماده شد."
                    ),
                    messages.SUCCESS,
                )

        if (
            selected_count == 1
            and target_invoice
        ):

            url = reverse(
                (
                    f"admin:"
                    f"{target_invoice._meta.app_label}_"
                    f"{target_invoice._meta.model_name}_change"
                ),
                args=[
                    target_invoice.pk,
                ],
            )

            return redirect(url)

class InvoiceServiceItemInline(
    admin.TabularInline,
):

    classes = (
        "invoice-service-inline",
    )

    model = InvoiceItem

    extra = 0
    can_delete = False
    show_change_link = False

    verbose_name = "خدمت"
    verbose_name_plural = "خدمات"

    fields = (
        "title",
        "total_price_display",
    )

    readonly_fields = (
        "title",
        "total_price_display",
    )

    def get_queryset(
        self,
        request,
    ):

        return (
            super()
            .get_queryset(request)
            .filter(
                item_type="service"
            )
        )

    @admin.display(
        description="مبلغ",
    )
    def total_price_display(
        self,
        obj,
    ):

        if not obj or not obj.pk:
            return "-"

        value = obj.total_price or 0

        return (
            f"{int(value):,} تومان"
        )

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        return False

class InvoicePartItemInline(
    admin.TabularInline,
):

    classes = (
        "invoice-part-inline",
    )

    model = InvoiceItem

    extra = 0
    can_delete = False
    show_change_link = False

    verbose_name = "قطعه"
    verbose_name_plural = "قطعات"

    fields = (
        "title",
        "quantity",
        "total_price_display",
    )

    readonly_fields = (
        "title",
        "quantity",
        "total_price_display",
    )

    def get_queryset(
        self,
        request,
    ):

        return (
            super()
            .get_queryset(request)
            .filter(
                item_type="part"
            )
        )

    @admin.display(
        description="مبلغ",
    )
    def total_price_display(
        self,
        obj,
    ):

        if not obj or not obj.pk:
            return "-"

        value = obj.total_price or 0

        return (
            f"{int(value):,} تومان"
        )

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        return False
    
class InvoicePaymentInlineForm(
    forms.ModelForm,
):

    paid_at = JalaliDateField(
        label="تاریخ",
        required=True,
        widget=AdminJalaliDateWidget,
    )

    class Meta:
        model = InvoicePayment

        fields = (
            "amount",
            "payment_method",
            "paid_at",
        )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields["amount"].label = (
            "مبلغ پرداختی"
        )

        self.fields["payment_method"].label = (
            "روش پرداخت"
        )

        self.fields["paid_at"].label = (
            "تاریخ"
        )

        if (
            self.instance
            and self.instance.pk
            and self.instance.paid_at
        ):
            self.initial["paid_at"] = (
                self.instance.paid_at.date()
            )

    def save(
        self,
        commit=True,
    ):

        instance = super().save(
            commit=False
        )

        selected_date = (
            self.cleaned_data.get("paid_at")
        )

        if selected_date:

            if (
                self.instance
                and self.instance.pk
                and self.instance.paid_at
            ):

                current_time = (
                    timezone.localtime(
                        self.instance.paid_at
                    ).time()
                )

            else:

                current_time = (
                    timezone.localtime().time()
                )

            instance.paid_at = (
                timezone.make_aware(
                    datetime.combine(
                        selected_date,
                        current_time,
                    ),
                    timezone.get_current_timezone(),
                )
            )

        if commit:
            instance.save()

        return instance

class InvoicePaymentInline(
    admin.TabularInline,
):

    classes = (
        "invoice-payment-inline",
    )

    model = InvoicePayment

    form = InvoicePaymentInlineForm

    extra = 0

    can_delete = False
    show_change_link = False

    verbose_name = "پرداخت"
    verbose_name_plural = "پرداخت‌ها"

    fields = (
        "amount",
        "payment_method",
        "paid_at",
    )

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        return True
    
@admin.register(Invoice)
class InvoiceAdmin(
    BaseModelAdmin,
):

    list_display = (
        "invoice_number",
        "tracking_code",
        "repair_number_display",
        "customer_display",
        "vehicle_display",
        "plate_display",
        "total_display",
        "paid_display",
        "remaining_display",
        "payment_status_display",
        "payment_methods_display",
        "issued_at",
        "preview_link",
        "print_link",
    )

    list_filter = (
        "issued_at",
    )

    search_fields = (
        "invoice_number",
        "tracking_code",
        "repair__repair_number",
        "repair__customer__full_name",
        "repair__customer__mobile",
        "repair__vehicle__plate_number",
        "repair__vehicle__brand",
    )

    autocomplete_fields = (
        "repair",
    )

    readonly_fields = (
        "invoice_number",
        "tracking_code",
        "issued_at",
        "repair_number_display",
        "customer_display",
        "vehicle_display",
        "plate_display",
        "total_display",
        "paid_display",
        "remaining_display",
        "payment_status_display",
        "payment_methods_display",
    )

    fieldsets = (
        (
            "اطلاعات اصلی فاکتور",
            {
                "fields": (
                    "repair",
                    "repair_number_display",
                    "invoice_number",
                    "tracking_code",
                    "customer_display",
                    "vehicle_display",
                    "plate_display",
                    "issued_at",
                ),
            },
        ),

        (
            "خلاصه مالی",
            {
                "fields": (
                    "total_display",
                    "paid_display",
                    "remaining_display",
                    "payment_status_display",
                    "payment_methods_display",
                ),
            },
        ),
    )

    inlines = (
        InvoiceServiceItemInline,
        InvoicePartItemInline,
        InvoicePaymentInline,
    )

    def get_queryset(
        self,
        request,
    ):

        return (
            super()
            .get_queryset(request)
            .select_related(
                "repair",
                "repair__customer",
                "repair__vehicle",
            )
            .prefetch_related(
                "items",
                "payments",
            )
        )

    @admin.display(
        description="شماره پذیرش",
        ordering="repair__repair_number",
    )
    def repair_number_display(
        self,
        obj,
    ):

        if not obj.repair_id:
            return "-"

        return obj.repair.repair_number

    @admin.display(
        description="مشتری",
        ordering="repair__customer__full_name",
    )
    def customer_display(
        self,
        obj,
    ):

        if not obj.repair_id:
            return "-"

        if not obj.repair.customer_id:
            return "-"

        return obj.repair.customer.full_name

    @admin.display(
        description="خودرو",
        ordering="repair__vehicle__brand",
    )
    def vehicle_display(
        self,
        obj,
    ):

        if not obj.repair_id:
            return "-"

        if not obj.repair.vehicle_id:
            return "-"

        return obj.repair.vehicle.brand

    @admin.display(
        description="پلاک",
    )
    def plate_display(
        self,
        obj,
    ):

        if not obj.repair_id:
            return "-"

        if not obj.repair.vehicle_id:
            return "-"

        plate = (
            obj.repair.vehicle.plate_number
            .strip()
        )

        import re

        match = re.match(
            r"^(\d{2})([آ-ی])(\d{3})(\d{2})$",
            plate,
        )

        if not match:
            return format_html(
                '<span dir="ltr" '
                'style="'
                'direction:ltr;'
                'unicode-bidi:isolate;'
                'white-space:nowrap;'
                '">'
                '{}'
                '</span>',
                plate,
            )

        first_two = match.group(1)
        letter = match.group(2)
        middle_three = match.group(3)
        iran_code = match.group(4)

        return format_html(
            '<span dir="ltr" '
            'style="'
            'direction:ltr;'
            'unicode-bidi:isolate;'
            'white-space:nowrap;'
            'display:inline-flex;'
            'align-items:center;'
            '">'
            '<span>{}</span>'
            '<span>&nbsp;/&nbsp;</span>'
            '<span>{}</span>'
            '<span>&nbsp;/&nbsp;</span>'
            '<span>{}</span>'
            '<span>&nbsp;/&nbsp;</span>'
            '<span dir="ltr">'
            'ایران&nbsp;{}'
            '</span>'
            '</span>',
            first_two,
            letter,
            middle_three,
            iran_code,
        )

    @admin.display(
        description="مبلغ کل",
    )
    def total_display(
        self,
        obj,
    ):

        return (
            f"{obj.total_amount:,.0f}"
            " تومان"
        )

    @admin.display(
        description="پرداخت شده",
    )
    def paid_display(
        self,
        obj,
    ):

        return (
            f"{obj.paid_amount:,.0f}"
            " تومان"
        )

    @admin.display(
        description="باقیمانده",
    )
    def remaining_display(
        self,
        obj,
    ):

        return (
            f"{obj.remaining_amount:,.0f}"
            " تومان"
        )

    @admin.display(
        description="وضعیت پرداخت",
    )
    def payment_status_display(
        self,
        obj,
    ):

        return obj.payment_status

    @admin.display(
        description="روش پرداخت",
    )
    def payment_methods_display(
        self,
        obj,
    ):

        payments = obj.payments.all()

        if not payments:
            return "-"

        methods = []

        for payment in payments:

            method = (
                payment
                .get_payment_method_display()
            )

            if method not in methods:
                methods.append(method)

        return "، ".join(methods)

    @admin.display(
        description="پیش‌نمایش",
    )
    def preview_link(
        self,
        obj,
    ):

        if not obj.pk:
            return "-"

        url = reverse(
            "admin:crm_invoice_preview",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}" '
            'target="_blank" '
            'style="font-weight:700;">'
            'مشاهده'
            '</a>',
            url,
        )

    @admin.display(
        description="چاپ",
    )
    def print_link(
        self,
        obj,
    ):

        if not obj.pk:
            return "-"

        url = reverse(
            "admin:crm_invoice_print",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}" '
            'target="_blank" '
            'style="font-weight:700;">'
            'چاپ'
            '</a>',
            url,
        )

    def get_urls(
        self,
    ):

        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/preview/",
                self.admin_site.admin_view(
                    self.preview_invoice
                ),
                name="crm_invoice_preview",
            ),
            path(
                "<path:object_id>/print/",
                self.admin_site.admin_view(
                    self.print_invoice
                ),
                name="crm_invoice_print",
            ),
        ]

        return custom_urls + urls

    def get_invoice(
        self,
        object_id,
    ):

        return get_object_or_404(
            Invoice.objects
            .select_related(
                "repair",
                "repair__customer",
                "repair__vehicle",
            )
            .prefetch_related(
                "items__mechanic",
                "payments",
            ),
            pk=object_id,
        )

    def get_grouped_items(
        self,
        invoice,
    ):

        from collections import OrderedDict

        grouped_items = OrderedDict()

        for item in invoice.items.all():

            if item.item_type == "service":
                category = "خدمات"

            elif item.item_type == "part":
                category = "قطعات"

            else:
                continue

            grouped_items.setdefault(
                category,
                [],
            ).append(item)

        return grouped_items.items()

    def preview_invoice(
        self,
        request,
        object_id,
    ):

        invoice = self.get_invoice(
            object_id
        )

        back_url = reverse(
            (
                f"admin:"
                f"{invoice._meta.app_label}_"
                f"{invoice._meta.model_name}_change"
            ),
            args=[
                invoice.pk,
            ],
        )

        context = {
            **self.admin_site.each_context(
                request
            ),
            "invoice": invoice,
            "grouped_items": (
                self.get_grouped_items(
                    invoice
                )
            ),
            "back_url": back_url,
        }

        return TemplateResponse(
            request,
            "invoice/preview.html",
            context,
        )

    def print_invoice(
        self,
        request,
        object_id,
    ):

        invoice = self.get_invoice(
            object_id
        )

        context = {
            **self.admin_site.each_context(
                request
            ),
            "invoice": invoice,
            "grouped_items": (
                self.get_grouped_items(
                    invoice
                )
            ),
        }

        return TemplateResponse(
            request,
            "invoice/print.html",
            context,
        )