from django import forms
from core.admin import ServiceRequestSelect, CustomerVehicleSelect
from .models import (
    Repair,
    CustomerVehicle,
    CustomerServiceRequest,
    ServiceType,
)

class WebsiteServiceRequestForm(forms.Form):

    # =========================================================
    # Customer
    # =========================================================

    full_name = forms.CharField(
        max_length=200,
        required=True,
        label="نام و نام خانوادگی",
    )

    phone = forms.CharField(
        max_length=20,
        required=True,
        label="شماره تماس",
    )


    # =========================================================
    # Vehicle
    # =========================================================

    vehicle_brand = forms.CharField(
        max_length=100,
        required=True,
        label="برند خودرو",
    )

    vehicle_model = forms.CharField(
        max_length=100,
        required=True,
        label="مدل خودرو",
    )

    vehicle_year = forms.CharField(
        max_length=4,
        required=False,
        label="سال ساخت",
    )


    # =========================================================
    # Iranian Plate
    # =========================================================

    plate_city = forms.CharField(
        max_length=2,
        required=False,
        label="دو رقم اول پلاک",
    )

    plate_letter = forms.CharField(
        max_length=1,
        required=False,
        label="حرف پلاک",
    )

    plate_middle = forms.CharField(
        max_length=3,
        required=False,
        label="سه رقم پلاک",
    )

    plate_right = forms.CharField(
        max_length=2,
        required=False,
        label="کد ایران",
    )


    # =========================================================
    # Service
    # =========================================================

    service_type = forms.ChoiceField(
        choices=ServiceType.choices,
        required=True,
        label="نوع خدمت",
    )


    # =========================================================
    # Description
    # =========================================================

    problem_description = forms.CharField(
        required=True,
        label="شرح مشکل",
        widget=forms.Textarea,
    )


    # =========================================================
    # File
    # =========================================================

    attachment = forms.FileField(
        required=False,
        label="فایل پیوست",
    )


    # =========================================================
    # Honeypot
    # =========================================================

    website = forms.CharField(
        required=False,
    )


    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _normalize_digits(value):
        """
        تبدیل اعداد فارسی و عربی به انگلیسی.
        """

        if value is None:
            return value

        translation = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )

        return str(value).translate(
            translation
        )


    # =========================================================
    # Honeypot Validation
    # =========================================================

    def clean_website(self):

        website = (
            self.cleaned_data.get("website")
            or ""
        ).strip()

        if website:

            raise forms.ValidationError(
                "Invalid submission."
            )

        return website


    # =========================================================
    # Phone
    # =========================================================

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone"
        )

        phone = self._normalize_digits(
            phone
        )

        phone = (
            phone
            .replace(" ", "")
            .replace("-", "")
        )


        if phone.startswith("+98"):

            phone = (
                "0" +
                phone[3:]
            )

        elif phone.startswith("98"):

            phone = (
                "0" +
                phone[2:]
            )

        elif phone.startswith("9"):

            phone = (
                "0" +
                phone
            )


        if (
            not phone.isdigit()
            or len(phone) != 11
            or not phone.startswith("09")
        ):

            raise forms.ValidationError(
                "شماره موبایل معتبر وارد کنید."
            )

        return phone


    # =========================================================
    # Vehicle Year
    # =========================================================

    def clean_vehicle_year(self):

        value = self.cleaned_data.get(
            "vehicle_year"
        )

        value = self._normalize_digits(
            value
        )

        if not value:
            return None

        if not value.isdigit():

            raise forms.ValidationError(
                "سال ساخت باید فقط عدد باشد؛ مثلاً 1400."
            )

        if len(value) != 4:

            raise forms.ValidationError(
                "سال ساخت باید چهار رقمی باشد؛ مثلاً 1400."
            )

        return int(value)


    # =========================================================
    # Plate City
    # =========================================================

    def clean_plate_city(self):

        value = self._normalize_digits(
            self.cleaned_data.get(
                "plate_city"
            )
        )

        if not value:
            return ""

        if not value.isdigit():

            raise forms.ValidationError(
                "دو رقم اول پلاک باید عدد باشد."
            )

        if len(value) != 2:

            raise forms.ValidationError(
                "دو رقم اول پلاک باید دقیقاً ۲ رقم باشد."
            )

        return value


    # =========================================================
    # Plate Middle
    # =========================================================

    def clean_plate_middle(self):

        value = self._normalize_digits(
            self.cleaned_data.get(
                "plate_middle"
            )
        )

        if not value:
            return ""

        if not value.isdigit():

            raise forms.ValidationError(
                "بخش سه‌رقمی پلاک باید عدد باشد."
            )

        if len(value) != 3:

            raise forms.ValidationError(
                "بخش سه‌رقمی پلاک باید دقیقاً ۳ رقم باشد."
            )

        return value


    # =========================================================
    # Plate Right
    # =========================================================

    def clean_plate_right(self):

        value = self._normalize_digits(
            self.cleaned_data.get(
                "plate_right"
            )
        )

        if not value:
            return ""

        if not value.isdigit():

            raise forms.ValidationError(
                "کد ایران باید عدد باشد."
            )

        if len(value) != 2:

            raise forms.ValidationError(
                "کد ایران باید دقیقاً ۲ رقم باشد."
            )

        return value


    # =========================================================
    # Plate Letter
    # =========================================================

    def clean_plate_letter(self):

        value = (
            self.cleaned_data.get(
                "plate_letter"
            )
            or ""
        ).strip()

        if not value:
            return ""

        if len(value) != 1:

            raise forms.ValidationError(
                "حرف پلاک باید یک کاراکتر باشد."
            )

        return value

