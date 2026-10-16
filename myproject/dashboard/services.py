from datetime import date
from functools import cached_property
from inventory.models import UsedPart
from django.db.models import (
    Avg,
    Count,
    F,
    Sum,
    QuerySet,
)

from crm.models import Invoice
from audit.models import AuditLog
from daily_activity.models import (
    DailyIncome,
    DailyExpense,
    DailyNote,
    Attendance
)
from inventory.models import Part

class DashboardService:

    def __init__(self):

        self.today = date.today()

        self.current_year = self.today.year

        self.current_month = self.today.month


    # ======================================================
    # Cached QuerySets
    # ======================================================

    @cached_property
    def invoices(self) -> QuerySet:

        return Invoice.objects.all()


    @cached_property
    def audit_logs(self) -> QuerySet:

        return AuditLog.objects.all()



    @cached_property
    def incomes(self):

        return DailyIncome.objects.all()


    @cached_property
    def expenses(self):

        return DailyExpense.objects.all()


    @cached_property
    def attendances(self):

        return Attendance.objects.all()


    @cached_property
    def notes(self):

        return DailyNote.objects.all()

    @cached_property
    def parts(self) -> QuerySet:

        return Part.objects.all()
    
    # ======================================================
    # Cached Filtered QuerySets
    # ======================================================

    @cached_property
    def today_invoices(self) -> QuerySet:

        return self.invoices.filter(

            created_at__date=self.today,

        )


    @cached_property
    def monthly_invoices(self) -> QuerySet:

        return self.invoices.filter(

            created_at__year=self.current_year,

            created_at__month=self.current_month,

        )


    @cached_property
    def yearly_invoices(self) -> QuerySet:

        return self.invoices.filter(

            created_at__year=self.current_year,

        )


    @cached_property
    def monthly_repairs(self) -> QuerySet:

        return self.audit_logs.filter(

            service_date__year=self.current_year,

            service_date__month=self.current_month,

        )


    @cached_property
    def yearly_repairs(self) -> QuerySet:

        return self.audit_logs.filter(

            service_date__year=self.current_year,

        )


    @cached_property
    def today_activity(self):

        return self.activities.filter(

            report_date=self.today,

        ).first()


    @cached_property
    def unpaid_invoices(self) -> QuerySet:

        return self.invoices.filter(

            status__in=[

                "pending",

                "partial",

            ]

        )



    @cached_property
    def low_stock_parts(self) -> QuerySet:

        return self.parts.filter(

            stock__lte=F(

                "minimum_stock",

            )

        )
    
    # ======================================================
    # Revenue Analytics
    # ======================================================

    def get_today_income(self) -> int:

        return (

            self.today_invoices.aggregate(

                total=Sum(

                    "paid_amount",

                )

            )["total"]

            or 0

        )


    def get_month_income(self) -> int:

        return (

            self.monthly_invoices.aggregate(

                total=Sum(

                    "paid_amount",

                )

            )["total"]

            or 0

        )


    def get_year_income(self) -> int:

        return (

            self.yearly_invoices.aggregate(

                total=Sum(

                    "paid_amount",

                )

            )["total"]

            or 0

        )


    def get_average_invoice_amount(self) -> float:

        return (

            self.yearly_invoices.aggregate(

                average=Avg(

                    "paid_amount",

                )

            )["average"]

            or 0

        )


    def get_invoice_count_today(self) -> int:

        return self.today_invoices.count()


    def get_invoice_count_month(self) -> int:

        return self.monthly_invoices.count()


    def get_invoice_count_year(self) -> int:

        return self.yearly_invoices.count()


    def get_revenue_summary(self) -> dict:

        return {

            "today_income": self.get_today_income(),

            "month_income": self.get_month_income(),

            "year_income": self.get_year_income(),

            "average_invoice": self.get_average_invoice_amount(),

            "today_invoice_count": self.get_invoice_count_today(),

            "month_invoice_count": self.get_invoice_count_month(),

            "year_invoice_count": self.get_invoice_count_year(),

        }

    # ======================================================
    # Profit Analytics
    # ======================================================

    def get_month_profit(self) -> int:

        return (

            self.monthly_repairs.aggregate(

                total=Sum(

                    "workshop_profit",

                )

            )["total"]

            or 0

        )


    def get_year_profit(self) -> int:

        return (

            self.yearly_repairs.aggregate(

                total=Sum(

                    "workshop_profit",

                )

            )["total"]

            or 0

        )


    def get_average_profit(self) -> float:

        return (

            self.yearly_repairs.aggregate(

                average=Avg(

                    "workshop_profit",

                )

            )["average"]

            or 0

        )


    def get_total_repairs_month(self) -> int:

        return self.monthly_repairs.count()


    def get_total_repairs_year(self) -> int:

        return self.yearly_repairs.count()


    def get_average_profit_per_repair(self) -> float:

        repairs = self.get_total_repairs_year()

        if repairs == 0:

            return 0

        return (

            self.get_year_profit()

            / repairs

        )


    def get_profit_summary(self) -> dict:

        return {

            "month_profit":

                self.get_month_profit(),

            "year_profit":

                self.get_year_profit(),

            "average_profit":

                self.get_average_profit(),

            "repairs_month":

                self.get_total_repairs_month(),

            "repairs_year":

                self.get_total_repairs_year(),

            "average_profit_per_repair":

                self.get_average_profit_per_repair(),

        }
    
    # ======================================================
    # Vehicle Analytics
    # ======================================================

    def get_today_received_vehicles(self) -> int:

        if not self.today_activity:

            return 0

        return self.today_activity.vehicles_received


    def get_today_delivered_vehicles(self) -> int:

        if not self.today_activity:

            return 0

        return self.today_activity.vehicles_delivered


    def get_active_repairs_count(self) -> int:

        return self.active_repairs.count()


    def get_today_pending_vehicles(self) -> int:

        received = self.get_today_received_vehicles()

        delivered = self.get_today_delivered_vehicles()

        return max(

            received - delivered,

            0,

        )


    def get_vehicle_summary(self) -> dict:

        return {

            "received_today":

                self.get_today_received_vehicles(),

            "delivered_today":

                self.get_today_delivered_vehicles(),

            "active_repairs":

                self.get_active_repairs_count(),

            "pending_today":

                self.get_today_pending_vehicles(),

        }
    
    # ======================================================
    # Invoice Analytics
    # ======================================================

    def get_unpaid_invoice_count(self) -> int:

        return self.unpaid_invoices.count()


    def get_unpaid_invoice_amount(self) -> int:

        return (

            self.unpaid_invoices.aggregate(

                total=Sum(

                    "remaining_amount",

                )

            )["total"]

            or 0

        )


    def get_paid_invoice_count(self) -> int:

        return self.invoices.filter(

            status="paid",

        ).count()


    def get_partial_invoice_count(self) -> int:

        return self.invoices.filter(

            status="partial",

        ).count()


    def get_pending_invoice_count(self) -> int:

        return self.invoices.filter(

            status="pending",

        ).count()


    def get_invoice_collection_rate(self) -> float:

        total = self.yearly_invoices.count()

        if total == 0:

            return 0

        paid = self.yearly_invoices.filter(

            status="paid",

        ).count()

        return round(

            (paid / total) * 100,

            2,

        )


    def get_invoice_summary(self) -> dict:

        return {

            "unpaid_count":

                self.get_unpaid_invoice_count(),

            "unpaid_amount":

                self.get_unpaid_invoice_amount(),

            "paid_count":

                self.get_paid_invoice_count(),

            "partial_count":

                self.get_partial_invoice_count(),

            "pending_count":

                self.get_pending_invoice_count(),

            "collection_rate":

                self.get_invoice_collection_rate(),

        }
    
    # ======================================================
    # Customer Analytics
    # ======================================================

    def get_total_customers(self) -> int:

        return (

            self.invoices.values(

                "customer_phone",

            )

            .distinct()

            .count()

        )


    def get_returned_repairs_count(self) -> int:

        return self.audit_logs.filter(

            returned_for_repair=True,

        ).count()


    def get_return_rate(self) -> float:

        repairs = self.audit_logs.count()

        if repairs == 0:

            return 0

        returned = self.get_returned_repairs_count()

        return round(

            (returned / repairs) * 100,

            2,

        )


    def get_customer_summary(self) -> dict:

        return {

            "total_customers":

                self.get_total_customers(),


        }
    
    # ======================================================
    # Inventory Analytics
    # ======================================================

    def get_low_stock_parts_count(self) -> int:

        return self.low_stock_parts.count()


    def get_total_parts_count(self) -> int:

        return self.parts.count()


    def get_total_inventory_stock(self) -> int:

        return (

            self.parts.aggregate(

                total=Sum(

                    "stock",

                )

            )["total"]

            or 0

        )


    def get_inventory_value(self) -> float:

        total = 0

        for part in self.parts.filter(

            is_active=True,

        ).only(

            "stock",

            "purchase_price",

        ):

            total += (

                part.stock

                * part.purchase_price

            )

        return total


    def get_out_of_stock_parts_count(self) -> int:

        return self.parts.filter(

            stock=0,

        ).count()


    def get_inventory_health_percentage(self) -> float:

        total = self.get_total_parts_count()

        if total == 0:

            return 100

        healthy = (

            total

            - self.get_low_stock_parts_count()

        )

        return round(

            (healthy / total) * 100,

            2,

        )


    def get_inventory_summary(self) -> dict:

        return {

            "total_parts":

                self.get_total_parts_count(),

            "total_stock":

                self.get_total_inventory_stock(),

            "inventory_value":

                self.get_inventory_value(),

            "low_stock_parts":

                self.get_low_stock_parts_count(),

            "out_of_stock":

                self.get_out_of_stock_parts_count(),

            "inventory_health":

                self.get_inventory_health_percentage(),

        }
    

    def get_active_parts(self):

        return self.parts.filter(

            is_active=True

        ).count()
    

    # ======================================================
    # Service Analytics
    # ======================================================

    def get_most_popular_service(self):

        return (

            self.audit_logs.values(

                "service_type",

            )

            .annotate(

                total=Count(

                    "id",

                )

            )

            .order_by(

                "-total",

            )

            .first()

        )


    def get_total_services(self) -> int:

        return self.audit_logs.count()


    def get_average_service_profit(self) -> float:

        return (

            self.audit_logs.aggregate(

                average=Avg(

                    "workshop_profit",

                )

            )["average"]

            or 0

        )


    def get_completed_repairs(self) -> int:

        return self.audit_logs.filter(

            repair_status="completed",

        ).count()


    def get_completion_rate(self) -> float:

        repairs = self.get_total_services()

        if repairs == 0:

            return 0

        completed = self.get_completed_repairs()

        return round(

            (completed / repairs) * 100,

            2,

        )


    def get_service_summary(self) -> dict:

        return {

            "total_services":

                self.get_total_services(),

            "most_popular":

                self.get_most_popular_service(),

            "average_profit":

                self.get_average_service_profit(),

            "completed":

                self.get_completed_repairs(),

            "in_progress":

                self.get_in_progress_repairs(),

            "delivered":

                self.get_delivered_repairs(),

            "completion_rate":

                self.get_completion_rate(),

        }
    
    # ======================================================
    # Employee Analytics
    # ======================================================

    def get_best_mechanic(self):

        return (

            self.audit_logs.filter(

                mechanic__isnull=False,

            )

            .values(

                "mechanic__id",

                "mechanic__user__first_name",

                "mechanic__user__last_name",

            )

            .annotate(

                total_repairs=Count(

                    "id",

                ),

                total_profit=Sum(

                    "workshop_profit",

                ),

            )

            .order_by(

                "-total_repairs",

                "-total_profit",

            )

            .first()

        )


    def get_total_mechanics(self) -> int:

        return (

            self.audit_logs.filter(

                mechanic__isnull=False,

            )

            .values(

                "mechanic",

            )

            .distinct()

            .count()

        )


    def get_average_repairs_per_mechanic(self) -> float:

        mechanics = self.get_total_mechanics()

        if mechanics == 0:

            return 0

        return round(

            self.get_total_services()

            / mechanics,

            2,

        )


    def get_average_profit_per_mechanic(self) -> float:

        mechanics = self.get_total_mechanics()

        if mechanics == 0:

            return 0

        return round(

            self.get_year_profit()

            / mechanics,

            2,

        )


    def get_employee_summary(self) -> dict:

        return {

            "best_mechanic":

                self.get_best_mechanic(),

            "total_mechanics":

                self.get_total_mechanics(),

            "average_repairs":

                self.get_average_repairs_per_mechanic(),

            "average_profit":

                self.get_average_profit_per_mechanic(),

        }
    

    def get_dashboard_statistics(self) -> dict:

        return {

            "revenue":

                self.get_revenue_summary(),

            "profit":

                self.get_profit_summary(),

            "vehicles":

                self.get_vehicle_summary(),

            "invoices":

                self.get_invoice_summary(),

            "customers":

                self.get_customer_summary(),

            "inventory":

                self.get_inventory_summary(),

            "services":

                self.get_service_summary(),

            "employees":

                self.get_employee_summary(),

            "quality":

                self.get_quality_summary(),

        }


    def get_dashboard_cards(self) -> dict:

        revenue = self.get_revenue_summary()

        profit = self.get_profit_summary()

        vehicles = self.get_vehicle_summary()

        invoices = self.get_invoice_summary()

        inventory = self.get_inventory_summary()

        quality = self.get_quality_summary()

        return {

            "today_income":

                revenue["today_income"],

            "month_income":

                revenue["month_income"],

            "year_income":

                revenue["year_income"],

            "month_profit":

                profit["month_profit"],

            "received_today":

                vehicles["received_today"],

            "delivered_today":

                vehicles["delivered_today"],

            "active_repairs":

                vehicles["active_repairs"],

            "pending_invoices":

                invoices["unpaid_count"],

            "inventory_health":

                inventory["inventory_health"],

            "quality_score":

                quality["quality_score"],

        }


    def get_dashboard_summary(self) -> dict:

        return {

            "statistics":

                self.get_dashboard_statistics(),

            "cards":

                self.get_dashboard_cards(),

        }
    
    # ======================================================
    # Chart Data Provider
    # ======================================================

    def get_revenue_chart_data(self) -> dict:

        revenue = self.get_revenue_summary()

        return {

            "labels": [

                "امروز",

                "این ماه",

                "امسال",

            ],

            "values": [

                revenue["today_income"],

                revenue["month_income"],

                revenue["year_income"],

            ],

        }


    def get_profit_chart_data(self) -> dict:

        profit = self.get_profit_summary()

        return {

            "labels": [

                "ماه",

                "سال",

            ],

            "values": [

                profit["month_profit"],

                profit["year_profit"],

            ],

        }


    def get_vehicle_chart_data(self) -> dict:

        vehicles = self.get_vehicle_summary()

        return {

            "labels": [

                "پذیرش",

                "تحویل",

                "در تعمیر",

            ],

            "values": [

                vehicles["received_today"],

                vehicles["delivered_today"],

                vehicles["active_repairs"],

            ],

        }


    def get_invoice_chart_data(self) -> dict:

        invoices = self.get_invoice_summary()

        return {

            "labels": [

                "پرداخت شده",

                "ناقص",

                "در انتظار",

            ],

            "values": [

                invoices["paid_count"],

                invoices["partial_count"],

                invoices["pending_count"],

            ],

        }


    def get_inventory_chart_data(self) -> dict:

        inventory = self.get_inventory_summary()

        return {

            "labels": [

                "کل قطعات",

                "کم موجود",

                "ناموجود",

            ],

            "values": [

                inventory["total_parts"],

                inventory["low_stock_parts"],

                inventory["out_of_stock"],

            ],

        }


    def get_quality_chart_data(self) -> dict:

        quality = self.get_quality_summary()

        return {

            "labels": [

                "رضایت",

                "امتیاز کیفیت",

                "مراجعات",

            ],

            "values": [

                quality["average_satisfaction"],

                quality["quality_score"],

                quality["returned_repairs"],

            ],

        }


    def get_all_chart_data(self) -> dict:

        return {

            "revenue":

                self.get_revenue_chart_data(),

            "profit":

                self.get_profit_chart_data(),

            "vehicles":

                self.get_vehicle_chart_data(),

            "invoices":

                self.get_invoice_chart_data(),

            "inventory":

                self.get_inventory_chart_data(),

            "quality":

                self.get_quality_chart_data(),

        }

        # ======================================================
    # Future AI Ready
    # ======================================================

    def export_for_ml(self) -> dict:

        """
        تمام داده‌های موردنیاز موتور تحلیل
        و Machine Learning را در یک ساختار
        استاندارد برمی‌گرداند.
        """

        return {

            "generated_at": self.today,

            "revenue":

                self.get_revenue_summary(),

            "profit":

                self.get_profit_summary(),

            "vehicles":

                self.get_vehicle_summary(),

            "customers":

                self.get_customer_summary(),

            "inventory":
                self.get_inventory_summary(),

            "used_parts":
                self.get_parts_summary(),
                
            "services":

                self.get_service_summary(),

            "employees":

                self.get_employee_summary(),

            "quality":

                self.get_quality_summary(),

            "charts":

                self.get_all_chart_data(),

        }


    def export_for_reports(self) -> dict:

        """
        داده استاندارد جهت ساخت
        PDF / Excel / CSV
        """

        return self.get_dashboard_summary()


    def export_for_api(self) -> dict:

        """
        داده استاندارد جهت
        REST API
        """

        return self.get_dashboard_summary()


    def export_complete_dashboard(self) -> dict:

        """
        نقطه ورود اصلی سیستم

        Admin
        Reports
        API
        ML
        Charts

        همگی از این متد استفاده می‌کنند.
        """

        return {

            "dashboard":

                self.get_dashboard_summary(),

            "ml":

                self.export_for_ml(),

            "reports":

                self.export_for_reports(),

            "api":

                self.export_for_api(),

        }
    
# ======================================================
# Parts Analytics
# ======================================================

    def get_most_used_part(self):

        return (

            UsedPart.objects

            .values(

                "part__title",

            )

            .annotate(

                total=Sum(

                    "quantity",

                )

            )

            .order_by(

                "-total",

            )

            .first()

        )


    def get_total_used_parts(self):

        return (

            UsedPart.objects.aggregate(

                total=Sum(

                    "quantity",

                )

            )["total"]

            or 0

        )


    def get_parts_summary(self):

        return {

        "most_used":

            self.get_most_used_part(),

        "used_parts":

            self.get_total_used_parts(),

        "parts_profit":

            self.get_used_parts_profit(),

    }