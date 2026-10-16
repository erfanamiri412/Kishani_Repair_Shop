from collections import defaultdict
from datetime import datetime, time
from decimal import Decimal

from django.core.exceptions import FieldError
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from audit.models import (
    AuditLog,
    CustomerPart,
    InventoryUsedPart,
    PurchasedPart,
)
from crm.models import (
    Customer,
    CustomerServiceRequest,
    CustomerVehicle,
    Invoice,
    InvoiceItem,
    InvoicePayment,
    Repair,
    RepairPart,
    RepairServiceItem,
)
from daily_activity.models import (
    Attendance,
    DailyExpense,
    DailyIncome,
    DailyNote,
)
from inventory.models import Part, PartCategory, Supplier
from users.models import (
    EmployeeProfile,
    PayrollSnapshot,
    SalaryAdvance,
    SalaryBonus,
    SalaryPayment,
)

try:
    from crm.models import CustomerVisit
except ImportError:  # Older installations may not have a visit register.
    CustomerVisit = None

try:
    from communications.models import CommunicationLog
except ImportError:
    CommunicationLog = None

ZERO = Decimal("0")
MONEY_FIELD_CANDIDATES = (
    "amount", "total_price", "unit_price", "purchase_price",
    "sale_price", "fixed_salary", "paid_amount", "total_labor_income",
)


