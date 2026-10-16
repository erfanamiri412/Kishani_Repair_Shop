from decimal import Decimal

from django.test import SimpleTestCase

from .ml_productions import MLProductionService
from .pdf_generator import PDFReportGenerator


class ForecastGuardTests(SimpleTestCase):
    def test_regression_refuses_fewer_than_three_periods(self):
        self.assertIsNone(MLProductionService._linear_regression([100, 200]))

    def test_income_forecast_refuses_sparse_history(self):
        history = [{"income": 100}, {"income": 0}, {"income": 250}, {"income": 0}, {"income": 0}]
        self.assertIsNone(MLProductionService.get_next_month_income_prediction(history))

    def test_income_forecast_accepts_three_positive_periods(self):
        history = [{"income": 100}, {"income": 200}, {"income": 300}, {"income": 400}]
        prediction = MLProductionService.get_next_month_income_prediction(history)
        self.assertIsInstance(prediction, Decimal)
        self.assertGreater(prediction, Decimal("0"))

    def test_annual_forecast_requires_three_positive_years(self):
        history = [
            {"year": 1401, "income": 100},
            {"year": 1402, "income": 0},
            {"year": 1403, "income": 250},
        ]
        self.assertIsNone(MLProductionService.get_next_year_income_prediction(1403, history))

    def test_annual_forecast_accepts_three_positive_years(self):
        history = [
            {"year": 1401, "income": 100},
            {"year": 1402, "income": 200},
            {"year": 1403, "income": 300},
        ]
        prediction = MLProductionService.get_next_year_income_prediction(1403, history)
        self.assertIsInstance(prediction, Decimal)
        self.assertGreater(prediction, Decimal("0"))

    def test_signed_chart_preserves_negative_values(self):
        generator = PDFReportGenerator.__new__(PDFReportGenerator)
        chart = generator._signed_bar_chart(
            [{"label": "هزینه خالص", "value": -120}, {"label": "مازاد", "value": 250}],
            "label",
            "value",
            "جریان خالص",
        )
        self.assertIn("<svg", chart)
        self.assertIn("#d95d39", chart)
        self.assertIn("#16836b", chart)

    def test_empty_chart_has_explanation(self):
        generator = PDFReportGenerator.__new__(PDFReportGenerator)
        chart = generator._horizontal_bar_chart([], "label", "value", "آزمون")
        self.assertIn("برای این دوره داده‌ای", chart)

class ChartReadabilityRegressionTests(SimpleTestCase):
    def setUp(self):
        self.generator = PDFReportGenerator.__new__(PDFReportGenerator)

    def test_horizontal_chart_uses_compact_viewbox_and_shows_large_values(self):
        svg = self.generator._horizontal_bar_chart(
            [{"employee": "حسین محمودی", "labor_income": 82_600_000}],
            "employee",
            "labor_income",
            "اجرت فاکتورشده",
            "money",
            6,
        )
        self.assertIn('viewBox="0 0 620', svg)
        self.assertIn("82.6م", svg)
        self.assertIn("حسین محمودی", svg)

    def test_vehicle_chart_uses_work_count_even_without_admission_count(self):
        charts = {
            "vehicle_popularity": [{"vehicle": "پراید", "repair_count": 0, "chart_count": 3}],
            "top_customers": [],
        }
        rendered = self.generator._build_chart_svgs({"charts": charts, "report_type": "monthly"})
        self.assertIn(">3<", rendered["vehicles"])

    def test_customer_chart_uses_resolved_frequency_count(self):
        charts = {
            "top_customers": [{"customer": "مشتری نمونه", "visit_count": 0, "repair_count": 0, "frequency_count": 4}],
        }
        rendered = self.generator._build_chart_svgs({"charts": charts, "report_type": "monthly"})
        self.assertIn(">4<", rendered["customers"])

    def test_zero_labor_is_not_reported_as_best_employee(self):
        from .analytics import AnalyticsService

        insights = AnalyticsService._build_insights(
            financial={},
            operations={},
            employees=[{
                "employee": "کارمند نمونه",
                "attendance_hours": 10.6,
                "labor_revenue": Decimal("0"),
                "labor_revenue_per_attendance_hour": 0,
                "repair_count": 0,
            }],
            top_customers=[],
            vehicles=[],
            services=[],
            inventory={},
            activity={"attendance_count": 1},
        )
        titles = {item["title"] for item in insights}
        self.assertIn("اجرت قابل انتساب نیست", titles)
        self.assertNotIn("بیشترین اجرت به ازای ساعت حضور", titles)
