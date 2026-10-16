from collections import OrderedDict

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from .models import Invoice


def _get_invoice(invoice_id):

    return get_object_or_404(
        Invoice.objects
        .select_related(
            "repair",
            "repair__customer",
            "repair__vehicle",
        )
        .prefetch_related(
            "items__mechanic",
            "payments__received_by",
        ),
        pk=invoice_id,
    )


def _group_invoice_items(invoice):

    grouped_items = OrderedDict()

    for item in invoice.items.all():

        category = item.get_item_type_display()

        grouped_items.setdefault(
            category,
            [],
        ).append(item)

    return grouped_items.items()


@staff_member_required
def invoice_preview(request, invoice_id):

    invoice = _get_invoice(invoice_id)

    return render(
        request,
        "invoice/preview.html",
        {
            "invoice": invoice,
            "grouped_items": _group_invoice_items(
                invoice
            ),
        },
    )


@staff_member_required
def invoice_print(request, invoice_id):

    invoice = _get_invoice(invoice_id)

    return render(
        request,
        "invoice/print.html",
        {
            "invoice": invoice,
            "grouped_items": _group_invoice_items(
                invoice
            ),
        },
    )