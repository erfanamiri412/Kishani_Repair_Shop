from decimal import Decimal

from django.db.models import (
    Avg,
    Count,
    Q,
    Sum,
)

from audit.models import AuditLog


class EmployeePerformanceService:

    WEIGHTS = {

        "income": Decimal("35"),

        "repair_count": Decimal("15"),

        "satisfaction": Decimal("20"),

        "quality": Decimal("15"),

        "efficiency": Decimal("15"),

    }

    @classmethod
    def get_queryset(
        cls,
        employee,
        start_date,
        end_date,
    ):

        return AuditLog.objects.filter(
            mechanic=employee,
            service_date__range=(
                start_date,
                end_date,
            ),
        )

    @classmethod
    def calculate(
        cls,
        employee,
        start_date,
        end_date,
    ):

        queryset = cls.get_queryset(
            employee,
            start_date,
            end_date,
        )

        data = queryset.aggregate(

            repair_count=Count("id"),

            total_labor_income=Sum(
                "labor_total"
            ),

            average_labor_income=Avg(
                "labor_total"
            ),


            returned_repairs=Count(
                "id",
                filter=Q(
                    returned_for_repair=True
                ),
            ),
        )
        
        repair_count = (
            data["repair_count"] or 0
        )

        total_income = (
            data["total_labor_income"] or 0
        )

        average_income = (
            data["average_labor_income"] or 0
        )

        average_duration = (
            data["average_repair_duration"] or 0
        )

        income_score = cls._income_score(
            total_income
        )

        repair_count_score = cls._repair_count_score(
            repair_count
        )

        efficiency_score = cls._efficiency_score(
            average_duration
        )

        performance_score = (

            income_score *
            cls.WEIGHTS["income"] / 100

            +

            repair_count_score *
            cls.WEIGHTS["repair_count"] / 100

            +

            +

            +

            efficiency_score *
            cls.WEIGHTS["efficiency"] / 100

        )

        return {

            "repair_count": repair_count,

            "total_labor_income": int(
                total_income
            ),

            "average_labor_income": int(
                average_income
            ),

            "average_repair_duration": round(
                average_duration,
                2,
            ),

            "income_score": round(
                income_score,
                2,
            ),

            "repair_count_score": round(
                repair_count_score,
                2,
            ),

            "performance_score": round(
                performance_score,
                2,
            ),

            "performance_level":
                cls.performance_level(
                    performance_score
                ),

        }

    @staticmethod
    def _income_score(
        total_income
    ):

        if total_income <= 0:
            return Decimal("0")

        if total_income >= 200_000_000:
            return Decimal("100")

        return min(
            Decimal("100"),
            Decimal(total_income)
            / Decimal("2_000_000"),
        )

    @staticmethod
    def _repair_count_score(
        repair_count
    ):

        if repair_count <= 0:
            return Decimal("0")

        if repair_count >= 40:
            return Decimal("100")

        return min(
            Decimal("100"),
            Decimal(repair_count) *
            Decimal("2.5"),
        )

    @staticmethod
    def _efficiency_score(
        average_duration
    ):

        if not average_duration:
            return Decimal("0")

        if average_duration <= 120:
            return Decimal("100")

        if average_duration >= 600:
            return Decimal("20")

        score = (
            Decimal("100")
            -
            (
                Decimal(str(average_duration))
                - Decimal("120")
            )
            / Decimal("6")
        )

        return max(
            Decimal("20"),
            min(
                Decimal("100"),
                score,
            ),
        )

    @staticmethod
    def performance_level(
        score
    ):

        score = Decimal(str(score))

        if score >= 90:
            return "excellent"

        if score >= 75:
            return "good"

        if score >= 60:
            return "average"

        if score >= 40:
            return "weak"

        return "critical"