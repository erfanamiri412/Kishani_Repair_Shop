from django.contrib import messages
from django.shortcuts import render, redirect

from crm.forms import WebsiteServiceRequestForm

from crm.services import (
    CustomerServiceRequestService,
)
def service_request(request):

    if request.method != "POST":

        return redirect(
            "request"
        )


    form = WebsiteServiceRequestForm(
        request.POST,
        request.FILES,
    )


    # =========================================
    # Validation Error
    # =========================================

    if not form.is_valid():

        return render(
            request,
            "request.html",
            {
                "form": form,
            },
            status=400,
        )


    data = form.cleaned_data.copy()


    # =========================================
    # Plate
    # =========================================

    data["plate_number"] = (
        f'{data.get("plate_city", "")}'
        f'{data.get("plate_letter", "")}'
        f'{data.get("plate_middle", "")}'
        f'{data.get("plate_right", "")}'
    )


    # =========================================
    # Metadata
    # =========================================

    data["source"] = "website"

    data["preferred_contact_time"] = "any"

    data["client_ip"] = request.META.get(
        "REMOTE_ADDR"
    )

    data["user_agent"] = request.META.get(
        "HTTP_USER_AGENT",
        "",
    )


    # =========================================
    # CRM
    # =========================================

    try:

        CustomerServiceRequestService.create(
            validated_data=data,
            performed_by=(
                request.user
                if request.user.is_authenticated
                else None
            ),
        )

    except Exception:

        import traceback

        traceback.print_exc()

        messages.error(
            request,
            "در ثبت درخواست مشکلی به وجود آمد.",
        )

        return render(
            request,
            "request.html",
            {
                "form": form,
            },
            status=500,
        )


    # =========================================
    # Success
    # =========================================

    messages.success(
        request,
        "درخواست شما با موفقیت ثبت شد.",
    )

    return redirect(
        "home"
    )