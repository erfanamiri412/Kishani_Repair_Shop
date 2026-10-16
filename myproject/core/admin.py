from django import forms
from django.contrib import admin
from jalali_date.fields import (
    SplitJalaliDateTimeField,
)

from jalali_date.widgets import (
    AdminSplitJalaliDateTime,
)
from jalali_date.admin import (
    ModelAdminJalaliMixin,
    TabularInlineJalaliMixin,
    StackedInlineJalaliMixin,
)


# ==========================================================
# Numeric Widget
# ==========================================================

class AdminNumericInput(forms.TextInput):

    input_type = "text"

    def __init__(self, *args, **kwargs):

        attrs = kwargs.setdefault(
            "attrs",
            {},
        )

        attrs.setdefault(
            "inputmode",
            "numeric",
        )

        attrs.setdefault(
            "autocomplete",
            "off",
        )

        attrs.setdefault(
            "data-number-format",
            "true",
        )

        super().__init__(
            *args,
            **kwargs,
        )

    def value_from_datadict(
        self,
        data,
        files,
        name,
    ):

        value = super().value_from_datadict(
            data,
            files,
            name,
        )

        if value in (None, ""):
            return value

        value = str(value)

        value = value.replace(
            ",",
            "",
        )

        value = value.replace(
            "٬",
            "",
        )

        value = value.translate(
            str.maketrans(
                "۰۱۲۳۴۵۶۷۸۹",
                "0123456789",
            )
        )

        value = value.translate(
            str.maketrans(
                "٠١٢٣٤٥٦٧٨٩",
                "0123456789",
            )
        )

        return value

# ==========================================================
# Time Widget
# ==========================================================

class AdminTimeInput(forms.TextInput):

    input_type = "text"

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})

        attrs.update({
            "class": "vTextField admin-time-input",
            "readonly": "readonly",
            "autocomplete": "off",
            "placeholder": "انتخاب زمان",
            "data-time-picker": "true",
        })

        super().__init__(*args, **kwargs)

    def format_value(self, value):
        if value in (None, ""):
            return ""

        if hasattr(value, "strftime"):
            return value.strftime("%H:%M")

        value = str(value).strip()

        if len(value) >= 5 and value[2] == ":":
            return value[:5]

        return value
# ==========================================================
# Base Form
# ==========================================================

class AdminSplitJalaliDateTimeWithPicker(
    AdminSplitJalaliDateTime
):

    def get_context(
        self,
        name,
        value,
        attrs,
    ):

        context = super().get_context(
            name,
            value,
            attrs,
        )

        widgets = (
            context["widget"]["subwidgets"]
        )

        if len(widgets) >= 2:

            widgets[1]["attrs"][
                "data-time-picker"
            ] = "true"

            widgets[1]["attrs"][
                "class"
            ] = (
                widgets[1]["attrs"].get(
                    "class",
                    "",
                )
                + " admin-time-input"
            ).strip()

        return context

class CustomerVehicleSelect(
    forms.Select,
):

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):

        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex,
            attrs,
        )

        if (
            hasattr(
                value,
                "instance",
            )
            and value.instance
        ):

            option["attrs"][
                "data-customer-id"
            ] = str(
                value.instance.customer_id
            )

        return option

class ServiceRequestSelect(
    forms.Select,
):

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):

        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex,
            attrs,
        )

        if (
            hasattr(
                value,
                "instance",
            )
            and value.instance
        ):

            option["attrs"][
                "data-customer-id"
            ] = str(
                value.instance.customer_id
            )

            if value.instance.vehicle_id:

                option["attrs"][
                    "data-vehicle-id"
                ] = str(
                    value.instance.vehicle_id
                )

        return option
    
