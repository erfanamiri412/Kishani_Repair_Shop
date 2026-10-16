from django.urls import path
# from crm.views import service_request
from crm import views_ajax
from .invoice_views import (
    invoice_preview,
    invoice_print,
)

urlpatterns = [

    path(
        "ajax/customer/<int:customer_id>/vehicles/",
        views_ajax.customer_vehicles,
        name="customer_vehicles",
    ),

    # ==================================================
    # Invoice Preview
    # ==================================================

    path(
        "invoice/<int:invoice_id>/preview/",
        invoice_preview,
        name="invoice_preview",
    ),

    # ==================================================
    # Invoice Print
    # ==================================================

    path(
        "invoice/<int:invoice_id>/print/",
        invoice_print,
        name="invoice_print",
    ),

    # path(
    #     "service-request/",
    #     service_request,
    #     name="service_request",
    # ),
]

