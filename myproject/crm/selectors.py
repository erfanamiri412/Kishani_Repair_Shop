from django.db.models import Sum
from django.db.models import Count

from crm.models import Customer

from .models import (
    Repair,
    Invoice,
    RepairPart,
)

def get_customer_dashboard(customer_id):
    """
    اطلاعات کامل داشبورد مشتری
    """

    return (

        Customer.objects

        .select_related()

        .prefetch_related(

            "segments",

            "crm_statuses",

            "followups",

            "reminders",

        )

        .get(

            id=customer_id

        )

    )


def get_customer_statistics():

    """
    آمار کلی CRM
    """

    return {

        "customers": Customer.objects.count()


    }

class RepairReportSelector:

    @classmethod
    def repairs_count(

        cls,

    ):

        return Repair.objects.count()
    
    @classmethod
    def total_revenue(

        cls,

    ):

        result = Invoice.objects.aggregate(

            total=Sum(

                "paid_amount"

            )

        )

        return result["total"] or 0
    
    @classmethod
    def total_debts(

        cls,

    ):

        total = 0

        for invoice in Invoice.objects.all():

            total += invoice.remaining_amount

        return total
    
    @classmethod
    def top_parts(

        cls,

    ):

        return (

            RepairPart.objects

            .values(

                "inventory_item__name"

            )

            .annotate(

                total=Sum(

                    "quantity"

                )

            )

            .order_by(

                "-total"

            )[:10]

        )
    
