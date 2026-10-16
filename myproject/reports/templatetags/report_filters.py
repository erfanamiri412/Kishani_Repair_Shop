from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def report_money(value):
    if value is None or value == "":
        return "—"
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return "—"
    return f"{number:,.0f} تومان"


@register.filter
def report_number(value):
    if value is None or value == "":
        return "—"
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return "—"
    if number == number.to_integral_value():
        return f"{number:,.0f}"
    return f"{number:,.2f}"


@register.filter
def report_percent(value):
    if value is None or value == "":
        return "—"
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "—"


@register.filter
def jalali_date(value):
    if value is None or value == "":
        return "—"
    try:
        from reports.periods import jalali_date_label
        if hasattr(value, "date") and not hasattr(value, "year"):
            value = value.date()
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return jalali_date_label(value)
    except Exception:
        pass
    return str(value)


@register.filter
def has_value(value):
    return value is not None and value != ""
