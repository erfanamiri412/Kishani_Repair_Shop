from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from audit.models import AuditLog, CustomerPart, InventoryUsedPart, PurchasedPart
from crm.models import (
    Repair,
    InvoiceItem,
    InvoicePayment,
    RepairPart,
    RepairServiceItem,
)
from daily_activity.models import DailyExpense, DailyIncome
from users.models import SalaryPayment
from django.utils import timezone

from .analytics import AnalyticsService
from .periods import (
    JALALI_MONTH_NAMES,
    get_month_period,
    get_year_period,
    gregorian_to_jalali,
    jalali_month_label,
)

ZERO = Decimal("0")


class ChartsService:
    """Prepare data series with comparable units and readable time buckets."""

    @staticmethod
    def _value(value):
        try:
            return Decimal(str(value or 0))
        except Exception:
            return ZERO

    @staticmethod
    def _sum_by_date(queryset, date_getter, value_getter):
        totals = defaultdict(lambda: ZERO)
        for row in queryset:
            date_value = date_getter(row)
            if isinstance(date_value, datetime):
                if timezone.is_aware(date_value):
                    date_value = timezone.localtime(date_value).date()
                else:
                    date_value = date_value.date()
            if isinstance(date_value, date):
                totals[date_value] += ChartsService._value(value_getter(row))
        return totals

    @staticmethod
    def _monthly_keys(start_date, end_date):
        keys = []
        current = start_date
        while current <= end_date:
            year, month, _ = gregorian_to_jalali(current.year, current.month, current.day)
            if (year, month) not in keys:
                keys.append((year, month))
            month_start, _ = get_month_period(year, month)
            if month == 12:
                next_start, _ = get_month_period(year + 1, 1)
            else:
                next_start, _ = get_month_period(year, month + 1)
            if next_start <= current:
                break
            current = next_start
        return keys

    @staticmethod
    def _parts_cost_by_date(audit_rows):
        totals = defaultdict(lambda: ZERO)
        audit_by_id = {row.pk: row for row in audit_rows}
        if not audit_by_id:
            return totals

        # These are costs attached to a service report; stock usage is valued
        # at current purchase price only because historical purchase cost is
        # not stored on InventoryUsedPart.
        for row in PurchasedPart.objects.filter(audit_id__in=audit_by_id).select_related("audit"):
            day = getattr(row.audit, "service_date", None)
            if day:
                totals[day] += ChartsService._value(getattr(row, "total_price", 0))
        for row in InventoryUsedPart.objects.filter(audit_id__in=audit_by_id).select_related("audit", "part"):
            day = getattr(row.audit, "service_date", None)
            purchase_price = getattr(getattr(row, "part", None), "purchase_price", None)
            if day and purchase_price is not None:
                totals[day] += ChartsService._value(getattr(row, "quantity", 0)) * ChartsService._value(purchase_price)
        return totals

    @staticmethod
    def period_charts(start_date, end_date):
        if not start_date or not end_date or end_date < start_date:
            return {
                "daily_cashflow": [], "weekly_cashflow": [], "monthly_cashflow": [],
                "revenue_mix": [], "service_frequency": [], "mechanic_performance": [],
                "mechanic_hours": [], "top_parts": [], "vehicle_popularity": [],
                "top_customers": [], "expense_breakdown": [], "supplier_purchases": [],
            }

        daily_payments = AnalyticsService._period_qs(InvoicePayment, "paid_at", start_date, end_date, True)
        daily_income_qs = AnalyticsService._period_qs(DailyIncome, "income_date", start_date, end_date, False)
        daily_expense_qs = AnalyticsService._period_qs(DailyExpense, "expense_date", start_date, end_date, False)
        salary_qs = AnalyticsService._paid_salary_qs(start_date, end_date)

        payment_map = ChartsService._sum_by_date(daily_payments, lambda row: row.paid_at, lambda row: row.amount)
        income_map = ChartsService._sum_by_date(daily_income_qs, lambda row: row.income_date, lambda row: row.amount)
        expense_map = ChartsService._sum_by_date(daily_expense_qs, lambda row: row.expense_date, lambda row: row.amount)
        salary_map = ChartsService._sum_by_date(salary_qs, lambda row: row.payment_date, lambda row: row.amount)

        audit_rows = list(AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False))
        parts_cost_map = ChartsService._parts_cost_by_date(audit_rows)

        daily_cashflow = []
        current = start_date
        while current <= end_date:
            cash_collected = payment_map.get(current, ZERO)
            other_income = income_map.get(current, ZERO)
            expense = expense_map.get(current, ZERO) + salary_map.get(current, ZERO)
            income = cash_collected + other_income
            daily_cashflow.append({
                "date": current,
                "label": f"{gregorian_to_jalali(current.year, current.month, current.day)[2]:02d}",
                "cash_collected": cash_collected,
                "other_income": other_income,
                "income": income,
                "expense": expense,
                "known_parts_cost": parts_cost_map.get(current, ZERO),
                "net": income - expense,
            })
            current += timedelta(days=1)

        weekly_cashflow = []
        for offset in range(0, len(daily_cashflow), 7):
            chunk = daily_cashflow[offset:offset + 7]
            if not chunk:
                continue
            first = chunk[0]["date"]
            last = chunk[-1]["date"]
            start_day = gregorian_to_jalali(first.year, first.month, first.day)[2]
            end_day = gregorian_to_jalali(last.year, last.month, last.day)[2]
            weekly_cashflow.append({
                "label": f"{start_day:02d}–{end_day:02d}",
                "start_date": first,
                "end_date": last,
                "income": sum((row["income"] for row in chunk), ZERO),
                "expense": sum((row["expense"] for row in chunk), ZERO),
                "net": sum((row["net"] for row in chunk), ZERO),
            })

        monthly_cashflow = []
        for year, month in ChartsService._monthly_keys(start_date, end_date):
            month_start, month_end = get_month_period(year, month)
            month_start = max(month_start, start_date)
            month_end = min(month_end, end_date)
            rows = [row for row in daily_cashflow if month_start <= row["date"] <= month_end]
            monthly_cashflow.append({
                "year": year,
                "month": month,
                "label": JALALI_MONTH_NAMES[month - 1],
                "income": sum((row["income"] for row in rows), ZERO),
                "expense": sum((row["expense"] for row in rows), ZERO),
                "net": sum((row["net"] for row in rows), ZERO),
            })

        financial = AnalyticsService.get_financial_summary(start_date, end_date)
        revenue_mix = list(financial.get("revenue_by_type", []))
        if financial.get("other_income"):
            revenue_mix.append({
                "key": "other_income",
                "label": "سایر درآمدهای ثبت‌شده",
                "value": financial["other_income"],
                "count": financial.get("other_income_count", 0),
            })

        service_frequency = [
            {
                "service": row.get("service", "—"),
                "service_title": row.get("service", "—"),
                "count": row.get("count", 0),
                "amount": row.get("amount", ZERO),
                "source": row.get("source", "—"),
            }
            for row in AnalyticsService.get_top_services(start_date, end_date, limit=10)
        ]

        employees = AnalyticsService.get_employee_summary(start_date, end_date)
        mechanic_performance = sorted(
            [
                {
                    "employee": row["employee"],
                    "repairs": row["repair_count"],
                    "labor_income": row["labor_revenue"],
                    "attendance_hours": row["attendance_hours"],
                    "income_per_hour": row["labor_revenue_per_attendance_hour"],
                }
                for row in employees
            ],
            key=lambda row: row["labor_income"],
            reverse=True,
        )[:10]
        mechanic_hours = sorted(
            [{"employee": row["employee"], "hours": row["attendance_hours"], "repairs": row["repair_count"]} for row in employees],
            key=lambda row: row["hours"],
            reverse=True,
        )[:10]

        top_parts = defaultdict(lambda: {"quantity": 0, "source_set": set()})
        repair_part_keys = set()

        def normalize_part_name(value):
            return " ".join(str(value or "قطعه نامشخص").strip().casefold().split())

        # RepairPart.created_at marks when this individual part line was recorded.
        repair_parts = list(AnalyticsService._period_qs(RepairPart, "created_at", start_date, end_date, True).select_related("repair"))
        for row in repair_parts:
            name = str(getattr(row, "part_name", "قطعه نامشخص") or "قطعه نامشخص").strip()
            key = normalize_part_name(name)
            repair_part_keys.add((getattr(row, "repair_id", None), key))
            top_parts[name]["quantity"] += int(getattr(row, "quantity", 0) or 0)
            top_parts[name]["source_set"].add("قطعات ثبت‌شده روی تعمیر")

        # Legacy audit parts are used too, not only when the new repair table is
        # entirely empty. Where a linked repair already has the same named part,
        # prefer its RepairPart line to avoid counting the same usage twice.
        request_to_repair = {
            row.service_request_id: row.pk
            for row in Repair.objects.exclude(service_request__isnull=True).only("id", "service_request_id")
        }
        stock_used = InventoryUsedPart.objects.filter(audit__in=audit_rows).select_related("part", "audit")
        for row in stock_used:
            audit = getattr(row, "audit", None)
            repair_id = request_to_repair.get(getattr(audit, "service_request_id", None))
            part = getattr(row, "part", None)
            name = str(getattr(part, "title", "قطعه نامشخص") or "قطعه نامشخص").strip()
            if repair_id and (repair_id, normalize_part_name(name)) in repair_part_keys:
                continue
            top_parts[name]["quantity"] += int(getattr(row, "quantity", 0) or 0)
            top_parts[name]["source_set"].add("مصرف انبار در گزارش فعالیت")

        for model, name_field, source in (
            (PurchasedPart, "part_name", "قطعه خریداری‌شده برای تعمیر"),
            (CustomerPart, "part_name", "قطعه تأمین‌شده توسط مشتری"),
        ):
            for row in model.objects.filter(audit__in=audit_rows).select_related("audit"):
                audit = getattr(row, "audit", None)
                repair_id = request_to_repair.get(getattr(audit, "service_request_id", None))
                name = str(getattr(row, name_field, "قطعه نامشخص") or "قطعه نامشخص").strip()
                if repair_id and (repair_id, normalize_part_name(name)) in repair_part_keys:
                    continue
                top_parts[name]["quantity"] += int(getattr(row, "quantity", 0) or 0)
                top_parts[name]["source_set"].add(source)

        top_parts_data = []
        for name, values in top_parts.items():
            top_parts_data.append({
                "part": name,
                "quantity": values["quantity"],
                "source": "، ".join(sorted(values["source_set"])),
            })
        top_parts_data.sort(key=lambda row: row["quantity"], reverse=True)
        inventory = AnalyticsService.get_inventory_summary(start_date, end_date)
        return {
            "daily_cashflow": daily_cashflow,
            "weekly_cashflow": weekly_cashflow,
            "monthly_cashflow": monthly_cashflow,
            "revenue_mix": revenue_mix,
            "service_frequency": service_frequency,
            "mechanic_performance": mechanic_performance,
            "mechanic_hours": mechanic_hours,
            "top_parts": top_parts_data[:10],
            "vehicle_popularity": AnalyticsService.get_vehicle_summary(start_date, end_date),
            "top_customers": AnalyticsService.get_top_customers(start_date, end_date),
            "expense_breakdown": AnalyticsService.get_expense_breakdown(start_date, end_date),
            "supplier_purchases": inventory.get("top_suppliers", []),
        }

    @staticmethod
    def monthly_income_chart(year):
        start_date, end_date = get_year_period(year)
        return ChartsService.period_charts(start_date, end_date)["monthly_cashflow"]

    @staticmethod
    def monthly_profit_chart(year):
        start_date, end_date = get_year_period(year)
        return ChartsService.period_charts(start_date, end_date)["monthly_cashflow"]
