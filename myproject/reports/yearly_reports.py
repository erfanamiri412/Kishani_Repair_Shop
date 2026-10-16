from .analytics import AnalyticsService
from .charts import ChartsService
from .ml_productions import MLProductionService
from .periods import get_year_period, JALALI_MONTH_NAMES


class YearlyReportService:
    @staticmethod
    def generate(year):
        start_date, end_date = get_year_period(year)
        metrics = AnalyticsService.get_report_metrics(start_date, end_date)
        charts = ChartsService.period_charts(start_date, end_date)
        monthly_cashflow = charts.get("monthly_cashflow", [])
        monthly_data = []
        for item in monthly_cashflow:
            month_number = item.get("month", 0)
            label = JALALI_MONTH_NAMES[month_number - 1] if 1 <= month_number <= 12 else str(month_number)
            monthly_data.append({**item, "label": label, "index": month_number})

        annual_income_history = MLProductionService.get_annual_income_history(year)
        next_year_prediction = MLProductionService.get_next_year_income_prediction(
            year,
            history=annual_income_history,
        )

        return {
            "report_type": "yearly",
            "year": year,
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
            "monthly_data": monthly_data,
            "charts": charts,
            "ml": {
                "next_year_income_trend": MLProductionService.analyze_growth(monthly_cashflow),
                "next_year_income_prediction": next_year_prediction,
                "annual_income_history_years": len(annual_income_history),
            },
        }
