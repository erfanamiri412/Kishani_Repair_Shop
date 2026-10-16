from django import forms

from core.admin import (
    AdminSplitJalaliDateTimeWithPicker,
    BaseAdminForm,
)
from jalali_date.fields import SplitJalaliDateTimeField

from .models import CommunicationTemplate, SmsCampaign


# ==========================================================
# Communication Template
# ==========================================================

class CommunicationTemplateAdminForm(BaseAdminForm):

    class Meta:
        model = CommunicationTemplate
        fields = "__all__"


# ==========================================================
# SMS Campaign
# ==========================================================

class SmsCampaignAdminForm(BaseAdminForm):

    scheduled_at = SplitJalaliDateTimeField(
        required=False,
        label="زمان ارسال",
        widget=AdminSplitJalaliDateTimeWithPicker,
    )

    class Meta:
        model = SmsCampaign
        fields = (
            "title",
            "body",
            "target_type",
            "customer",
            "selected_customers",
            "scheduled_at",
        )

    def clean(self):

        cleaned = super().clean()

        target_type = cleaned.get(
            "target_type"
        )

        customer = cleaned.get(
            "customer"
        )

        selected = cleaned.get(
            "selected_customers"
        )

        if (
            target_type ==
            SmsCampaign.TARGET_SINGLE
            and not customer
        ):

            self.add_error(
                "customer",
                "برای ارسال به یک مشتری، مشتری را انتخاب کنید.",
            )

        if (
            target_type ==
            SmsCampaign.TARGET_GROUP
            and not selected
        ):

            self.add_error(
                "selected_customers",
                "حداقل یک مشتری انتخاب کنید.",
            )

        if target_type == SmsCampaign.TARGET_ALL:

            cleaned["customer"] = None
            cleaned["selected_customers"] = []

        if target_type == SmsCampaign.TARGET_SINGLE:

            cleaned["selected_customers"] = []

        if target_type == SmsCampaign.TARGET_GROUP:

            cleaned["customer"] = None

        return cleaned