from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import WebsiteServiceRequestForm
from .services import CustomerServiceRequestService


def get_client_ip(request):
    """
    دریافت IP کاربر.

    در صورت وجود Reverse Proxy / Load Balancer
    ابتدا X-Forwarded-For بررسی می‌شود.
    """

    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get(
        "REMOTE_ADDR"
    )


def service_request(request):

    # =====================================================
    # فقط POST
    # =====================================================

    if request.method != "POST":
        return redirect("request")

    # =====================================================
    # Form
    # =====================================================

    form = WebsiteServiceRequestForm(
        request.POST,
        request.FILES,
    )

    # =====================================================
    # Validation
    # =====================================================

    if not form.is_valid():

        return render(
            request,
            "request.html",
            {
                "form": form,
            },
            status=400,
        )

    # =====================================================
    # Clean Data
    # =====================================================

    data = form.cleaned_data.copy()

    # =====================================================
    # Plate Number
    # =====================================================

    data["plate_number"] = "".join(
        (
            str(data.get("plate_city") or ""),
            str(data.get("plate_letter") or ""),
            str(data.get("plate_middle") or ""),
            str(data.get("plate_right") or ""),
        )
    )

    # =====================================================
    # Request Metadata
    # =====================================================

    data.update(
        {
            "source": "website",
            "preferred_contact_time": "any",
            "client_ip": get_client_ip(request),
            "user_agent": request.META.get(
                "HTTP_USER_AGENT",
                "",
            ),
        }
    )

    # =====================================================
    # Business Service
    # =====================================================

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

        import logging

        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to create customer service request."
        )

        messages.error(
            request,
            (
                "در ثبت درخواست مشکلی به وجود آمد. "
                "لطفاً دوباره تلاش کنید."
            ),
        )

        return render(
            request,
            "request.html",
            {
                "form": form,
            },
            status=500,
        )

    # =====================================================
    # Success
    # =====================================================

    messages.success(
        request,
        "درخواست شما با موفقیت ثبت شد.",
    )

    # =====================================================
    # PRG Pattern
    # =====================================================

    return redirect("home")