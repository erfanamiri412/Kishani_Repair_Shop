from django import forms
from django.contrib import admin
from core.admin import BaseTabularInline, BaseJalaliAdmin
from .models import (
    AuditLog,
    InventoryUsedPart,
    PurchasedPart,
    CustomerPart,
)
from django.http import JsonResponse
from django.urls import path
from core.admin import (
    BaseTabularInline,
    BaseJalaliAdmin,
)
from inventory.models import Part
import re

from django.core.exceptions import (
    ObjectDoesNotExist,
    FieldDoesNotExist,
)
class InventoryUsedPartInline(
    BaseTabularInline,
):

    model = InventoryUsedPart

    extra = 0

    classes = (
        "collapse",
    )

    autocomplete_fields = (
        "part",
    )

    fields = (
        "part",
        "quantity",
    )

    readonly_fields = (
        "total_price_display",
    )

    verbose_name = "قطعه مصرفی انبار"
    verbose_name_plural = "قطعات مصرفی"
    show_change_link = False

    @admin.display(
        description="جمع قیمت",
    )
    def total_price_display(
        self,
        obj,
    ):

        if not obj or not obj.part_id:
            return "-"

        quantity = int(
            obj.quantity or 0
        )

        price = int(
            obj.part.sale_price or 0
        )

        return f"{quantity * price:,}"

class PurchasedPartInline(
    BaseTabularInline,
):

    model = PurchasedPart

    extra = 0

    classes = (
        "collapse",
    )

    fields = (
        "part_name",
        "supplier",
        "quantity",
    )

    readonly_fields = (
        "total_price_display",
    )

    verbose_name = "قطعه خریداری شده از بیرون"
    verbose_name_plural = "قطعات خریداری شده"

    @admin.display(
        description="جمع قیمت",
    )
    def total_price_display(
        self,
        obj,
    ):

        if not obj or not obj.pk:
            return "-"

        return f"{obj.total_price:,}"

class CustomerPartInline(
    BaseTabularInline,
):

    model = CustomerPart

    fk_name = "audit"

    extra = 0

    classes = (
        "collapse",
    )

    fields = (
        "part_name",
        "quantity",
    )

    readonly_fields = (
        "total_price_display",
    )

    verbose_name = "قطعه خریداری شده توسط مشتری"
    verbose_name_plural = "قطعات مشتری"

    show_change_link = False

    @admin.display(
        description="جمع قیمت",
    )
    def total_price_display(
        self,
        obj,
    ):

        if not obj or not obj.pk:
            return "-"

        return f"{obj.total_price:,}"
    