class BaseAdminForm(forms.ModelForm):

    class Meta:
        fields = "__all__"

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        for field_name, field in self.fields.items():

            # --------------------------------------------------
            # TimeField - Shared Time Picker
            # --------------------------------------------------

            if isinstance(field, forms.TimeField):

                old_attrs = dict(
                    field.widget.attrs
                )

                old_attrs.update({
                    "style": (
                        "width:100%;"
                        "max-width:100%;"
                    ),
                    "autocomplete": "off",
                })

                field.widget = AdminTimeInput(
                    attrs=old_attrs,
                )

                continue

            # --------------------------------------------------
            # Integer / Decimal
            # --------------------------------------------------

            if isinstance(
                field,
                (
                    forms.IntegerField,
                    forms.DecimalField,
                ),
            ):

                old_attrs = dict(
                    field.widget.attrs
                )

                old_attrs.update({
                    "style": (
                        "width:100%;"
                        "max-width:100%;"
                    ),
                    "class": "vTextField",
                    "inputmode": (
                        "decimal"
                        if isinstance(
                            field,
                            forms.DecimalField,
                        )
                        else "numeric"
                    ),
                    "autocomplete": "off",
                    "data-number-format": "true",
                })

                field.widget = AdminNumericInput(
                    attrs=old_attrs,
                )

                continue

            # --------------------------------------------------
            # General Widgets
            # --------------------------------------------------

            widget = field.widget

            widget.attrs.setdefault(
                "style",
                "width:100%;max-width:100%;",
            )

            widget.attrs.setdefault(
                "class",
                "vTextField",
            )

        # ------------------------------------------------------
        # Textarea
        # ------------------------------------------------------

        for field in self.fields.values():

            if isinstance(
                field.widget,
                forms.Textarea,
            ):

                field.widget.attrs.update({
                    "rows": 4,
                    "style": (
                        "width:100%;"
                        "max-width:100%;"
                    ),
                })

# ==========================================================
# Base Admin
# ==========================================================

class BaseModelAdmin(
    ModelAdminJalaliMixin,
    admin.ModelAdmin,
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
                "assets/css/admin_global.css",
                "assets/css/admin_time_picker.css",
            ),
        }

    save_on_top = False

    list_per_page = 30

    ordering = (
        "-id",
    )

    actions_on_top = True

    actions_on_bottom = False

    show_full_result_count = True

    list_select_related = ()

    empty_value_display = "-"

    save_as = False

    list_max_show_all = 200

    @staticmethod
    def format_price(
        value,
    ):

        if value is None:
            return "-"

        return f"{int(value):,} تومان"

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(
            request,
            obj,
            change=change,
            **kwargs,
        )

        for field in form.base_fields.values():
            widget = field.widget

            widget.attrs["autocomplete"] = "off"

            if isinstance(
                widget,
                (
                    forms.TextInput,
                    forms.EmailInput,
                    forms.URLInput,
                    forms.NumberInput,
                ),
            ):
                widget.attrs["autocomplete"] = "new-password"

        return form
        
    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):

        readonly = list(
            getattr(
                self,
                "readonly_fields",
                (),
            )
        )

        for field_name in (
            "created_at",
            "updated_at",
        ):

            if (
                hasattr(
                    self.model,
                    field_name,
                )
                and field_name not in readonly
            ):

                readonly.append(
                    field_name
                )

        return tuple(
            readonly
        )

# ==========================================================
# Inlines
# ==========================================================

class BaseTabularInline(
    TabularInlineJalaliMixin,
    admin.TabularInline,
):

    extra = 0

    show_change_link = True

    form = BaseAdminForm


class BaseStackedInline(
    StackedInlineJalaliMixin,
    admin.StackedInline,
):

    extra = 0

    show_change_link = True

    form = BaseAdminForm


# ==========================================================
# Jalali Admin
# ==========================================================

class JalaliAdminMixin:

    date_hierarchy = None


# ==========================================================
# Combined Base Admin
# ==========================================================

class BaseJalaliAdmin(
    JalaliAdminMixin,
    BaseModelAdmin,
):

    date_hierarchy = None