class RepairAdminForm(
    forms.ModelForm,
):

    class Meta:

        model = Repair

        fields = "__all__"

    def clean(self):

        cleaned_data = super().clean()

        customer = cleaned_data.get(
            "customer"
        )

        vehicle = cleaned_data.get(
            "vehicle"
        )

        service_request = cleaned_data.get(
            "service_request"
        )

        # ==================================================
        # Vehicle → Customer
        # ==================================================

        if (
            customer
            and vehicle
            and vehicle.customer_id
            != customer.id
        ):

            self.add_error(
                "vehicle",
                "خودروی انتخاب‌شده متعلق به این مشتری نیست.",
            )

        # ==================================================
        # Service Request → Customer
        # ==================================================

        if (
            customer
            and service_request
            and service_request.customer_id
            != customer.id
        ):

            self.add_error(
                "service_request",
                "درخواست خدمات متعلق به این مشتری نیست.",
            )

        # ==================================================
        # Service Request → Vehicle
        # ==================================================

        if (
            service_request
            and vehicle
            and service_request.vehicle_id
            and service_request.vehicle_id
            != vehicle.id
        ):

            self.add_error(
                "service_request",
                "درخواست خدمات مربوط به خودروی انتخاب‌شده نیست.",
            )

        return cleaned_data
    
class AdminTimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "format",
            "%H:%M",
        )

        attrs = kwargs.setdefault(
            "attrs",
            {},
        )

        attrs.setdefault(
            "class",
            "vTimeField",
        )

        super().__init__(
            *args,
            **kwargs,
        )

class BaseAdminForm(forms.ModelForm):

    class Meta:
        abstract = True

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        for field in self.fields.values():

            if isinstance(
                field,
                forms.TimeField,
            ):
                field.widget = AdminTimeInput(
                    format="%H:%M",
                )

class CustomerVehicleChoiceField(
    forms.ModelChoiceField
):

    def label_from_instance(
        self,
        obj,
    ):
        return (
            f"{obj.brand} {obj.model} | "
            f"{obj.formatted_plate}"
        )

class CustomerServiceRequestForm(
    forms.ModelForm
):

    vehicle = CustomerVehicleChoiceField(
        queryset=CustomerVehicle.objects.all(),
        label="خودرو",
        required=False,
    )

    class Meta:

        model = CustomerServiceRequest

        fields = (
            "customer",
            "service_type",
            "vehicle",
            "vehicle_year",
            "problem_description",
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

        customer_id = (
            self.data.get("customer")
            if self.is_bound
            else self.initial.get("customer")
        )

        if customer_id:

            self.fields[
                "vehicle"
            ].queryset = (
                CustomerVehicle.objects
                .filter(
                    customer_id=customer_id
                )
                .select_related(
                    "customer"
                )
            )

        else:

            self.fields[
                "vehicle"
            ].queryset = (
                CustomerVehicle.objects.none()
            )

        # ------------------------------------------------------
        # Customer
        # ------------------------------------------------------

        self.fields[
            "customer"
        ].widget.attrs.update({
            "data-dependent-field":
                "vehicle",
        })

        # ------------------------------------------------------
        # Vehicle
        # ------------------------------------------------------

        self.fields[
            "vehicle"
        ].widget.attrs.update({
            "data-parent-field":
                "customer",
        })
