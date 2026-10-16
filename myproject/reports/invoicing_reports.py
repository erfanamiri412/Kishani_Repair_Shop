from django.db.models import Sum, Count
from crm.models import Invoice, InvoicePayment, InvoiceItem


class InvoiceReportsService:

    @staticmethod
    def financial_summary():

        invoices = Invoice.objects.all().prefetch_related(
            "items",
            "payments",
        )

        total_sales = sum(
            invoice.total_amount
            for invoice in invoices
        )

        total_receivables = sum(
            max(invoice.remaining_amount, 0)
            for invoice in invoices
        )

        total_paid = sum(
            invoice.paid_amount
            for invoice in invoices
        )

        return {

            "invoice_count": invoices.count(),

            "total_sales": total_sales,

            "total_paid": total_paid,

            "total_receivables": total_receivables,

            "average_invoice": (
                total_sales / invoices.count()
                if invoices.count()
                else 0
            ),
        }

    @staticmethod
    def invoice_status_statistics():

        result = {
            "paid": 0,
            "partial": 0,
            "pending": 0,
            "cancelled": 0,
        }

        invoices = Invoice.objects.all().prefetch_related(
            "items",
            "payments",
        )

        for invoice in invoices:

            if invoice.remaining_amount <= 0:
                result["paid"] += 1
            elif invoice.paid_amount > 0:
                result["partial"] += 1
            else:
                result["pending"] += 1

        return result

    @staticmethod
    def top_customers(limit=10):

        result = {}

        invoices = Invoice.objects.all().prefetch_related(
            "items",
            "payments",
        )

        for invoice in invoices:

            name = str(invoice.customer)

            if name not in result:
                result[name] = {
                    "customer": name,
                    "invoice_count": 0,
                    "paid_amount": 0,
                }

            result[name]["invoice_count"] += 1
            result[name]["paid_amount"] += invoice.paid_amount

        return sorted(
            result.values(),
            key=lambda item: item["paid_amount"],
            reverse=True,
        )[:limit]

    @staticmethod
    def payment_method_statistics():

        return InvoicePayment.objects.values(
            "payment_method"
        ).annotate(
            payment_count=Count("id"),
            total_amount=Sum("amount"),
        ).order_by(
            "-total_amount"
        )

    @staticmethod
    def warranty_invoices():

        return Invoice.objects.none()

    @staticmethod
    def debtors():

        result = []

        for invoice in Invoice.objects.all().prefetch_related(
            "items",
            "payments",
        ):

            if invoice.remaining_amount > 0:
                result.append(invoice)

        return result

    @staticmethod
    def monthly_statistics(year):

        data = []

        for month in range(1, 13):

            invoices = Invoice.objects.filter(
                issued_at__year=year,
                issued_at__month=month,
            ).prefetch_related(
                "items",
            )

            data.append({

                "month": month,

                "invoice_count": invoices.count(),

                "income": sum(
                    invoice.total_amount
                    for invoice in invoices
                ),
            })

        return data

    @staticmethod
    def invoice_dashboard():

        return {

            "financial":
                InvoiceReportsService.financial_summary(),

            "status":
                InvoiceReportsService.invoice_status_statistics(),

            "top_customers":
                InvoiceReportsService.top_customers(),

        }
