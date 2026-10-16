from django.contrib import admin
from django.urls import (
    path,
    include,
)

from . import views

from crm.views import (
    service_request as submit_service_request,
)

from crm.admin_views import (
    KishaniAutocompleteJsonView,
)


urlpatterns = [

    # ==========================================================
    # Admin Autocomplete
    # ==========================================================

    path(
        'admin/autocomplete/',
        KishaniAutocompleteJsonView.as_view(
            admin_site=admin.site,
        ),
        name='admin-autocomplete',
    ),

    # ==========================================================
    # Django Admin
    # ==========================================================

    path(
        'admin/',
        admin.site.urls,
    ),

    # ==========================================================
    # Website
    # ==========================================================

    path(
        '',
        views.home,
        name='home',
    ),

    path(
        'about/',
        views.about,
        name='about',
    ),

    # ==========================================================
    # Service Request
    # ==========================================================

    path(
        'request/',
        views.service_request,
        name='request',
    ),

    # ==========================================================
    # Service Request Submit
    # ==========================================================

    path(
        'service-request/',
        submit_service_request,
        name='service_request',
    ),

    # ==========================================================
    # Services
    # ==========================================================

    path(
        'services/',
        views.services,
        name='services',
    ),

    # ==========================================================
    # Service Details
    # ==========================================================

    path(
        'service-details-1/',
        views.service_details_1,
        name='service_details_1',
    ),

    path(
        'service-details-2/',
        views.service_details_2,
        name='service_details_2',
    ),

    path(
        'service-details-3/',
        views.service_details_3,
        name='service_details_3',
    ),

    path(
        'service-details-4/',
        views.service_details_4,
        name='service_details_4',
    ),

    path(
        'service-details-5/',
        views.service_details_5,
        name='service_details_5',
    ),

    path(
        'service-details-6/',
        views.service_details_6,
        name='service_details_6',
    ),

    # ==========================================================
    # CRM URLs
    # ==========================================================

    path(
        'crm/',
        include(
            'crm.urls'
        ),
    ),
]