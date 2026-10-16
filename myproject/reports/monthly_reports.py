from .analytics import AnalyticsService
from .charts import ChartsService
from .ml_productions import MLProductionService
from .periods import get_month_period, jalali_month_label


class MonthlyReportService:
    @staticmethod
    def generate(year, month):
        start_date, end_date = get_month_period(year, month)
        metrics = AnalyticsService.get_report_metrics(start_date, end_date)
        charts = ChartsService.period_charts(start_date, end_date)
        income_history = MLProductionService.get_income_history(year, month)

        prediction = MLProductionService.get_next_month_income_prediction(
            [{"income": value} for value in income_history]
        )
        parts_forecast = MLProductionService.predict_next_month_parts(year, month)
        growth = MLProductionService.monthly_growth(year, month)

        return {
            "report_type": "monthly",
            "year": year,
            "month": month,
            "month_label": jalali_month_label(year, month),
            "period_start": start_date,
            "period_end": end_date,
            "financial": metrics["financial"],
            "operations": metrics["operations"],
            "invoices": metrics["invoices"],
            "inventory": metrics["inventory"],
            "employees": metrics["employees"],
            "activity": metrics["activity"],
            "communications": metrics["communications"],
            "top_services": metrics["top_services"],
            "top_customers": metrics["top_customers"],
            "vehicles": metrics["vehicles"],
            "expense_breakdown": metrics["expense_breakdown"],
            "data_quality": metrics["data_quality"],
            "insights": metrics["insights"],
            "charts": charts,
            "ml": {
                "next_month_income_prediction": prediction,
                "parts_purchase_forecast": parts_forecast,
                "growth": growth,
                "history_months": len(income_history),
                "active_income_months": sum(1 for value in income_history if value),
            },
        }
