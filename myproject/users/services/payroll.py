from decimal import Decimal
from datetime import timedelta

from django.db.models import (
    Avg,
    Count,
    Sum,
)

from users.models import (
    EmployeeProfile,
    PayrollSnapshot,
    SalaryBonus,
    SalaryAdvance,
)

from audit.models import AuditLog


class PayrollService:

    """
    Single source of truth for payroll calculations.

    تمام محاسبات حقوق باید از این سرویس عبور کنند.
    """

    # ======================================================
    # Performance
    # ======================================================

    @staticmethod
    def calculate_performance(
        employee,
        start_date,
        end_date,
    ):

        queryset = AuditLog.objects.filter(
            mechanic=employee,
            service_date__range=(
                start_date,
                end_date,
            ),
        )

        aggregate = queryset.aggregate(
            repair_count=Count("id"),
            total_labor_income=Sum(
                "labor_total"
            ),
            average_labor_income=Avg(
                "labor_total"
            ),
            average_repair_duration=Avg(
                "total_repair_duration_minutes"
            ),
        )

        repair_count = (
            aggregate["repair_count"]
            or 0
        )

        total_labor_income = (
            aggregate["total_labor_income"]
            or 0
        )

        average_labor_income = int(
            aggregate["average_labor_income"]
            or 0
        )

        average_repair_duration = int(
            aggregate[
                "average_repair_duration"
            ]
            or 0
        )


        # --------------------------------------------------
        # Score 1: Income
        # --------------------------------------------------

        income_score = PayrollService._income_score(
            total_labor_income
        )

        # --------------------------------------------------
        # Score 2: Repair count
        # --------------------------------------------------

        repair_count_score = PayrollService._repair_count_score(
            repair_count
        )



        # --------------------------------------------------
        # Final weighted score
        # --------------------------------------------------

        performance_score = (
            income_score * Decimal("0.35")
            + repair_count_score * Decimal("0.20")
        )

        performance_score = min(
            max(
                performance_score,
                Decimal("0"),
            ),
            Decimal("100"),
        )

        performance_level = (
            PayrollService.performance_level(
                performance_score
            )
        )

        return {
            "repair_count": repair_count,
            "total_labor_income": int(
                total_labor_income
            ),
            "average_labor_income": (
                average_labor_income
            ),
            "average_repair_duration": (
                average_repair_duration
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
            "performance_level": (
                performance_level
            ),
        }

    @staticmethod
    def _income_score(
        income,
    ):

        """
        امتیاز درآمد فعلاً نسبت به سقف مرجع
        محاسبه می‌شود.

        این مقدار بعداً می‌تواند با
        historical benchmarking جایگزین شود.
        """

        if income <= 0:
            return Decimal("0")

        reference = Decimal(
            "50000000"
        )

        score = (
            Decimal(income)
            / reference
            * Decimal("100")
        )

        return min(
            score,
            Decimal("100"),
        )

    @staticmethod
    def _repair_count_score(
        repair_count,
    ):

        if repair_count <= 0:
            return Decimal("0")

        reference = Decimal("30")

        score = (
            Decimal(repair_count)
            / reference
            * Decimal("100")
        )

        return min(
            score,
            Decimal("100"),
        )

    @staticmethod
    def performance_level(
        score,
    ):

        score = Decimal(score)

        if score >= 80:
            return "excellent"

        if score >= 60:
            return "good"

        if score >= 40:
            return "average"

        return "weak"

    # ======================================================
    # Payroll
    # ======================================================

    @staticmethod
    def calculate_payroll(
        employee,
        start_date,
        end_date,
    ):

        performance = (
            PayrollService.calculate_performance(
                employee,
                start_date,
                end_date,
            )
        )

        # --------------------------------------------------
        # Fixed salary
        # --------------------------------------------------

        fixed_salary = 0
        commission_amount = 0

        if employee.payment_type == "fixed":

            fixed_salary = (
                PayrollService.calculate_fixed_salary(
                    employee,
                    start_date,
                    end_date,
                )
            )

        # --------------------------------------------------
        # Percentage employee
        # --------------------------------------------------

        elif employee.payment_type == "percentage":

            commission_amount = int(
                Decimal(
                    performance[
                        "total_labor_income"
                    ]
                )
                * (
                    employee.percentage_rate
                    / Decimal("100")
                )
            )

        # --------------------------------------------------
        # Bonuses
        # --------------------------------------------------

        bonus_amount = (
            SalaryBonus.objects.filter(
                employee=employee,
                date__range=(
                    start_date,
                    end_date,
                ),
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        # --------------------------------------------------
        # Outstanding salary advances
        # --------------------------------------------------

        advance_amount = (
            PayrollPaymentService
            .get_outstanding_advance_amount(
                employee
            )
        )

        # --------------------------------------------------
        # Gross payroll
        # --------------------------------------------------

        gross_amount = (
            fixed_salary
            + commission_amount
            + bonus_amount
        )

        # --------------------------------------------------
        # Net payable
        # --------------------------------------------------

        payable_amount = max(
            gross_amount
            - advance_amount,
            0,
        )

        return {
        **performance,

        "fixed_salary": fixed_salary,

        "commission_amount": commission_amount,

        "bonus_amount": bonus_amount,

        "advance_amount": advance_amount,

        "payable_amount": payable_amount,
    }

    @staticmethod
    def calculate_fixed_salary(
        employee,
        start_date,
        end_date,
    ):

        """
        حقوق ثابت بر اساس آخرین حقوق
        مؤثر در دوره محاسبه می‌شود.
        """

        revision = (
            employee.salary_revisions
            .filter(
                effective_date__lte=end_date
            )
            .order_by(
                "-effective_date",
                "-id",
            )
            .first()
        )

        if revision:
            return revision.new_salary

        return employee.fixed_salary

    # ======================================================
    # Snapshot
    # ======================================================

    @staticmethod
    def generate_snapshot(
        employee,
        start_date,
        end_date,
    ):

        data = PayrollService.calculate_payroll(
            employee,
            start_date,
            end_date,
        )

        snapshot, _ = (
            PayrollSnapshot.objects.update_or_create(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                defaults={
                    **data,
                    "status": "draft",
                },
            )
        )

        return snapshot

    # ======================================================
    # Batch
    # ======================================================

    @staticmethod
    def generate_for_all(
        start_date,
        end_date,
    ):

        employees = (
            EmployeeProfile.objects
            .filter(
                role="mechanic"
            )
            .select_related("user")
        )

        snapshots = []

        for employee in employees:

            snapshots.append(
                PayrollService.generate_snapshot(
                    employee,
                    start_date,
                    end_date,
                )
            )

        return snapshots

from django.db import transaction
from django.db.models import Sum

from users.models import (
    SalaryPayment,
    SalaryAdvance,
)


class PayrollPaymentService:

    """
    مدیریت پرداخت واقعی حقوق.

    هر پرداخت یک رکورد مستقل است.
    """

    # ======================================================
    # Payment Summary
    # ======================================================

    @staticmethod
    def get_payment_summary(
        payroll,
    ):

        paid_amount = (
            SalaryPayment.objects.filter(
                payroll=payroll,
                payment_status="confirmed",
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        remaining_amount = max(
            payroll.payable_amount
            - paid_amount,
            0,
        )

        return {
            "payable_amount": (
                payroll.payable_amount
            ),

            "paid_amount": paid_amount,

            "remaining_amount": (
                remaining_amount
            ),
        }

    # ======================================================
    # Create Payment
    # ======================================================

    @staticmethod
    @transaction.atomic
    def create_payment(
        payroll,
        amount,
        payment_date,
        description="",
    ):

        if amount <= 0:

            raise ValueError(
                "مبلغ پرداخت باید بیشتر از صفر باشد."
            )

        summary = (
            PayrollPaymentService
            .get_payment_summary(
                payroll
            )
        )

        remaining = summary[
            "remaining_amount"
        ]

        if amount > remaining:

            raise ValueError(
                "مبلغ پرداختی نمی‌تواند "
                "بیشتر از مبلغ باقی‌مانده حقوق باشد."
            )

        payment = SalaryPayment.objects.create(
            employee=payroll.employee,
            payroll=payroll,
            amount=amount,
            payment_date=payment_date,
            payment_status="confirmed",
            description=description,
        )

        PayrollPaymentService.refresh_payroll(
            payroll
        )

        return payment

    # ======================================================
    # Refresh Payroll
    # ======================================================

    @staticmethod
    @transaction.atomic
    def refresh_payroll(
        payroll,
    ):

        paid_amount = (
            SalaryPayment.objects.filter(
                payroll=payroll,
                payment_status="confirmed",
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        payroll.paid_amount = paid_amount

        if paid_amount >= payroll.payable_amount:

            payroll.status = "paid"

        elif paid_amount > 0:

            payroll.status = "approved"

        else:

            payroll.status = "draft"

        payroll.save(
            update_fields=[
                "paid_amount",
                "status",
                "updated_at",
            ]
        )

        return payroll

    # ======================================================
    # Cancel Payment
    # ======================================================

    @staticmethod
    @transaction.atomic
    def cancel_payment(
        payment,
    ):

        if payment.payment_status == "cancelled":

            return payment

        payment.payment_status = "cancelled"

        payment.save(
            update_fields=[
                "payment_status",
            ]
        )

        if payment.payroll_id:

            PayrollPaymentService.refresh_payroll(
                payment.payroll
            )

        return payment

    # ======================================================
    # Outstanding Advances
    # ======================================================

    @staticmethod
    def get_outstanding_advances(
        employee,
    ):

        return (
            SalaryAdvance.objects
            .filter(
                employee=employee,
                status__in=(
                    "open",
                    "partial",
                ),
            )
            .order_by(
                "date",
                "id",
            )
        )

    # ======================================================
    # Outstanding Advance Amount
    # ======================================================

    @staticmethod
    def get_outstanding_advance_amount(
        employee,
    ):

        advances = (
            PayrollPaymentService
            .get_outstanding_advances(
                employee
            )
        )

        return sum(
            advance.remaining_amount
            for advance in advances
        )

    # ======================================================
    # Apply Advance Repayment
    # ======================================================

    @staticmethod
    @transaction.atomic
    def apply_advance_repayment(
        employee,
        amount,
    ):

        if amount <= 0:

            return 0

        advances = (
            PayrollPaymentService
            .get_outstanding_advances(
                employee
            )
        )

        remaining_amount = amount

        for advance in advances:

            if remaining_amount <= 0:

                break

            outstanding = (
                advance.remaining_amount
            )

            repayment = min(
                outstanding,
                remaining_amount,
            )

            advance.paid_amount += repayment

            advance.refresh_status()

            remaining_amount -= repayment

        return (
            amount - remaining_amount
        )
