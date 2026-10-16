from django.core.exceptions import ValidationError



class ServiceRequestValidator:

    REQUIRED_FIELDS = [

        "full_name",

        "phone",

        "service_type",

        "vehicle_brand",

        "vehicle_model",

        "problem_description",

    ]

    @classmethod
    def validate(
        cls,
        data,
        request=None,
    ):

        cls.validate_required_fields(data)

        cls.normalize_phone(data)

        cls.normalize_strings(data)

        cls.attach_request_metadata(
            data,
            request,
        )

        cls.apply_defaults(data)

        return data

    @classmethod
    def validate_required_fields(
        cls,
        data,
    ):

        for field in cls.REQUIRED_FIELDS:

            if not data.get(field):

                raise ValidationError(

                    f"{field} is required."

                )

    @staticmethod
    def normalize_phone(
        data,
    ):

        phone = data["phone"]

        phone = phone.replace(" ", "")

        phone = phone.replace("-", "")

        if phone.startswith("09"):

            phone = "98" + phone[1:]

        elif phone.startswith("+98"):

            phone = "98" + phone[3:]

        data["phone"] = phone

    @staticmethod
    def normalize_strings(
        data,
    ):

        for key, value in data.items():

            if isinstance(value, str):

                data[key] = value.strip()

    @staticmethod
    def attach_request_metadata(
        data,
        request,
    ):

        if request is None:

            return

        data["client_ip"] = request.META.get(
            "REMOTE_ADDR"
        )

        data["user_agent"] = request.META.get(
            "HTTP_USER_AGENT"
        )

from django.core.validators import RegexValidator

iran_plate_validator = RegexValidator(
    regex=r"^\d{2}[آ-ی]\d{3}\d{2}$",
    message="فرمت پلاک صحیح نیست. مثال: 12ب34567"
)

def phone_validator(value):

    value = str(value).strip()

    # فقط عدد
    if not value.isdigit():
        raise ValidationError(
            "شماره تماس فقط باید شامل اعداد باشد."
        )

    # موبایل
    if value.startswith("09"):

        if len(value) != 11:
            raise ValidationError(
                "شماره موبایل باید 11 رقم باشد."
            )

        return

    # تلفن ثابت با کد شهر
    if value.startswith("0"):

        if len(value) < 10:
            raise ValidationError(
                "شماره تلفن ثابت با کد شهر معتبر نیست."
            )

        return

    # تلفن ثابت بدون کد شهر
    if len(value) < 8:

        raise ValidationError(
            "شماره تلفن ثابت باید حداقل 8 رقم باشد."
        )