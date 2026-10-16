from django import forms
from django.db.models import Q

from core.admin import (
    AdminTimeInput,
    BaseAdminForm,
)

from .models import (
    MaintenanceReminderType,
    MaintenanceRule,
)


class MaintenanceRuleAdminForm(BaseAdminForm):

    keywords_text = forms.CharField(
        required=False,
        label="کلیدواژه‌ها",
        help_text=(
            "با ویرگول جدا کنید؛ مثال: تعویض روغن, روغن موتور. "
            "برای تطبیق همه رویدادها از * استفاده کنید."
        ),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
    )

    class Meta:
        model = MaintenanceRule
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

        # ======================================================
        # Reminder Type
        # ======================================================

        current_type_id = getattr(
            self.instance,
            "reminder_type_id",
            None,
        )

        queryset = MaintenanceReminderType.objects.filter(
            is_active=True,
        )

        if current_type_id:
            queryset = MaintenanceReminderType.objects.filter(
                Q(is_active=True)
                | Q(pk=current_type_id),
            )

        self.fields[
            "reminder_type"
        ].queryset = queryset.order_by(
            "order",
            "title",
        )

        # ======================================================
        # Keywords
        # ======================================================

        self.fields[
            "keywords_text"
        ].initial = ", ".join(
            self.instance.keywords or []
        )

        # ======================================================
        # Time Picker
        # ======================================================

        for field_name in (
            "send_window_start",
            "send_window_end",
        ):

            field = self.fields[
                field_name
            ]

            field.widget = AdminTimeInput(
                attrs={
                    "class": (
                        "vTextField "
                        "admin-time-input"
                    ),
                    "autocomplete": "off",
                    "placeholder": "انتخاب زمان",
                    "data-time-picker": "true",
                    "style": (
                        "width:100%;"
                        "max-width:100%;"
                        "cursor:pointer;"
                    ),
                }
            )

    # ==========================================================
    # List Parser
    # ==========================================================

    @staticmethod
    def _parse_list(value):

        value = (
            value or ""
        ).strip()

        if not value:
            return []

        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    # ==========================================================
    # Clean
    # ==========================================================

    def clean(self):

        cleaned = super().clean()

        cleaned[
            "keywords"
        ] = self._parse_list(
            cleaned.pop(
                "keywords_text",
                "",
            )
        )

        return cleaned