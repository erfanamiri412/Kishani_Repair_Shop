from decimal import Decimal
from math import ceil

from django.utils import timezone

from audit.models import InventoryUsedPart
from crm.models import RepairPart, InvoicePayment
from daily_activity.models import DailyIncome
from inventory.models import Part

from .periods import get_month_period, get_year_period, previous_jalali_month


class MLProductionService:
    """Conservative trend estimates; suppress forecasts when history is weak."""

    @staticmethod
    def _linear_regression(values):
        values = [float(value or 0) for value in values]
        if len(values) < 3:
            return None
        x_values = list(range(1, len(values) + 1))
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(values) / len(values)
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        if denominator == 0:
            return max(y_mean, 0.0)
        slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values)) / denominator
        prediction = slope * (len(values) + 1) + (y_mean - slope * x_mean)
        return max(prediction, 0.0)

    @staticmethod
    def _monthly_usage(part, year, month):
        start_date, end_date = get_month_period(year, month)
        usage = 0

        repair_parts = RepairPart.objects.filter(
            repair__created_at__date__gte=start_date,
            repair__created_at__date__lte=end_date,
        )
        try:
            RepairPart._meta.get_field("inventory_item")
            repair_parts = repair_parts.filter(inventory_item=part)
        except Exception:
            try:
                repair_parts = repair_parts.filter(part_name__iexact=part.title)
            except Exception:
                repair_parts = repair_parts.none()
        usage += sum(int(value or 0) for value in repair_parts.values_list("quantity", flat=True))

        try:
            legacy_parts = InventoryUsedPart.objects.filter(
                part=part,
                audit__service_date__gte=start_date,
                audit__service_date__lte=end_date,
            )
            usage += sum(int(value or 0) for value in legacy_parts.values_list("quantity", flat=True))
        except Exception:
            pass
        return usage

    @staticmethod
    def _history(part, year, month, periods=12):
        result = []
        current_year, current_month = year, month
        for index in range(periods):
            if index:
                current_year, current_month = previous_jalali_month(current_year, current_month)
            result.append(MLProductionService._monthly_usage(part, current_year, current_month))
        result.reverse()
        return result

    @staticmethod
    def predict_next_month_parts(year, month, limit=15):
        results = []
        for part in Part.objects.all():
            history = MLProductionService._history(part, year, month)
            active_months = sum(1 for value in history if value > 0)
            if active_months < 3:
                continue
            raw_prediction = MLProductionService._linear_regression(history)
            if raw_prediction is None:
                continue
            prediction = int(ceil(raw_prediction))
            minimum_stock = int(getattr(part, "minimum_stock", 0) or 0)
            current_stock = int(getattr(part, "stock", 0) or 0)
            target_stock = max(minimum_stock, prediction)
            recommended = max(0, target_stock - current_stock)
            if recommended <= 0:
                continue
            results.append({
                "part": part.title,
                "current_stock": current_stock,
                "minimum_stock": minimum_stock,
                "historical_usage": history,
                "active_months": active_months,
                "predicted_usage": prediction,
                "recommended_purchase": recommended,
                "confidence": "کم تا متوسط",
            })
        results.sort(key=lambda item: (item["recommended_purchase"], item["predicted_usage"]), reverse=True)
        return results[:limit]

    @staticmethod
    def get_income_history(year, month, periods=12):
        history = []
        current_year, current_month = year, month
        for _ in range(periods):
            start_date, end_date = get_month_period(current_year, current_month)
            payments = InvoicePayment.objects.filter(
                paid_at__date__gte=start_date,
                paid_at__date__lte=end_date,
            ).values_list("amount", flat=True)
            other_income = DailyIncome.objects.filter(
                income_date__gte=start_date,
                income_date__lte=end_date,
            ).values_list("amount", flat=True)
            history.append(sum((Decimal(str(value or 0)) for value in payments), Decimal("0")) + sum((Decimal(str(value or 0)) for value in other_income), Decimal("0")))
            current_year, current_month = previous_jalali_month(current_year, current_month)
        history.reverse()
        return history

    @staticmethod
    def monthly_growth(year, month):
        current_start, current_end = get_month_period(year, month)
        previous_year, previous_month = previous_jalali_month(year, month)
        previous_start, previous_end = get_month_period(previous_year, previous_month)

        def income(start_date, end_date):
            payments = InvoicePayment.objects.filter(paid_at__date__gte=start_date, paid_at__date__lte=end_date).values_list("amount", flat=True)
            other = DailyIncome.objects.filter(income_date__gte=start_date, income_date__lte=end_date).values_list("amount", flat=True)
            return sum((Decimal(str(value or 0)) for value in payments), Decimal("0")) + sum((Decimal(str(value or 0)) for value in other), Decimal("0"))

        current_income = income(current_start, current_end)
        previous_income = income(previous_start, previous_end)
        if previous_income:
            growth = (current_income - previous_income) / previous_income * 100
        else:
            growth = None if not current_income else Decimal("100")
        return {
            "growth_percent": round(float(growth), 2) if growth is not None else None,
            "current_income": current_income,
            "previous_income": previous_income,
            "trend": "insufficient_data" if growth is None else "up" if growth > 2 else "down" if growth < -2 else "stable",
        }

    @staticmethod
    def get_next_month_income_prediction(monthly_cashflow):
        values = [float(item.get("income", 0) or 0) for item in monthly_cashflow if isinstance(item, dict)]
        if len(values) < 3 or sum(1 for value in values if value > 0) < 3:
            return None
        prediction = MLProductionService._linear_regression(values[-6:])
        if prediction is None:
            return None
        return Decimal(str(round(prediction, 2)))

    @staticmethod
    def get_annual_income_history(year, periods=5):
        history = []
        first_year = year - periods + 1
        for current_year in range(first_year, year + 1):
            start_date, end_date = get_year_period(current_year)
            payments = InvoicePayment.objects.filter(
                paid_at__date__gte=start_date,
                paid_at__date__lte=end_date,
            ).values_list("amount", flat=True)
            other_income = DailyIncome.objects.filter(
                income_date__gte=start_date,
                income_date__lte=end_date,
            ).values_list("amount", flat=True)
            amount = sum((Decimal(str(value or 0)) for value in payments), Decimal("0"))
            amount += sum((Decimal(str(value or 0)) for value in other_income), Decimal("0"))
            history.append({"year": current_year, "income": amount})
        return history

    @staticmethod
    def get_next_year_income_prediction(year, history=None):
        history = history if history is not None else MLProductionService.get_annual_income_history(year)
        if history:
            try:
                last_recorded_year = int(history[-1].get("year"))
                _, last_recorded_period_end = get_year_period(last_recorded_year)
                if last_recorded_period_end > timezone.localdate():
                    return None
            except (AttributeError, TypeError, ValueError):
                return None
        values = [float(row.get("income", 0) or 0) for row in history if isinstance(row, dict)]
        if len(values) < 3 or sum(1 for value in values if value > 0) < 3:
            return None
        prediction = MLProductionService._linear_regression(values[-5:])
        if prediction is None:
            return None
        return Decimal(str(round(prediction, 2)))

    @staticmethod
    def analyze_growth(monthly_cashflow):
        if len(monthly_cashflow) < 3:
            return {"growth_percent": None, "trend": "insufficient_data"}
        values = [float(item.get("income", 0) or 0) for item in monthly_cashflow[-3:]]
        if sum(1 for value in values if value > 0) < 2:
            return {"growth_percent": None, "trend": "insufficient_data"}
        current, previous = values[-1], values[-2]
        if previous == 0:
            growth = 100 if current > 0 else 0
        else:
            growth = (current - previous) / previous * 100
        trend = "up" if growth > 2 else "down" if growth < -2 else "stable"
        return {"growth_percent": round(growth, 2), "trend": trend}
