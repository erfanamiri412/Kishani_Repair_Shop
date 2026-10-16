from users.models import EmployeeProfile

from .analytics import AnalyticsService


class EmployeeReportService:
    @staticmethod
    def _rows(start_date=None, end_date=None):
        return AnalyticsService.get_employee_summary(start_date, end_date)

    @staticmethod
    def _row_for(employee, start_date=None, end_date=None):
        for row in EmployeeReportService._rows(start_date, end_date):
            if row.get("employee_id") == getattr(employee, "pk", None):
                return row
        return {
            "employee_id": getattr(employee, "pk", None),
            "employee": str(employee),
            "repair_count": 0,
            "completed_repairs": 0,
            "labor_revenue": 0,
            "salary_paid": 0,
            "estimated_contribution_after_salary": 0,
            "customer_satisfaction": None,
            "returned_repairs": 0,
            "attendance_hours": 0,
        }

    @staticmethod
    def get_completed_repairs(employee, start_date=None, end_date=None):
        return EmployeeReportService._row_for(employee, start_date, end_date).get("repair_count", 0)

    @staticmethod
    def get_generated_revenue(employee, start_date=None, end_date=None):
        return EmployeeReportService._row_for(employee, start_date, end_date).get("labor_revenue", 0)

    @staticmethod
    def get_generated_profit(employee, start_date=None, end_date=None):
        # This is only labor revenue less recorded salary payments, not net profit.
        return EmployeeReportService._row_for(employee, start_date, end_date).get("estimated_contribution_after_salary", 0)

    @staticmethod
    def get_customer_satisfaction(employee):
        return EmployeeReportService._row_for(employee).get("customer_satisfaction")

    @staticmethod
    def get_returned_repairs(employee):
        return EmployeeReportService._row_for(employee).get("returned_repairs", 0)

    @staticmethod
    def get_employee_report(employee, start_date=None, end_date=None):
        row = EmployeeReportService._row_for(employee, start_date, end_date)
        return {
            "employee": row.get("employee", str(employee)),
            "completed_repairs": row.get("repair_count", 0),
            "repairs_participated": row.get("repair_count", 0),
            "generated_revenue": row.get("labor_revenue", 0),
            "generated_profit": row.get("estimated_contribution_after_salary", 0),
            "customer_satisfaction": row.get("customer_satisfaction"),
            "returned_repairs": row.get("returned_repairs", 0),
            "attendance_hours": row.get("attendance_hours", 0),
            "average_check_in": row.get("average_check_in", "—"),
            "average_check_out": row.get("average_check_out", "—"),
            "salary_paid": row.get("salary_paid", 0),
            "estimated_contribution_after_salary": row.get("estimated_contribution_after_salary", 0),
        }

    @staticmethod
    def get_employee_ranking(start_date=None, end_date=None):
        active_ids = set(EmployeeProfile.objects.filter(user__is_active=True).values_list("pk", flat=True))
        rows = [row for row in EmployeeReportService._rows(start_date, end_date) if row.get("employee_id") in active_ids]
        rows.sort(key=lambda row: (
            row.get("labor_revenue_per_attendance_hour") is not None,
            row.get("labor_revenue_per_attendance_hour") or 0,
            row.get("labor_revenue", 0),
        ), reverse=True)
        for row in rows:
            row["generated_revenue"] = row.get("labor_revenue", 0)
            row["generated_profit"] = row.get("estimated_contribution_after_salary", 0)
            row["completed_repairs"] = row.get("repair_count", 0)
        return rows

    @staticmethod
    def employee_dashboard(start_date=None, end_date=None):
        return EmployeeReportService.get_employee_ranking(start_date, end_date)
