from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from audit.models import AuditLog, InventoryUsedPart, PurchasedPart
from crm.models import Invoice, InvoicePayment, Repair
from daily_activity.models import DailyIncome

from .analytics import AnalyticsService


class FinancialReportService:
    """Compatibility API backed by the central, consistently scoped analytics."""

    @staticmethod
    def _get_parts_cost(reports):
        external = PurchasedPart.objects.filter(audit__in=reports).aggregate(total=Sum("total_price"))["total"] or 0
        stock_rows = InventoryUsedPart.objects.filter(audit__in=reports).select_related("part")
        stock_cost = sum(
            Decimal(str(row.quantity or 0)) * Decimal(str(getattr(row.part, "purchase_price", 0) or 0))
            for row in stock_rows
        )
        return Decimal(str(external)) + stock_cost

    @staticmethod
    def get_total_income(start_date=None, end_date=None):
        return AnalyticsService.get_financial_summary(start_date, end_date)["cash_income"]

    @staticmethod
    def get_total_invoices(start_date=None, end_date=None):
        return AnalyticsService.get_financial_summary(start_date, end_date)["invoice_count"]

    @staticmethod
    def get_unpaid_amount():
        return AnalyticsService.get_financial_summary(None, timezone.localdate())["receivables"]

    @staticmethod
    def get_total_profit(start_date=None, end_date=None):
        return AnalyticsService.get_financial_summary(start_date, end_date)["management_profit"]

    @staticmethod
    def get_average_invoice_amount(start_date=None, end_date=None):
        return AnalyticsService.get_financial_summary(start_date, end_date)["average_invoice"]

    @staticmethod
    def get_repaired_vehicles_count(start_date=None, end_date=None):
        return AnalyticsService.get_operational_summary(start_date, end_date)["repairs"]

    @staticmethod
    def get_top_services(limit=10, start_date=None, end_date=None):
        return [
            {"service_type": row["service"], "count": row["count"], "amount": row["amount"], "source": row["source"]}
            for row in AnalyticsService.get_top_services(start_date, end_date, limit=limit)
        ]

    @staticmethod
    def get_monthly_income(year):
        from .charts import ChartsService
        from .periods import get_year_period
        start_date, end_date = get_year_period(year)
        return ChartsService.period_charts(start_date, end_date)["monthly_cashflow"]

    @staticmethod
    def get_daily_summary(report_date):
        repairs_received = Repair.objects.filter(created_at__date=report_date).count()
        delivered = Repair.objects.filter(delivered_at__date=report_date).count()
        in_progress = Repair.objects.filter(created_at__date__lte=report_date, delivered_at__isnull=True).count()
        invoice_payments = InvoicePayment.objects.filter(paid_at__date=report_date).aggregate(total=Sum("amount"))["total"] or 0
        other_income = DailyIncome.objects.filter(income_date=report_date).aggregate(total=Sum("amount"))["total"] or 0
        return {
            "vehicles_received": repairs_received,
            "vehicles_delivered": delivered,
            "vehicles_in_progress": in_progress,
            "daily_income": invoice_payments + other_income,
            "invoice_payments": invoice_payments,
            "other_income": other_income,
        }

    @staticmethod
    def financial_dashboard(start_date=None, end_date=None):
        summary = AnalyticsService.get_financial_summary(start_date, end_date)
        operations = AnalyticsService.get_operational_summary(start_date, end_date)
        return {
            "total_income": summary["cash_income"],
            "total_invoices": summary["invoice_count"],
            "unpaid_amount": summary["receivables"],
            "average_invoice_amount": summary["average_invoice"],
            "repaired_vehicles": operations["repairs"],
            "invoiced_revenue": summary["invoiced_revenue"],
            "cash_collected": summary["cash_collected"],
            "daily_expenses": summary["daily_expenses"],
            "salary_paid": summary["salary_paid"],
            "parts_cost": summary["parts_cost"],
            "estimated_operating_result": summary["management_profit"],
            "profit_definition": summary["profit_definition"],
        }
