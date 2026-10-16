from decimal import Decimal

from django.db.models import F
from inventory.models import Part


class InventoryReportService:
    @staticmethod
    def _parts():
        return Part.objects.all()

    @staticmethod
    def get_total_inventory_value():
        return sum((Decimal(str(part.stock or 0)) * Decimal(str(part.purchase_price or 0)) for part in InventoryReportService._parts()), Decimal("0"))

    @staticmethod
    def get_total_sale_value():
        return sum((Decimal(str(part.stock or 0)) * Decimal(str(part.sale_price or 0)) for part in InventoryReportService._parts()), Decimal("0"))

    @staticmethod
    def get_potential_profit():
        return InventoryReportService.get_total_sale_value() - InventoryReportService.get_total_inventory_value()

    @staticmethod
    def get_low_stock_parts():
        return Part.objects.filter(stock__lte=F("minimum_stock")).order_by("stock", "title")

    @staticmethod
    def get_out_of_stock_parts():
        return Part.objects.filter(stock=0).order_by("title")

    @staticmethod
    def get_total_parts_count():
        return Part.objects.count()

    @staticmethod
    def get_total_stock_count():
        return sum(int(part.stock or 0) for part in InventoryReportService._parts())

    @staticmethod
    def get_low_stock_alert_count():
        return InventoryReportService.get_low_stock_parts().count()

    @staticmethod
    def get_stock_by_category():
        result = {}
        for part in InventoryReportService._parts():
            category = str(getattr(part, "category", "") or "بدون دسته‌بندی").strip()
            result[category] = result.get(category, 0) + int(part.stock or 0)
        return result

    @staticmethod
    def get_expensive_parts(limit=10):
        return Part.objects.order_by("-sale_price", "title")[:limit]

    @staticmethod
    def inventory_summary():
        stock_by_category = InventoryReportService.get_stock_by_category()
        return {
            "total_inventory_value": InventoryReportService.get_total_inventory_value(),
            "total_sale_value": InventoryReportService.get_total_sale_value(),
            "potential_profit": InventoryReportService.get_potential_profit(),
            "total_parts": InventoryReportService.get_total_parts_count(),
            "total_stock": InventoryReportService.get_total_stock_count(),
            "low_stock_alerts": InventoryReportService.get_low_stock_alert_count(),
            "out_of_stock_parts": InventoryReportService.get_out_of_stock_parts().count(),
            "stock_by_category": stock_by_category,
        }