@admin.register(AuditLog)
class AuditLogAdmin(BaseJalaliAdmin):

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "part-price/",
                self.admin_site.admin_view(
                    self.part_price_view
                ),
                name="audit_auditlog_part_price",
            ),
            path(
                "service-request-details/",
                self.admin_site.admin_view(
                    self.service_request_details_view
                ),
                name="audit_auditlog_service_request_details",
            ),
        ]

        return custom_urls + urls

    def part_price_view(self, request):
        part_id = request.GET.get("part_id")

        if not part_id:
            return JsonResponse({
                "success": False,
                "price": 0,
            })

        try:
            part = Part.objects.get(pk=part_id)
        except (
            Part.DoesNotExist,
            ValueError,
            TypeError,
        ):
            return JsonResponse({
                "success": False,
                "price": 0,
            })

        return JsonResponse({
            "success": True,
            "price": int(part.sale_price or 0),
        })

    @staticmethod
    def _get_attr(obj, attr_name):
        if obj is None:
            return None

        try:
            return getattr(obj, attr_name, None)
        except (
            AttributeError,
            ObjectDoesNotExist,
            TypeError,
        ):
            return None

    @classmethod
    def _text_value(cls, value):
        if callable(value):
            try:
                value = value()
            except (
                AttributeError,
                ObjectDoesNotExist,
                TypeError,
            ):
                return ""

        if isinstance(value, str):
            return value.strip()

        return ""

    @classmethod
    def _text_attr(cls, obj, *attr_names):
        for attr_name in attr_names:
            value = cls._get_attr(obj, attr_name)
            text = cls._text_value(value)

            if text:
                return text

        return ""

    @classmethod
    def _component_text(cls, value):
        text = cls._text_value(value)

        if text:
            return text

        for attr_name in (
            "name",
            "title",
            "label",
            "brand_name",
            "model_name",
        ):
            text = cls._text_attr(value, attr_name)

            if text:
                return text

        return ""

    @classmethod
    def _person_name(cls, obj):
        if obj is None:
            return ""

        full_name = cls._text_attr(
            obj,
            "full_name",
            "get_full_name",
            "display_name",
            "customer_name",
        )

        if full_name:
            return full_name

        first_name = cls._text_attr(
            obj,
            "first_name",
            "given_name",
        )

        last_name = cls._text_attr(
            obj,
            "last_name",
            "family_name",
            "surname",
        )

        if first_name or last_name:
            return f"{first_name} {last_name}".strip()

        return cls._text_attr(obj, "name")

    @classmethod
    def _find_customer_name(
        cls,
        obj,
        depth=0,
        visited=None,
    ):
        if obj is None or depth > 3:
            return ""

        if visited is None:
            visited = set()

        identity = (
            obj.__class__,
            getattr(obj, "pk", id(obj)),
        )

        if identity in visited:
            return ""

        visited.add(identity)

        model_name = getattr(
            getattr(obj, "_meta", None),
            "model_name",
            "",
        ).lower()

        if (
            depth > 0
            and any(
                token in model_name
                for token in (
                    "customer",
                    "client",
                    "person",
                    "contact",
                )
            )
            and "vehicle" not in model_name
        ):
            result = cls._person_name(obj)

            if result:
                return result

        try:
            fields = obj._meta.get_fields()
        except (AttributeError, TypeError):
            return ""

        relations = [
            field
            for field in fields
            if (
                getattr(field, "concrete", False)
                and getattr(field, "is_relation", False)
                and (
                    getattr(field, "many_to_one", False)
                    or getattr(field, "one_to_one", False)
                )
            )
        ]

        relations.sort(
            key=lambda field: (
                0
                if (
                    "customer" in field.name.lower()
                    and "vehicle" not in field.name.lower()
                )
                else 1
                if any(
                    token in field.name.lower()
                    for token in (
                        "client",
                        "owner",
                        "contact",
                    )
                )
                else 2
                if "vehicle" in field.name.lower()
                else 3
            )
        )

        for field in relations:
            field_name = field.name.lower()

            if not any(
                token in field_name
                for token in (
                    "customer",
                    "client",
                    "owner",
                    "contact",
                    "vehicle",
                    "person",
                )
            ):
                continue

            related_obj = cls._get_attr(
                obj,
                field.name,
            )

            if related_obj is None:
                continue

            if (
                any(
                    token in field_name
                    for token in (
                        "customer",
                        "client",
                        "owner",
                        "contact",
                        "person",
                    )
                )
                and "vehicle" not in field_name
            ):
                result = cls._person_name(related_obj)

                if result:
                    return result

            result = cls._find_customer_name(
                related_obj,
                depth + 1,
                visited,
            )

            if result:
                return result

        return ""

    @classmethod
    def _customer_name_from_request(cls, service_request):
        if service_request is None:
            return "-"

        name = cls._text_attr(
            service_request,
            "customer_name",
            "full_name",
            "name",
        )

        if name:
            return name

        name = cls._find_customer_name(
            service_request
        )

        return name or "-"

    @staticmethod
    def _clean_vehicle_label(value):
        if not isinstance(value, str):
            return ""

        value = re.sub(
            r"(?<!\w)(?:13|14|19|20)[0-9۰-۹]{2}(?!\w)",
            " ",
            value,
        )

        value = re.sub(r"\s+", " ", value)

        return value.strip(" -_/،,")

    @classmethod
    def _vehicle_name_from_request(
        cls,
        service_request,
    ):
        if service_request is None:
            return "-"

        vehicle = cls._get_attr(
            service_request,
            "vehicle",
        )

        if vehicle is None:
            vehicle = cls._get_attr(
                service_request,
                "customer_vehicle",
            )

        if vehicle is None:
            return "-"

        if isinstance(vehicle, str):
            return (
                cls._clean_vehicle_label(vehicle)
                or "-"
            )

        brand = ""

        for attr_name in (
            "brand",
            "company",
            "make",
            "vehicle_brand",
        ):
            brand = cls._component_text(
                cls._get_attr(vehicle, attr_name)
            )

            if brand:
                break

        model = ""

        for attr_name in (
            "model",
            "vehicle_model",
            "model_name",
        ):
            model = cls._component_text(
                cls._get_attr(vehicle, attr_name)
            )

            if model:
                break

        brand = cls._clean_vehicle_label(brand)
        model = cls._clean_vehicle_label(model)

        if brand and model:
            if brand.casefold() == model.casefold():
                return brand

            if model.casefold().startswith(
                brand.casefold() + " "
            ):
                return model

            if brand.casefold() in model.casefold():
                return model

            return f"{brand} {model}"

        if brand:
            return brand

        if model:
            return model

        fallback_name = cls._text_attr(
            vehicle,
            "vehicle_name",
            "name",
            "title",
        )

        return (
            cls._clean_vehicle_label(fallback_name)
            or "-"
        )

    def service_request_details_view(self, request):
        if request.method != "GET":
            return JsonResponse(
                {
                    "success": False,
                    "error": "متد درخواست معتبر نیست.",
                },
                status=405,
            )

        service_request_id = request.GET.get(
            "service_request_id"
        )

        if not service_request_id:
            return JsonResponse({
                "success": False,
                "customer_name": "-",
                "vehicle_name": "-",
            })

        request_model = (
            AuditLog._meta
            .get_field("service_request")
            .remote_field.model
        )

        try:
            service_request = (
                request_model._default_manager.get(
                    pk=service_request_id
                )
            )
        except (
            ObjectDoesNotExist,
            ValueError,
            TypeError,
        ):
            return JsonResponse({
                "success": False,
                "customer_name": "-",
                "vehicle_name": "-",
            })

        return JsonResponse({
            "success": True,
            "customer_name": (
                self._customer_name_from_request(
                    service_request
                )
            ),
            "vehicle_name": (
                self._vehicle_name_from_request(
                    service_request
                )
            ),
        })

    class Media:
        js = (
            "assets/js/audit_inline.js",
            "assets/js/admin_number_formatter.js",
            "assets/js/admin_time_picker.js",
        )

        css = {
            "all": (
                "assets/css/admin_time_picker.css",
            ),
        }

    inlines = (
        InventoryUsedPartInline,
        PurchasedPartInline,
        CustomerPartInline,
    )

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(
            request,
            obj,
        )

        for inline in inline_instances:
            inline.extra = 0

        return inline_instances

    autocomplete_fields = (
        "mechanic",
        "service_request",
    )

    list_display = (
        "mechanic",
        "customer_name_display",
        "vehicle_display",
        "service_type",
        "service_date",
    )

    list_filter = (
        "mechanic",
        "service_type",
        "service_date",
        "created_at",
    )

    search_fields = (
        "mechanic__user__first_name",
        "mechanic__user__last_name",
        "mechanic__user__username",
    )


    def get_search_fields(self, request):
        text_field_types = {
            "CharField",
            "TextField",
            "EmailField",
            "SlugField",
            "URLField",
        }

        fields = []

        def add_text_fields(model, prefix=""):
            for model_field in model._meta.get_fields():
                if (
                    not getattr(model_field, "concrete", False)
                    or getattr(model_field, "is_relation", False)
                ):
                    continue

                if (
                    model_field.get_internal_type()
                    in text_field_types
                ):
                    fields.append(
                        f"{prefix}{model_field.name}"
                    )

        for field_name in (
            "service_type",
            "work_description",
        ):
            try:
                model_field = AuditLog._meta.get_field(
                    field_name
                )
            except FieldDoesNotExist:
                continue

            if (
                model_field.get_internal_type()
                in text_field_types
            ):
                fields.append(field_name)

        try:
            request_model = (
                AuditLog._meta
                .get_field("service_request")
                .remote_field.model
            )

            for field_name in (
                "name",
                "full_name",
                "phone",
                "mobile",
                "vehicle",
            ):
                try:
                    model_field = request_model._meta.get_field(
                        field_name
                    )
                except FieldDoesNotExist:
                    continue

                if (
                    model_field.get_internal_type()
                    in text_field_types
                ):
                    fields.append(
                        f"service_request__{field_name}"
                    )

        except FieldDoesNotExist:
            pass

        try:
            mechanic_model = (
                AuditLog._meta
                .get_field("mechanic")
                .remote_field.model
            )

            add_text_fields(
                mechanic_model,
                "mechanic__",
            )

            for relation in mechanic_model._meta.get_fields():
                if (
                    not getattr(relation, "concrete", False)
                    or not getattr(relation, "is_relation", False)
                    or not (
                        getattr(relation, "many_to_one", False)
                        or getattr(relation, "one_to_one", False)
                    )
                ):
                    continue

                related_model = relation.remote_field.model

                add_text_fields(
                    related_model,
                    f"mechanic__{relation.name}__",
                )

        except FieldDoesNotExist:
            pass

        return tuple(dict.fromkeys(fields))

    readonly_fields = (
        "created_at",
        "updated_at",
        "customer_name_display",
        "vehicle_display",
    )

    date_hierarchy = "service_date"

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "mechanic",
        "service_request",
    )

    list_per_page = 30

    fieldsets = (
        (
            "مکانیک و درخواست مرتبط",
            {
                "fields": (
                    "mechanic",
                    "service_request",
                    "customer_name_display",
                    "vehicle_display",
                ),
            },
        ),
        (
            "خدمات انجام شده",
            {
                "fields": (
                    "service_type",
                    "work_description",
                ),
            },
        ),
        (
            "زمان انجام خدمات",
            {
                "fields": (
                    "work_start",
                    "work_end",
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

    @admin.display(description="نام مشتری")
    def customer_name_display(self, obj):
        service_request = self._get_attr(
            obj,
            "service_request",
        )

        return self._customer_name_from_request(
            service_request
        )

    @admin.display(description="خودرو")
    def vehicle_display(self, obj):
        service_request = self._get_attr(
            obj,
            "service_request",
        )

        return self._vehicle_name_from_request(
            service_request
        )
