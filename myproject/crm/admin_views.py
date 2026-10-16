from django.contrib.admin.views.autocomplete import (
    AutocompleteJsonView,
)

from .admin_utils import format_plate_text
from .models import CustomerVehicle


class KishaniAutocompleteJsonView(
    AutocompleteJsonView,
):

    def serialize_result(
        self,
        obj,
        to_field_name,
    ):

        if isinstance(
            obj,
            CustomerVehicle,
        ):

            text = (
                f"{obj.brand} "
                f"{obj.model}"
                f" | "
                f"{format_plate_text(obj.plate_number)}"
            )

        else:

            text = str(obj)


        return {
            "id": str(
                getattr(
                    obj,
                    to_field_name,
                )
            ),
            "text": text,
        }