class AnalyticsService:
    """Business reporting built from the shop's source records.

    Revenue from invoices, money collected, operating expenses and estimated
    cost of parts are reported separately so different accounting bases are
    never silently added together.
    """

    @staticmethod
    def _has_field(model, name):
        try:
            model._meta.get_field(name)
            return True
        except Exception:
            return False

    @staticmethod
    def _safe_filter(queryset, **kwargs):
        try:
            return queryset.filter(**kwargs)
        except (FieldError, TypeError, ValueError):
            return queryset.none()

    @staticmethod
    def _date_range(queryset, field, start_date, end_date, datetime_field=None):
        if not start_date and not end_date:
            return queryset
        try:
            if datetime_field is None:
                model = queryset.model
                current_model = model
                field_obj = None
                for part in field.split("__"):
                    if part in {"exact", "gte", "lte", "gt", "lt", "date"}:
                        break
                    field_obj = current_model._meta.get_field(part)
                    if getattr(field_obj, "is_relation", False) and getattr(field_obj, "related_model", None):
                        current_model = field_obj.related_model
                datetime_field = bool(field_obj and field_obj.get_internal_type() == "DateTimeField")
            suffix = "__date" if datetime_field else ""
            filters = {}
            if start_date:
                filters[f"{field}{suffix}__gte"] = start_date
            if end_date:
                filters[f"{field}{suffix}__lte"] = end_date
            return queryset.filter(**filters)
        except (FieldError, TypeError, ValueError, LookupError):
            return queryset.none()

    @staticmethod
    def _sum(queryset, field):
        try:
            return queryset.aggregate(total=Sum(field)).get("total") or ZERO
        except (FieldError, TypeError, ValueError):
            return ZERO

    @staticmethod
    def _item_total(items):
        total = ZERO
        for item in items:
            try:
                total += Decimal(str(item.quantity or 0)) * Decimal(str(item.unit_price or 0))
            except Exception:
                continue
        return total

    @staticmethod
    def _choices_map(model, field_name):
        try:
            return dict(model._meta.get_field(field_name).choices or [])
        except Exception:
            return {}

    @staticmethod
    def _cash(value):
        try:
            return Decimal(str(value or 0))
        except Exception:
            return ZERO

    @staticmethod
    def _period_qs(model, field, start_date, end_date, datetime_field=None):
        return AnalyticsService._date_range(model.objects.all(), field, start_date, end_date, datetime_field)

    @staticmethod
    def _repair_activity_qs(start_date, end_date):
        """Repairs created or delivered in the selected period, without duplicates."""
        created = AnalyticsService._period_qs(Repair, "created_at", start_date, end_date, True)
        if AnalyticsService._has_field(Repair, "delivered_at"):
            delivered = AnalyticsService._period_qs(Repair, "delivered_at", start_date, end_date, True)
            return (created | delivered).distinct()
        return created.distinct()

    @staticmethod
    def _vehicle_label(vehicle, fallback=""):
        if vehicle is not None:
            parts = [getattr(vehicle, key, "") for key in ("company", "brand", "model")]
            label = " ".join(str(value).strip() for value in parts if value is not None and str(value).strip())
            if label:
                return label
            return str(vehicle).strip() or "خودرو نامشخص"
        return str(fallback or "خودرو نامشخص").strip()

    @staticmethod
    def _paid_salary_qs(start_date, end_date):
        queryset = AnalyticsService._period_qs(SalaryPayment, "payment_date", start_date, end_date, False)
        if AnalyticsService._has_field(SalaryPayment, "payment_status"):
            queryset = queryset.filter(payment_status__in=("partial", "paid"))
        return queryset

    @staticmethod
    def _invoice_total(invoice, payment_cutoff=None):
        items = list(invoice.items.all())
        total = AnalyticsService._item_total(items)
        payments = list(invoice.payments.all())
        paid = ZERO
        for payment in payments:
            paid_at = getattr(payment, "paid_at", None)
            if payment_cutoff and paid_at:
                try:
                    if isinstance(paid_at, datetime) and timezone.is_aware(paid_at):
                        paid_day = timezone.localtime(paid_at).date()
                    elif isinstance(paid_at, datetime):
                        paid_day = paid_at.date()
                    else:
                        paid_day = paid_at
                except (AttributeError, TypeError, ValueError):
                    paid_day = paid_at
                if paid_day > payment_cutoff:
                    continue
            paid += AnalyticsService._cash(getattr(payment, "amount", 0))
        return total, paid

    @staticmethod
    def get_financial_summary(start_date, end_date):
        invoices = AnalyticsService._period_qs(Invoice, "issued_at", start_date, end_date, True)
        invoice_items = InvoiceItem.objects.filter(invoice__in=invoices).select_related("invoice__repair")
        invoice_items_list = list(invoice_items)
        invoiced_revenue = AnalyticsService._item_total(invoice_items_list)

        item_totals = defaultdict(lambda: ZERO)
        item_counts = defaultdict(int)
        item_quantities = defaultdict(int)
        for item in invoice_items_list:
            code = getattr(item, "item_type", "other") or "other"
            item_totals[code] += AnalyticsService._cash(item.quantity) * AnalyticsService._cash(item.unit_price)
            item_counts[code] += 1
            item_quantities[code] += int(getattr(item, "quantity", 0) or 0)

        payments = AnalyticsService._period_qs(InvoicePayment, "paid_at", start_date, end_date, True)
        cash_collected = AnalyticsService._sum(payments, "amount")
        other_income_qs = AnalyticsService._period_qs(DailyIncome, "income_date", start_date, end_date, False)
        other_income = AnalyticsService._sum(other_income_qs, "amount")
        expenses_qs = AnalyticsService._period_qs(DailyExpense, "expense_date", start_date, end_date, False)
        daily_expenses = AnalyticsService._sum(expenses_qs, "amount")
        salaries_qs = AnalyticsService._paid_salary_qs(start_date, end_date)
        salary_paid = AnalyticsService._sum(salaries_qs, "amount")
        bonuses_qs = AnalyticsService._period_qs(SalaryBonus, "date", start_date, end_date, False)
        bonus_accrued = AnalyticsService._sum(bonuses_qs, "amount")

        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False)
        supplier_parts = AnalyticsService._safe_filter(PurchasedPart.objects.all(), audit__in=audit_rows)
        external_parts_cost = AnalyticsService._sum(supplier_parts, "total_price")

        stock_used = AnalyticsService._safe_filter(InventoryUsedPart.objects.all(), audit__in=audit_rows).select_related("part")
        estimated_stock_cogs = ZERO
        for row in stock_used:
            purchase_price = getattr(getattr(row, "part", None), "purchase_price", None)
            if purchase_price is None:
                # Historical cost is not saved on this usage record. Do not
                # silently use total_price because it is set from sale_price.
                continue
            estimated_stock_cogs += AnalyticsService._cash(row.quantity) * AnalyticsService._cash(purchase_price)

        recorded_parts_cost = external_parts_cost + estimated_stock_cogs
        recorded_costs = daily_expenses + salary_paid + recorded_parts_cost
        other_accrual_income = invoiced_revenue + other_income
        estimated_operating_result = other_accrual_income - recorded_costs
        cash_income = cash_collected + other_income
        recorded_cash_outflow = daily_expenses + salary_paid
        cash_surplus = cash_income - recorded_cash_outflow

        invoices_as_of_end = Invoice.objects.all()
        try:
            if end_date:
                invoices_as_of_end = invoices_as_of_end.filter(issued_at__date__lte=end_date)
            elif end_date is None:
                pass
        except (FieldError, TypeError, ValueError):
            invoices_as_of_end = Invoice.objects.none()
        invoices_as_of_end = invoices_as_of_end.prefetch_related("items", "payments")
        receivables = ZERO
        for invoice in invoices_as_of_end:
            total, paid_through_end = AnalyticsService._invoice_total(invoice, payment_cutoff=end_date)
            receivables += max(total - paid_through_end, ZERO)

        invoice_count = invoices.count()
        choice_titles = AnalyticsService._choices_map(InvoiceItem, "item_type")
        revenue_by_type = [
            {
                "key": key,
                "label": choice_titles.get(key, key.replace("_", " ").title()),
                "value": value,
                "count": item_counts[key],
                "quantity": item_quantities[key],
            }
            for key, value in item_totals.items()
            if value != 0 or item_counts[key]
        ]
        revenue_by_type.sort(key=lambda row: row["value"], reverse=True)

        payment_method_titles = AnalyticsService._choices_map(InvoicePayment, "payment_method")
        payment_methods = defaultdict(lambda: {"count": 0, "amount": ZERO})
        for payment in payments:
            key = getattr(payment, "payment_method", "other") or "other"
            payment_methods[key]["count"] += 1
            payment_methods[key]["amount"] += AnalyticsService._cash(getattr(payment, "amount", 0))
        payment_method_rows = [
            {"key": key, "label": payment_method_titles.get(key, key), **values}
            for key, values in payment_methods.items()
        ]
        payment_method_rows.sort(key=lambda row: row["amount"], reverse=True)

        invoice_status = {"paid": 0, "partial": 0, "pending": 0, "empty": 0}
        invoices_in_period = invoices.prefetch_related("items", "payments")
        for invoice in invoices_in_period:
            total, paid = AnalyticsService._invoice_total(invoice, payment_cutoff=end_date)
            if total <= 0:
                invoice_status["empty"] += 1
            elif paid >= total:
                invoice_status["paid"] += 1
            elif paid > 0:
                invoice_status["partial"] += 1
            else:
                invoice_status["pending"] += 1

        revenue_total = invoiced_revenue + other_income
        margin = (estimated_operating_result / revenue_total * 100) if revenue_total else None
        purchase_data_available = supplier_parts.exists() or stock_used.exists()

        return {
            # Legacy aliases retained for existing admin tools/templates.
            "invoice_amount": invoiced_revenue,
            "total_income": revenue_total,
            "cash_income": cash_income,
            "cash_collected": cash_collected,
            "other_income": other_income,
            "invoiced_revenue": invoiced_revenue,
            "daily_expenses": daily_expenses,
            "salary_paid": salary_paid,
            "bonus_accrued": bonus_accrued,
            "parts_cost": recorded_parts_cost,
            "external_parts_cost": external_parts_cost,
            "estimated_stock_cogs": estimated_stock_cogs,
            "cash_outflow": recorded_cash_outflow,
            "cashflow": cash_surplus,
            "cash_surplus": cash_surplus,
            "management_profit": estimated_operating_result,
            "estimated_operating_result": estimated_operating_result,
            "profit_margin_percent": round(float(margin), 2) if margin is not None else None,
            "receivables": receivables,
            "invoice_count": invoice_count,
            "payment_count": payments.count(),
            "average_invoice": invoiced_revenue / invoice_count if invoice_count else None,
            "revenue_by_type": revenue_by_type,
            "payment_methods": payment_method_rows,
            "invoice_status": invoice_status,
            "daily_expense_count": expenses_qs.count(),
            "salary_payment_count": salaries_qs.count(),
            "other_income_count": other_income_qs.count(),
            "supplier_purchase_records": supplier_parts.count(),
            "has_recorded_parts_cost_data": purchase_data_available,
            "profit_definition": (
                "درآمد فاکتورهای صادرشده + سایر درآمدهای ثبت‌شده، منهای هزینه‌های روزانه، حقوق پرداخت‌شده، "
                "خرید قطعات ثبت‌شده برای تعمیر و برآورد بهای خرید قطعات انبار مصرف‌شده. این شاخص برآورد مدیریتی است؛ "
                "خرید تاریخی انبار و سربار ثبت‌نشده را پوشش نمی‌دهد."
            ),
        }

    @staticmethod
    def get_operational_summary(start_date, end_date):
        requests = AnalyticsService._period_qs(CustomerServiceRequest, "created_at", start_date, end_date, True)
        new_customers = AnalyticsService._period_qs(Customer, "created_at", start_date, end_date, True)
        new_vehicles = AnalyticsService._period_qs(CustomerVehicle, "created_at", start_date, end_date, True)
        repairs_created = AnalyticsService._period_qs(Repair, "created_at", start_date, end_date, True)
        repairs_active = AnalyticsService._repair_activity_qs(start_date, end_date)
        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False)

        delivered_count = 0
        if AnalyticsService._has_field(Repair, "delivered_at"):
            delivered_count = AnalyticsService._period_qs(Repair, "delivered_at", start_date, end_date, True).count()
        elif AnalyticsService._has_field(Repair, "status"):
            status_titles = AnalyticsService._choices_map(Repair, "status")
            completed_values = [key for key, title in status_titles.items() if any(term in str(title).lower() for term in ("تکمیل", "تحویل", "complete", "deliver"))]
            if completed_values:
                delivered_count = AnalyticsService._safe_filter(repairs_created, status__in=completed_values).count()

        open_as_of_end = 0
        if AnalyticsService._has_field(Repair, "delivered_at") and end_date:
            try:
                open_as_of_end = Repair.objects.filter(created_at__date__lte=end_date).filter(
                    delivered_at__isnull=True
                ).count() + Repair.objects.filter(
                    created_at__date__lte=end_date,
                    delivered_at__date__gt=end_date,
                ).count()
            except (FieldError, TypeError, ValueError):
                open_as_of_end = 0

        visits_count = 0
        if CustomerVisit is not None:
            visits = AnalyticsService._period_qs(CustomerVisit, "arrived_at", start_date, end_date, True)
            if AnalyticsService._has_field(CustomerVisit, "status"):
                visits = visits.exclude(status="cancelled")
            visits_count = visits.count()

        return {
            "service_requests": requests.count(),
            "new_customers": new_customers.count(),
            "new_vehicles": new_vehicles.count(),
            "repairs": repairs_created.count(),
            "repairs_active": repairs_active.count(),
            "completed_repairs": delivered_count,
            "delivered_repairs": delivered_count,
            "open_repairs_as_of_end": open_as_of_end,
            "legacy_activity_records": audit_rows.count(),
            "customer_visits": visits_count,
            "repair_part_lines": AnalyticsService._period_qs(RepairPart, "created_at", start_date, end_date, True).count(),
            "repair_service_lines": AnalyticsService._period_qs(RepairServiceItem, "created_at", start_date, end_date, True).count(),
        }

    @staticmethod
    def get_invoice_summary(start_date, end_date):
        invoices = AnalyticsService._period_qs(Invoice, "issued_at", start_date, end_date, True).prefetch_related("items", "payments")
        rows = list(invoices)
        total_amount = ZERO
        for invoice in rows:
            amount, _ = AnalyticsService._invoice_total(invoice, payment_cutoff=end_date)
            total_amount += amount

        items = InvoiceItem.objects.filter(invoice__in=rows)
        item_types = AnalyticsService._choices_map(InvoiceItem, "item_type")
        by_type = {}
        for key, title in item_types.items():
            typed = list(items.filter(item_type=key))
            by_type[key] = {
                "title": title,
                "count": len(typed),
                "quantity": sum(int(getattr(row, "quantity", 0) or 0) for row in typed),
                "amount": AnalyticsService._item_total(typed),
            }

        payment_status = {"paid": 0, "partial": 0, "pending": 0, "empty": 0}
        for invoice in rows:
            total, paid = AnalyticsService._invoice_total(invoice, payment_cutoff=end_date)
            if total <= 0:
                payment_status["empty"] += 1
            elif paid >= total:
                payment_status["paid"] += 1
            elif paid > 0:
                payment_status["partial"] += 1
            else:
                payment_status["pending"] += 1

        return {
            "count": len(rows),
            "total_amount": total_amount,
            "items_by_type": by_type,
            "status": payment_status,
            "payments_count": sum(len(list(inv.payments.all())) for inv in rows),
        }

    @staticmethod
    def get_inventory_summary(start_date, end_date):
        parts = list(Part.objects.all().select_related("supplier"))
        stock_units = sum(int(getattr(part, "stock", 0) or 0) for part in parts)
        current_purchase_value = sum(
            Decimal(str(getattr(part, "stock", 0) or 0)) * Decimal(str(getattr(part, "purchase_price", 0) or 0))
            for part in parts
        )
        sale_value = sum(
            Decimal(str(getattr(part, "stock", 0) or 0)) * Decimal(str(getattr(part, "sale_price", 0) or 0))
            for part in parts
        )
        low_stock_parts = [
            {
                "part": getattr(part, "title", str(part)),
                "stock": int(getattr(part, "stock", 0) or 0),
                "minimum_stock": int(getattr(part, "minimum_stock", 0) or 0),
                "supplier": str(getattr(part, "supplier", "") or "—"),
            }
            for part in parts
            if int(getattr(part, "stock", 0) or 0) <= int(getattr(part, "minimum_stock", 0) or 0)
        ]
        low_stock_parts.sort(key=lambda row: (row["stock"] - row["minimum_stock"], row["part"]))

        repair_parts = AnalyticsService._period_qs(RepairPart, "created_at", start_date, end_date, True)
        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False)
        stock_used = AnalyticsService._safe_filter(InventoryUsedPart.objects.all(), audit__in=audit_rows)
        supplier_parts = AnalyticsService._safe_filter(PurchasedPart.objects.all(), audit__in=audit_rows).select_related("supplier")
        customer_parts = AnalyticsService._safe_filter(CustomerPart.objects.all(), audit__in=audit_rows)

        # Purchases in this model are attached to service records. Their date
        # is service_date, not a dedicated procurement/payment timestamp.
        supplier_totals = defaultdict(lambda: {"amount": ZERO, "quantity": 0, "lines": 0})
        for row in supplier_parts:
            supplier = str(getattr(row, "supplier", None) or "تأمین‌کننده نامشخص")
            supplier_totals[supplier]["amount"] += AnalyticsService._cash(getattr(row, "total_price", 0))
            supplier_totals[supplier]["quantity"] += int(getattr(row, "quantity", 0) or 0)
            supplier_totals[supplier]["lines"] += 1
        top_suppliers = [
            {"supplier": name, **values}
            for name, values in supplier_totals.items()
        ]
        top_suppliers.sort(key=lambda row: row["amount"], reverse=True)

        stock_by_supplier = defaultdict(lambda: {"stock_units": 0, "current_purchase_value": ZERO})
        for part in parts:
            supplier = str(getattr(part, "supplier", None) or "تأمین‌کننده نامشخص")
            stock_by_supplier[supplier]["stock_units"] += int(getattr(part, "stock", 0) or 0)
            stock_by_supplier[supplier]["current_purchase_value"] += Decimal(str(getattr(part, "stock", 0) or 0)) * Decimal(str(getattr(part, "purchase_price", 0) or 0))
        current_stock_by_supplier = [
            {"supplier": name, **values}
            for name, values in stock_by_supplier.items()
        ]
        current_stock_by_supplier.sort(key=lambda row: row["current_purchase_value"], reverse=True)

        return {
            "part_count": len(parts),
            "category_count": len({str(getattr(part, "category", "") or "بدون دسته‌بندی").strip() for part in parts}),
            "supplier_count": Supplier.objects.count(),
            "stock_units": stock_units,
            "purchase_value": current_purchase_value,
            "sale_value": sale_value,
            "potential_profit": sale_value - current_purchase_value,
            "low_stock": len(low_stock_parts),
            "low_stock_parts": low_stock_parts[:15],
            "repair_part_lines": repair_parts.count(),
            "inventory_part_lines": stock_used.count(),
            "purchased_part_lines": supplier_parts.count(),
            "customer_part_lines": customer_parts.count(),
            "purchased_part_cost": AnalyticsService._sum(supplier_parts, "total_price"),
            "top_suppliers": top_suppliers[:10],
            "current_stock_by_supplier": current_stock_by_supplier[:10],
            "snapshot_note": "ارزش موجودی، وضعیت فعلی انبار در زمان تولید گزارش است؛ از آن نمی‌توان موجودی تاریخی پایان دوره را نتیجه گرفت.",
            "purchase_date_note": "سوابق قطعات خریداری‌شده به تاریخ خدمت گزارش‌شده متصل‌اند؛ تا زمانی که تاریخ مستقل خرید ثبت نشود، رتبه تأمین‌کننده بر مبنای همین تاریخ قابل مشاهده است.",
        }

    @staticmethod
    def _time_average(times):
        minutes = []
        for value in times:
            if isinstance(value, time):
                minutes.append(value.hour * 60 + value.minute + value.second / 60)
            elif isinstance(value, datetime):
                minutes.append(value.hour * 60 + value.minute + value.second / 60)
        if not minutes:
            return None
        mean = int(round(sum(minutes) / len(minutes))) % (24 * 60)
        return f"{mean // 60:02d}:{mean % 60:02d}"

    @staticmethod
    def _attendance_duration(record):
        status = getattr(record, "status", "present")
        if status not in ("present", "late", "half_day"):
            return 0.0
        check_in = getattr(record, "check_in", None)
        check_out = getattr(record, "check_out", None)
        if not check_in or not check_out:
            return 0.0
        start = check_in.hour * 3600 + check_in.minute * 60 + check_in.second
        end = check_out.hour * 3600 + check_out.minute * 60 + check_out.second
        if end < start:
            end += 24 * 3600
        return max((end - start) / 3600, 0.0)

    @staticmethod
    def get_employee_summary(start_date, end_date):
        employees = list(EmployeeProfile.objects.select_related("user").all())
        rows = {
            employee.pk: {
                "employee_id": employee.pk,
                "employee": str(employee),
                "role": getattr(employee, "get_role_display", lambda: getattr(employee, "role", "—"))(),
                "repair_ids": set(),
                "attendance_hours": 0.0,
                "attendance_days": 0,
                "present_days": 0,
                "absent_days": 0,
                "late_days": 0,
                "leave_days": 0,
                "check_ins": [],
                "check_outs": [],
                "recorded_repair_hours": 0.0,
                "audit_activity_count": 0,
                "labor_revenue": ZERO,
                "salary_paid": ZERO,
                "customer_satisfaction": None,
                "returned_repairs": 0,
            }
            for employee in employees
        }

        attendance_qs = AnalyticsService._period_qs(Attendance, "date", start_date, end_date, False).select_related("employee")
        for attendance in attendance_qs:
            employee_id = getattr(attendance, "employee_id", None)
            if employee_id not in rows:
                continue
            row = rows[employee_id]
            row["attendance_days"] += 1
            row["attendance_hours"] += AnalyticsService._attendance_duration(attendance)
            status = getattr(attendance, "status", "")
            if status in ("present", "late", "half_day"):
                row["present_days"] += 1
                if getattr(attendance, "check_in", None):
                    row["check_ins"].append(attendance.check_in)
                if getattr(attendance, "check_out", None):
                    row["check_outs"].append(attendance.check_out)
            if status == "absent":
                row["absent_days"] += 1
            if status == "late":
                row["late_days"] += 1
            if status == "leave":
                row["leave_days"] += 1

        # Include repairs delivered during the period even when their original
        # admission was in an earlier period.
        for repair in AnalyticsService._repair_activity_qs(start_date, end_date).select_related("mechanic"):
            mechanic_id = getattr(repair, "mechanic_id", None)
            if mechanic_id in rows:
                rows[mechanic_id]["repair_ids"].add(("repair", repair.pk))

        service_lines_recorded = AnalyticsService._period_qs(
            RepairServiceItem, "created_at", start_date, end_date, True
        )
        service_lines_on_active_repairs = RepairServiceItem.objects.filter(
            repair__in=AnalyticsService._repair_activity_qs(start_date, end_date)
        )
        service_items = list(
            (service_lines_recorded | service_lines_on_active_repairs)
            .distinct()
            .select_related("mechanic", "repair__mechanic", "repair")
        )
        for item in service_items:
            mechanic_id = getattr(item, "mechanic_id", None) or getattr(getattr(item, "repair", None), "mechanic_id", None)
            if mechanic_id in rows:
                rows[mechanic_id]["repair_ids"].add(("repair", item.repair_id))

        # Parts do not have their own mechanic field; attribute them to the
        # repair's assigned mechanic when a part line is recorded in-period.
        repair_parts = AnalyticsService._period_qs(RepairPart, "created_at", start_date, end_date, True).select_related("repair__mechanic")
        for item in repair_parts:
            mechanic_id = getattr(getattr(item, "repair", None), "mechanic_id", None)
            if mechanic_id in rows:
                rows[mechanic_id]["repair_ids"].add(("repair", item.repair_id))

        audit_qs = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False).select_related("mechanic", "service_request")
        request_to_repair = {}
        if AnalyticsService._has_field(Repair, "service_request"):
            for repair in Repair.objects.exclude(service_request__isnull=True).only("id", "service_request_id"):
                request_to_repair[repair.service_request_id] = repair.pk
        for audit in audit_qs:
            mechanic_id = getattr(audit, "mechanic_id", None)
            if mechanic_id not in rows:
                continue
            row = rows[mechanic_id]
            row["audit_activity_count"] += 1
            request_id = getattr(audit, "service_request_id", None)
            repair_id = request_to_repair.get(request_id) if request_id else None
            row["repair_ids"].add(("repair", repair_id) if repair_id else ("audit", audit.pk))
            started = getattr(audit, "work_start", None)
            ended = getattr(audit, "work_end", None)
            if started and ended:
                try:
                    duration = (ended - started).total_seconds() / 3600
                    if duration >= 0:
                        row["recorded_repair_hours"] += duration
                except Exception:
                    pass
            if AnalyticsService._has_field(AuditLog, "returned_for_repair") and getattr(audit, "returned_for_repair", False):
                row["returned_repairs"] += 1
            if AnalyticsService._has_field(AuditLog, "customer_satisfaction"):
                value = getattr(audit, "customer_satisfaction", None)
                if value is not None:
                    row.setdefault("_satisfaction_values", []).append(float(value))

        invoice_items = AnalyticsService._period_qs(InvoiceItem, "invoice__issued_at", start_date, end_date, True).select_related("invoice__repair__mechanic", "mechanic")
        mechanics_with_invoiced_labor = set()
        for item in invoice_items:
            if getattr(item, "item_type", None) != "service":
                continue
            repair = getattr(getattr(item, "invoice", None), "repair", None)
            mechanic_id = getattr(item, "mechanic_id", None) or getattr(repair, "mechanic_id", None)
            if mechanic_id in rows:
                rows[mechanic_id]["labor_revenue"] += AnalyticsService._cash(item.quantity) * AnalyticsService._cash(item.unit_price)
                mechanics_with_invoiced_labor.add(mechanic_id)

        # Invoices are the financial source when a mechanic has invoiced labor;
        # otherwise use service rows recorded in the period as the best available proxy.
        for item in service_items:
            mechanic_id = getattr(item, "mechanic_id", None) or getattr(getattr(item, "repair", None), "mechanic_id", None)
            if mechanic_id in rows and mechanic_id not in mechanics_with_invoiced_labor:
                rows[mechanic_id]["labor_revenue"] += AnalyticsService._cash(item.quantity) * AnalyticsService._cash(item.unit_price)

        salary_rows = AnalyticsService._paid_salary_qs(start_date, end_date).select_related("employee")
        for payment in salary_rows:
            employee_id = getattr(payment, "employee_id", None)
            if employee_id in rows:
                rows[employee_id]["salary_paid"] += AnalyticsService._cash(getattr(payment, "amount", 0))

        result = []
        for employee in employees:
            row = rows[employee.pk]
            satisfaction_values = row.pop("_satisfaction_values", [])
            row["customer_satisfaction"] = round(sum(satisfaction_values) / len(satisfaction_values), 2) if satisfaction_values else None
            row["repair_count"] = len(row.pop("repair_ids"))
            row["completed_repairs"] = row["repair_count"]
            row["attendance_hours"] = round(row["attendance_hours"], 2)
            row["recorded_repair_hours"] = round(row["recorded_repair_hours"], 2)
            row["average_daily_hours"] = round(row["attendance_hours"] / row["present_days"], 2) if row["present_days"] else None
            row["average_check_in"] = AnalyticsService._time_average(row.pop("check_ins")) or "—"
            row["average_check_out"] = AnalyticsService._time_average(row.pop("check_outs")) or "—"
            row["labor_income"] = row["labor_revenue"]
            row["generated_revenue"] = row["labor_revenue"]
            row["estimated_contribution_after_salary"] = row["labor_revenue"] - row["salary_paid"]
            row["labor_revenue_per_attendance_hour"] = round(float(row["labor_revenue"] / Decimal(str(row["attendance_hours"]))), 2) if row["attendance_hours"] > 0 else None
            row["repairs_per_present_day"] = round(row["repair_count"] / row["present_days"], 2) if row["present_days"] else None
            result.append(row)

        result.sort(key=lambda row: (row["attendance_hours"], row["repair_count"], row["labor_revenue"]), reverse=True)
        return result

    @staticmethod
    def get_daily_activity_summary(start_date, end_date):
        attendance = AnalyticsService._period_qs(Attendance, "date", start_date, end_date, False)
        notes = AnalyticsService._period_qs(DailyNote, "note_date", start_date, end_date, False)
        advances = AnalyticsService._period_qs(SalaryAdvance, "date", start_date, end_date, False)
        bonuses = AnalyticsService._period_qs(SalaryBonus, "date", start_date, end_date, False)
        payrolls = PayrollSnapshot.objects.filter(start_date__lte=end_date, end_date__gte=start_date) if start_date and end_date else PayrollSnapshot.objects.all()
        payments = AnalyticsService._paid_salary_qs(start_date, end_date)
        incomes = AnalyticsService._period_qs(DailyIncome, "income_date", start_date, end_date, False)
        expenses = AnalyticsService._period_qs(DailyExpense, "expense_date", start_date, end_date, False)
        attendance_rows = list(attendance)
        measured_presence = ("present", "late", "half_day")
        attendance_rows_missing_times = sum(
            1 for record in attendance_rows
            if getattr(record, "status", "present") in measured_presence
            and (not getattr(record, "check_in", None) or not getattr(record, "check_out", None))
        )
        return {
            "attendance_count": len(attendance_rows),
            "attendance_rows_missing_times": attendance_rows_missing_times,
            "present_days": attendance.filter(status__in=("present", "late", "half_day")).count(),
            "absent_days": attendance.filter(status="absent").count(),
            "leave_days": attendance.filter(status="leave").count(),
            "late_days": attendance.filter(status="late").count(),
            "half_days": attendance.filter(status="half_day").count(),
            "recorded_attendance_hours": round(sum(AnalyticsService._attendance_duration(record) for record in attendance), 2),
            "daily_income_count": incomes.count(),
            "daily_expense_count": expenses.count(),
            "daily_note_count": notes.count(),
            "payroll_count": payrolls.count(),
            "salary_payment_count": payments.count(),
            "salary_advance_count": advances.count(),
            "salary_advance_amount": AnalyticsService._sum(advances, "amount"),
            "salary_bonus_count": bonuses.count(),
            "salary_bonus_amount": AnalyticsService._sum(bonuses, "amount"),
        }

    @staticmethod
    def get_communication_summary(start_date, end_date):
        if CommunicationLog is None:
            return {"count": 0, "sent": 0, "failed": 0}
        logs = AnalyticsService._period_qs(CommunicationLog, "created_at", start_date, end_date, True)
        status_titles = AnalyticsService._choices_map(CommunicationLog, "status")
        sent_values = [key for key, title in status_titles.items() if str(key).lower() in ("sent", "success", "delivered") or any(token in str(title).lower() for token in ("ارسال", "موفق", "تحویل"))]
        failed_values = [key for key, title in status_titles.items() if str(key).lower() in ("failed", "error") or any(token in str(title).lower() for token in ("ناموفق", "خطا", "شکست"))]
        return {
            "count": logs.count(),
            "sent": logs.filter(status__in=sent_values).count() if sent_values else 0,
            "failed": logs.filter(status__in=failed_values).count() if failed_values else 0,
        }

    @staticmethod
    def get_top_services(start_date, end_date, limit=10):
        rows = defaultdict(lambda: {"count": 0, "amount": ZERO, "source_set": set()})
        invoiced_keys = set()
        service_repair_ids = set()

        invoice_items = AnalyticsService._period_qs(InvoiceItem, "invoice__issued_at", start_date, end_date, True).filter(item_type="service").select_related("invoice__repair")
        for item in invoice_items:
            title = str(getattr(item, "title", "خدمت ثبت‌نشده") or "خدمت ثبت‌نشده").strip()
            repair_id = getattr(getattr(item, "invoice", None), "repair_id", None)
            if repair_id:
                service_repair_ids.add(repair_id)
                invoiced_keys.add((repair_id, title.casefold()))
            rows[title]["count"] += int(getattr(item, "quantity", 0) or 0)
            rows[title]["amount"] += AnalyticsService._cash(item.quantity) * AnalyticsService._cash(item.unit_price)
            rows[title]["source_set"].add("فاکتور")

        service_lines_recorded = AnalyticsService._period_qs(
            RepairServiceItem, "created_at", start_date, end_date, True
        )
        service_lines_on_active_repairs = RepairServiceItem.objects.filter(
            repair__in=AnalyticsService._repair_activity_qs(start_date, end_date)
        )
        service_items = (service_lines_recorded | service_lines_on_active_repairs).distinct().select_related("repair")
        for item in service_items:
            title = str(getattr(item, "title", "خدمت ثبت‌نشده") or "خدمت ثبت‌نشده").strip()
            repair_id = getattr(item, "repair_id", None)
            # Invoice generation copies repair service lines; do not double-count
            # the same repair/title when both source records occur in this period.
            if repair_id and (repair_id, title.casefold()) in invoiced_keys:
                continue
            rows[title]["count"] += int(getattr(item, "quantity", 0) or 0)
            rows[title]["amount"] += AnalyticsService._cash(item.quantity) * AnalyticsService._cash(item.unit_price)
            rows[title]["source_set"].add("خدمات تعمیر")
            if repair_id:
                service_repair_ids.add(repair_id)

        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False).select_related("service_request")
        request_to_repair = {
            repair.service_request_id: repair.pk
            for repair in Repair.objects.exclude(service_request__isnull=True).only("id", "service_request_id")
        }
        choice_titles = AnalyticsService._choices_map(AuditLog, "service_type")
        for activity in audit_rows:
            repair_id = request_to_repair.get(getattr(activity, "service_request_id", None))
            if repair_id and repair_id in service_repair_ids:
                continue
            code = str(getattr(activity, "service_type", "other") or "other")
            title = choice_titles.get(code, code) or "سایر خدمات"
            rows[title]["count"] += 1
            rows[title]["source_set"].add("گزارش فعالیت تعمیرکار")

        result = []
        for title, values in rows.items():
            sources = sorted(values.pop("source_set"))
            values["source"] = "، ".join(sources)
            result.append({"service": title, **values})
        result.sort(key=lambda row: (row["count"], row["amount"]), reverse=True)
        return result[:limit]

    @staticmethod
    def get_top_customers(start_date, end_date, limit=10):
        customer_stats = defaultdict(lambda: {
            "repair_count": 0, "visit_count": 0, "activity_count": 0,
            "invoice_count": 0, "amount": ZERO, "paid_amount": ZERO,
            "repair_ids": set(), "activity_ids": set(), "visit_ids": set(),
        })
        visits_available = False

        customer_by_name = {}
        for customer in Customer.objects.all():
            name = str(getattr(customer, "full_name", "") or str(customer)).strip().casefold()
            if name:
                customer_by_name[name] = customer

        if CustomerVisit is not None:
            visits = AnalyticsService._period_qs(CustomerVisit, "arrived_at", start_date, end_date, True).select_related("customer")
            if AnalyticsService._has_field(CustomerVisit, "status"):
                visits = visits.exclude(status="cancelled")
            for visit in visits:
                customer = getattr(visit, "customer", None)
                if customer:
                    bucket = customer_stats[customer.pk]
                    bucket.update({"customer_id": customer.pk, "customer": str(customer)})
                    bucket["visit_ids"].add(visit.pk)
                    bucket["visit_count"] = len(bucket["visit_ids"])
            visits_available = any(values["visit_count"] for values in customer_stats.values())

        repair_scope = AnalyticsService._repair_activity_qs(start_date, end_date).select_related("customer")
        for repair in repair_scope:
            customer = getattr(repair, "customer", None)
            if customer:
                bucket = customer_stats[customer.pk]
                bucket.update({"customer_id": customer.pk, "customer": str(customer)})
                bucket["repair_ids"].add(repair.pk)
                bucket["repair_count"] = len(bucket["repair_ids"])

        request_to_repair = {
            repair.service_request_id: repair
            for repair in Repair.objects.select_related("customer").exclude(service_request__isnull=True)
        }
        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False).select_related("service_request")
        for activity in audit_rows:
            request_id = getattr(activity, "service_request_id", None)
            linked_repair = request_to_repair.get(request_id)
            customer = getattr(getattr(activity, "service_request", None), "customer", None)
            if customer is None and linked_repair is not None:
                customer = getattr(linked_repair, "customer", None)
            if customer is None:
                customer = customer_by_name.get(str(getattr(activity, "customer_name", "") or "").strip().casefold())
            if customer is None:
                continue
            bucket = customer_stats[customer.pk]
            bucket.update({"customer_id": customer.pk, "customer": str(customer)})
            if linked_repair is not None:
                bucket["repair_ids"].add(linked_repair.pk)
                bucket["repair_count"] = len(bucket["repair_ids"])
            else:
                bucket["activity_ids"].add(activity.pk)
                bucket["activity_count"] = len(bucket["activity_ids"])

        invoices = AnalyticsService._period_qs(Invoice, "issued_at", start_date, end_date, True).select_related("repair__customer").prefetch_related("items", "payments")
        for invoice in invoices:
            customer = getattr(getattr(invoice, "repair", None), "customer", None)
            if customer:
                bucket = customer_stats[customer.pk]
                bucket.update({"customer_id": customer.pk, "customer": str(customer)})
                bucket["invoice_count"] += 1
                total, paid = AnalyticsService._invoice_total(invoice, payment_cutoff=end_date)
                bucket["amount"] += total
                bucket["paid_amount"] += paid

        result = []
        if visits_available:
            basis = "مراجعات ثبت‌شده"
        else:
            basis = "تعمیرات و فعالیت‌های ثبت‌شده (دفتر مراجعه خالی است)"
        for values in customer_stats.values():
            values["frequency_basis"] = basis
            values["frequency_count"] = values["visit_count"] if visits_available else values["repair_count"] + values["activity_count"]
            values.pop("repair_ids", None)
            values.pop("activity_ids", None)
            values.pop("visit_ids", None)
            if values["frequency_count"] > 0:
                result.append(values)
        result.sort(key=lambda row: (row["frequency_count"], row["amount"], row["invoice_count"]), reverse=True)
        return result[:limit]

    @staticmethod
    def get_vehicle_summary(start_date, end_date, limit=10):
        grouped = defaultdict(lambda: {
            "repair_ids": set(), "invoice_ids": set(), "activity_ids": set(), "unlinked_activity_ids": set(), "visit_ids": set(),
            "work_ids": set(), "vehicle_ids": set(), "invoiced_revenue": ZERO,
        })

        def bucket_for(vehicle=None, fallback_label=""):
            label = AnalyticsService._vehicle_label(vehicle, fallback_label)
            bucket = grouped[label]
            if vehicle is not None and getattr(vehicle, "pk", None) is not None:
                bucket["vehicle_ids"].add(vehicle.pk)
            return label, bucket

        def vehicle_for_repair(repair):
            vehicle = getattr(repair, "vehicle", None)
            if vehicle is None:
                vehicle = getattr(getattr(repair, "service_request", None), "vehicle", None)
            return vehicle

        repair_scope = AnalyticsService._repair_activity_qs(start_date, end_date).select_related("vehicle", "service_request__vehicle")
        repair_to_label = {}
        for repair in repair_scope:
            vehicle = vehicle_for_repair(repair)
            if vehicle is None:
                continue
            label, bucket = bucket_for(vehicle)
            bucket["repair_ids"].add(repair.pk)
            bucket["work_ids"].add(("repair", repair.pk))
            repair_to_label[repair.pk] = label

        invoices = AnalyticsService._period_qs(Invoice, "issued_at", start_date, end_date, True).select_related("repair__vehicle", "repair__service_request__vehicle").prefetch_related("items")
        for invoice in invoices:
            repair = getattr(invoice, "repair", None)
            vehicle = vehicle_for_repair(repair) if repair is not None else None
            if vehicle is None:
                continue
            label, bucket = bucket_for(vehicle)
            bucket["invoice_ids"].add(invoice.pk)
            bucket["work_ids"].add(("repair", repair.pk))
            bucket["invoiced_revenue"] += AnalyticsService._item_total(list(invoice.items.all()))

        if CustomerVisit is not None:
            visits = AnalyticsService._period_qs(CustomerVisit, "arrived_at", start_date, end_date, True).exclude(status="cancelled").select_related("vehicle")
            for visit in visits:
                vehicle = getattr(visit, "vehicle", None)
                if vehicle is not None:
                    _, bucket = bucket_for(vehicle)
                    bucket["visit_ids"].add(visit.pk)

        request_to_repair = {
            repair.service_request_id: repair.pk
            for repair in Repair.objects.exclude(service_request__isnull=True).only("id", "service_request_id")
        }
        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False).select_related("service_request__vehicle")
        for activity in audit_rows:
            request = getattr(activity, "service_request", None)
            vehicle = getattr(request, "vehicle", None) if request else None
            fallback = getattr(activity, "vehicle", "")
            label, bucket = bucket_for(vehicle, fallback)
            repair_id = request_to_repair.get(getattr(activity, "service_request_id", None))
            bucket["activity_ids"].add(activity.pk)
            # A linked activity confirms that this repair was worked on during
            # the period, even if the repair admission was older.
            if repair_id:
                bucket["repair_ids"].add(repair_id)
                bucket["work_ids"].add(("repair", repair_id))
            else:
                bucket["unlinked_activity_ids"].add(activity.pk)
                bucket["work_ids"].add(("audit", activity.pk))

        result = []
        for label, values in grouped.items():
            repair_count = len(values["repair_ids"])
            activity_count = len(values["activity_ids"])
            visit_count = len(values["visit_ids"])
            work_count = len(values["work_ids"])
            chart_count = work_count if work_count else visit_count
            row = {
                "vehicle": label,
                "repair_count": repair_count,
                "activity_count": activity_count,
                "visit_count": visit_count,
                "work_count": work_count,
                "chart_count": chart_count,
                "invoice_count": len(values["invoice_ids"]),
                "invoiced_revenue": values["invoiced_revenue"],
                "distinct_vehicles": len(values["vehicle_ids"]),
            }
            result.append(row)
        result.sort(key=lambda row: (row["work_count"], row["invoiced_revenue"], row["visit_count"]), reverse=True)
        return result[:limit]

    @staticmethod
    def get_expense_breakdown(start_date, end_date, limit=10):
        totals = defaultdict(lambda: {"amount": ZERO, "count": 0})
        expenses = AnalyticsService._period_qs(DailyExpense, "expense_date", start_date, end_date, False)
        for record in expenses:
            title = str(getattr(record, "title", "هزینه نامشخص") or "هزینه نامشخص")
            totals[title]["amount"] += AnalyticsService._cash(getattr(record, "amount", 0))
            totals[title]["count"] += 1
        salary = AnalyticsService._paid_salary_qs(start_date, end_date)
        if salary.exists():
            totals["حقوق پرداخت‌شده"]["amount"] += AnalyticsService._sum(salary, "amount")
            totals["حقوق پرداخت‌شده"]["count"] += salary.count()
        audit_rows = AnalyticsService._period_qs(AuditLog, "service_date", start_date, end_date, False)
        supplier_parts = AnalyticsService._safe_filter(PurchasedPart.objects.all(), audit__in=audit_rows)
        if supplier_parts.exists():
            totals["قطعات خریداری‌شده برای تعمیر"]["amount"] += AnalyticsService._sum(supplier_parts, "total_price")
            totals["قطعات خریداری‌شده برای تعمیر"]["count"] += supplier_parts.count()
        stock_used = AnalyticsService._safe_filter(InventoryUsedPart.objects.all(), audit__in=audit_rows).select_related("part")
        estimated_stock_cost = ZERO
        for row in stock_used:
            purchase_price = getattr(getattr(row, "part", None), "purchase_price", None)
            if purchase_price is not None:
                estimated_stock_cost += AnalyticsService._cash(row.quantity) * AnalyticsService._cash(purchase_price)
        if estimated_stock_cost:
            totals["بهای برآوردی قطعات مصرفی انبار"]["amount"] += estimated_stock_cost
            totals["بهای برآوردی قطعات مصرفی انبار"]["count"] += stock_used.count()
        result = [{"category": title, **values} for title, values in totals.items()]
        result.sort(key=lambda row: row["amount"], reverse=True)
        return result[:limit]

    @staticmethod
    def _build_insights(financial, operations, employees, top_customers, vehicles, services, inventory, activity):
        insights = []
        if top_customers:
            top = top_customers[0]
            if top.get("frequency_basis", "").startswith("مراجعات"):
                freq = top.get("visit_count", 0)
                freq_label = "مراجعه ثبت‌شده"
            else:
                freq = top.get("frequency_count", 0)
                freq_label = "تعمیر/فعالیت ثبت‌شده"
            insights.append({"title": "مشتری پرتکرار", "text": f"{top.get('customer', '—')} با {freq or 0} {freq_label} در رتبه نخست قرار دارد."})
        if vehicles:
            top = vehicles[0]
            if top.get("work_count", 0):
                freq = top["work_count"]
                freq_label = "تعمیر/فعالیت مرتبط"
            else:
                freq = top.get("visit_count", 0)
                freq_label = "مراجعه"
            insights.append({"title": "خودروی پرتکرار", "text": f"{top['vehicle']} با {freq} {freq_label} پرتکرارترین گروه خودرو است."})
        if services:
            top = services[0]
            insights.append({"title": "خدمت پرتکرار", "text": f"{top['service']} با {top['count']} مورد ثبت، بیشترین فراوانی را دارد."})
        if employees:
            by_hours = max(employees, key=lambda row: row.get("attendance_hours", 0))
            if by_hours.get("attendance_hours", 0) > 0:
                insights.append({"title": "بیشترین حضور ثبت‌شده", "text": f"{by_hours['employee']} با {by_hours['attendance_hours']:.1f} ساعت حضور ثبت‌شده بیشترین ساعات حضور را داشته است."})
            # Do not declare an employee "best" when everyone has zero
            # attributable labor revenue; that would turn missing assignments
            # into a misleading zero-value ranking.
            revenue_ranked = [
                row for row in employees
                if row.get("labor_revenue_per_attendance_hour") is not None
                and AnalyticsService._cash(row.get("labor_revenue")) > ZERO
            ]
            if revenue_ranked:
                best = max(revenue_ranked, key=lambda row: row["labor_revenue_per_attendance_hour"])
                insights.append({"title": "بیشترین اجرت به ازای ساعت حضور", "text": f"{best['employee']} با {best['labor_revenue_per_attendance_hour']:,.0f} تومان به ازای هر ساعت حضور، بالاترین نسبت ثبت‌شده را دارد؛ این شاخص به‌تنهایی سود خالص یا کیفیت کار را اثبات نمی‌کند."})
            elif any(row.get("attendance_hours", 0) > 0 for row in employees):
                insights.append({"title": "اجرت قابل انتساب نیست", "text": "ساعات حضور ثبت شده، اما در این دوره اجرت فاکتورشده قابل انتساب به تعمیرکاران وجود ندارد؛ تا اصلاح انتساب خدمات، رتبه بهره‌وری مالی اعلام نمی‌شود."})
        if operations.get("repairs", 0) == 0 and operations.get("delivered_repairs", 0) > 0:
            insights.append({"title": "تعمیرات تحویل‌شده از دوره‌های قبل", "text": f"در این دوره {operations['delivered_repairs']} تعمیر تحویل شده اما پذیرش جدیدی در همین بازه ثبت نشده است؛ این دو شاخص بر اساس تاریخ‌های متفاوت محاسبه می‌شوند."})
        if financial.get("invoice_count", 0) == 0 and financial.get("cash_collected", 0) > 0:
            insights.append({"title": "تفکیک فاکتور و وصولی", "text": "در این دوره وصول وجه ثبت شده اما فاکتور جدیدی صادر نشده است؛ وصولی‌های این دوره ممکن است مربوط به فاکتورهای دوره‌های قبل باشد."})
        if inventory.get("low_stock", 0):
            insights.append({"title": "نیاز به بررسی انبار", "text": f"{inventory['low_stock']} قلم کالا در وضعیت کم‌موجودی یا زیر حداقل موجودی قرار دارد."})
        if activity.get("attendance_count", 0) == 0:
            insights.append({"title": "محدودیت محاسبه بهره‌وری", "text": "برای این دوره هیچ رکورد حضور و غیاب ثبت نشده؛ مقایسه ساعات کار و میانگین ورود/خروج قابل محاسبه نیست."})
        return insights[:8]

    @staticmethod
    def get_report_metrics(start_date, end_date):
        financial = AnalyticsService.get_financial_summary(start_date, end_date)
        operations = AnalyticsService.get_operational_summary(start_date, end_date)
        invoices = AnalyticsService.get_invoice_summary(start_date, end_date)
        inventory = AnalyticsService.get_inventory_summary(start_date, end_date)
        employees = AnalyticsService.get_employee_summary(start_date, end_date)
        activity = AnalyticsService.get_daily_activity_summary(start_date, end_date)
        communications = AnalyticsService.get_communication_summary(start_date, end_date)
        top_services = AnalyticsService.get_top_services(start_date, end_date)
        top_customers = AnalyticsService.get_top_customers(start_date, end_date)
        vehicles = AnalyticsService.get_vehicle_summary(start_date, end_date)
        expenses = AnalyticsService.get_expense_breakdown(start_date, end_date)

        # Totals help distinguish "no records in this period" from "no records
        # exist in the database". All period counts use the source entity's own
        # event date unless explicitly labelled as an associated repair.
        customers_total = Customer.objects.count()
        vehicles_total = CustomerVehicle.objects.count()
        requests_total = CustomerServiceRequest.objects.count()
        repairs_total = Repair.objects.count()
        repair_service_lines_total = RepairServiceItem.objects.count()
        repair_parts_total = RepairPart.objects.count()
        invoices_total = Invoice.objects.count()
        payments_total = InvoicePayment.objects.count()
        audit_logs_total = AuditLog.objects.count()
        visits_total = CustomerVisit.objects.count() if CustomerVisit is not None else 0
        attendance_total = Attendance.objects.count()
        data_quality = {
            "source_counts": {
                "customers_total": customers_total,
                "customers_in_period": operations["new_customers"],
                "vehicles_total": vehicles_total,
                "vehicles_in_period": operations["new_vehicles"],
                "requests_total": requests_total,
                "service_requests_in_period": operations["service_requests"],
                "repairs_total": repairs_total,
                "repairs_created_in_period": operations["repairs"],
                "repairs_active_in_period": operations["repairs_active"],
                "repairs_delivered_in_period": operations["delivered_repairs"],
                "repair_service_lines_total": repair_service_lines_total,
                "repair_service_lines_in_period": operations["repair_service_lines"],
                "repair_parts_total": repair_parts_total,
                "repair_part_lines_in_period": operations["repair_part_lines"],
                "invoices_total": invoices_total,
                "invoices_in_period": financial["invoice_count"],
                "payments_total": payments_total,
                "payments_in_period": financial["payment_count"],
                "audit_logs_total": audit_logs_total,
                "legacy_audit_logs_in_period": operations["legacy_activity_records"],
                "visits_total": visits_total,
                "customer_visits_in_period": operations["customer_visits"],
                "attendance_total": attendance_total,
                "attendance_rows_in_period": activity["attendance_count"],
                "supplier_purchase_lines_total": PurchasedPart.objects.count(),
                "supplier_purchase_lines_in_period": inventory["purchased_part_lines"],
            },
            "warnings": [],
        }
        source_counts = data_quality["source_counts"]
        if source_counts["invoices_total"] and not financial["invoice_count"]:
            data_quality["warnings"].append(
                f"در کل پایگاه داده {source_counts['invoices_total']} فاکتور وجود دارد، اما تاریخ صدور هیچ‌کدام در بازه این گزارش نیست؛ درآمد فاکتور این دوره صفر است، نه لزوماً کل فروش پایگاه داده."
            )
        if source_counts["repair_service_lines_total"] and not operations["repair_service_lines"]:
            data_quality["warnings"].append(
                f"در کل پایگاه داده {source_counts['repair_service_lines_total']} ردیف خدمات تعمیر وجود دارد، اما تاریخ ثبت این ردیف‌ها خارج از بازه گزارش است."
            )
        if source_counts["repair_parts_total"] and not operations["repair_part_lines"]:
            data_quality["warnings"].append(
                f"در کل پایگاه داده {source_counts['repair_parts_total']} ردیف قطعات تعمیر وجود دارد، اما تاریخ ثبت آن‌ها خارج از بازه گزارش است."
            )
        if source_counts["audit_logs_total"] and not operations["legacy_activity_records"]:
            data_quality["warnings"].append(
                f"در کل پایگاه داده {source_counts['audit_logs_total']} گزارش فعالیت تعمیرکار وجود دارد، اما تاریخ خدمت آن‌ها خارج از بازه گزارش است."
            )
        if source_counts["visits_total"] and not operations["customer_visits"]:
            data_quality["warnings"].append(
                f"در کل پایگاه داده {source_counts['visits_total']} مراجعه ثبت شده است، اما مراجعه معتبر با تاریخ ورود در بازه این گزارش وجود ندارد."
            )
        if source_counts["attendance_total"] and not activity["attendance_count"]:
            data_quality["warnings"].append(
                f"در کل پایگاه داده {source_counts['attendance_total']} رکورد حضور و غیاب وجود دارد، اما رکوردی با تاریخ حضور در بازه گزارش ثبت نشده است."
            )
        if operations["repairs"] and not operations["completed_repairs"]:
            data_quality["warnings"].append("هیچ تحویل/تکمیل در این دوره از روی فیلد تحویل تعمیر ثبت نشده است؛ بررسی کنید تاریخ تحویل تعمیرات ثبت شود.")
        if not operations["customer_visits"]:
            data_quality["warnings"].append("دفتر مراجعات در این دوره داده ندارد؛ رتبه مشتریان در صورت نبودن مراجعه ثبت‌شده بر مبنای تعداد تعمیرات ثبت‌شده محاسبه می‌شود.")
        if not activity["attendance_count"]:
            data_quality["warnings"].append("داده حضور و غیاب این دوره خالی است؛ شاخص ساعات حضور و میانگین ورود/خروج برای دوره قابل اتکا نیست.")
        elif activity.get("attendance_rows_missing_times", 0):
            data_quality["warnings"].append(f"در {activity['attendance_rows_missing_times']} رکورد حضورِ حاضر/تأخیری/نیمه‌وقت، ساعت ورود یا خروج کامل ثبت نشده؛ این ردیف‌ها در جمع ساعت حضور منظور نشده‌اند.")
        if financial["invoice_count"] == 0 and financial["cash_collected"] > 0:
            data_quality["warnings"].append("پرداخت ثبت شده اما فاکتور صادرشده در این دوره وجود ندارد؛ دریافت وجه با فروش فاکتورشده یکسان نیست.")
        if financial["invoice_count"] and invoices["status"].get("empty", 0):
            data_quality["warnings"].append(f"{invoices['status']['empty']} فاکتور بدون ردیف مالی یا با مبلغ صفر ثبت شده؛ پیش از تحلیل میانگین و فروش، اقلام این فاکتورها بررسی شوند.")
        if financial["salary_payment_count"]:
            data_quality["warnings"].append("نتیجه عملیاتی بر مبنای حقوق ثبت‌شده به‌عنوان پرداخت‌شده محاسبه می‌شود؛ تعهد حقوق و پاداش پرداخت‌نشده در این شاخص منظور نشده است.")
        if not inventory["purchased_part_lines"]:
            data_quality["warnings"].append("ردیف خرید قطعه برای تعمیر در این دوره ثبت نشده؛ هزینه واقعی خرید تاریخی انبار از موجودی فعلی قابل بازسازی نیست.")
        if operations["repair_part_lines"]:
            data_quality["warnings"].append("در ردیف قطعات تعمیر، قیمت ثبت‌شده قیمت واحد فروش است و بهای خرید تاریخی به‌ازای همان ردیف ذخیره نشده؛ بنابراین نتیجه عملیاتی می‌تواند بیش‌برآورد شود.")
        if activity["attendance_count"]:
            data_quality["warnings"].append("به‌دلیل تعریف‌نشدن ساعات استاندارد شیفت، گزارش مدت حضور ثبت‌شده را نشان می‌دهد و اضافه‌کاری قراردادی را به‌صورت قطعی محاسبه نمی‌کند.")
        if any(row["repair_count"] and not row["labor_revenue"] for row in employees):
            data_quality["warnings"].append("برای برخی تعمیرکاران تعمیر ثبت شده ولی اجرت فاکتورشده به نام آن‌ها ثبت نشده؛ تکمیل انتساب تعمیرکار روی خدمات/فاکتور، رتبه‌بندی را دقیق‌تر می‌کند.")
        elif any(row.get("attendance_hours", 0) > 0 for row in employees) and not any(row.get("labor_revenue", ZERO) > ZERO for row in employees):
            data_quality["warnings"].append("حضور و غیاب ثبت شده، اما اجرت مثبت و قابل انتساب به تعمیرکاران در این دوره پیدا نشد؛ این به معنی بهره‌وری صفر کارکنان نیست و ممکن است ناشی از انتساب‌نشدن خدمات به تعمیرکار یا خارج‌بودن فاکتور از بازه باشد.")

        report = {
            "financial": financial,
            "operations": operations,
            "invoices": invoices,
            "inventory": inventory,
            "employees": employees,
            "activity": activity,
            "communications": communications,
            "top_services": top_services,
            "top_customers": top_customers,
            "vehicles": vehicles,
            "expense_breakdown": expenses,
            "data_quality": data_quality,
        }
        report["insights"] = AnalyticsService._build_insights(financial, operations, employees, top_customers, vehicles, top_services, inventory, activity)
        return report
