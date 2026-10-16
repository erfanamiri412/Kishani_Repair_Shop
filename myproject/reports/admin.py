from django.contrib import admin
from django.http import FileResponse, Http404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from core.admin import BaseModelAdmin

from .models import (
    ReportHistory,
    BackupHistory,
)
from .services import ReportsService


# ==========================================================
# Report History Admin
# ==========================================================

@admin.register(ReportHistory)
class ReportHistoryAdmin(
    BaseModelAdmin,
):

    list_display = (
        "title_display",
        "report_type_display",
        "period_display",
        "report_format_display",
        "created_at",
        "preview_link",
        "print_link",
    )

    list_filter = (
        "report_type",
        "period_year",
        "period_month",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "file_name",
        "generation_key",
    )

    readonly_fields = (
        "title",
        "report_type",
        "report_format",
        "file_name",
        "file_path",
        "file_size",
        "description",
        "period_year",
        "period_month",
        "period_start",
        "period_end",
        "generation_key",
        "snapshot",
        "chart_data",
        "created_at",
        "created_by",
        "preview_link",
        "print_link",
    )

    fieldsets = (
        (
            "اطلاعات اصلی گزارش",
            {
                "fields": (
                    "title",
                    "report_type",
                    "report_format",
                    "created_at",
                    "created_by",
                ),
            },
        ),
        (
            "دوره گزارش",
            {
                "fields": (
                    "period_year",
                    "period_month",
                    "period_start",
                    "period_end",
                ),
            },
        ),
        (
            "فایل گزارش",
            {
                "fields": (
                    "file_name",
                    "file_path",
                    "file_size",
                    "preview_link",
                    "print_link",
                ),
            },
        ),
        (
            "اطلاعات ثابت و تحلیل",
            {
                "fields": (
                    "description",
                    "generation_key",
                    "snapshot",
                    "chart_data",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    list_per_page = 30

    save_on_top = False

    date_hierarchy = "created_at"

    empty_value_display = "-"


    # =====================================================
    # Queryset
    # =====================================================

    def get_queryset(
        self,
        request,
    ):

        return (
            super()
            .get_queryset(request)
            .filter(
                report_type__in=(
                    "monthly",
                    "yearly",
                )
            )
        )

    # =====================================================
    # Title
    # =====================================================

    @admin.display(
        description="عنوان گزارش",
    )
    def title_display(
        self,
        obj,
    ):

        if not obj.pk:
            return obj.title

        url = reverse(
            "admin:reports_reporthistory_preview",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}" '
            'target="_blank" '
            'style="font-weight:700;">'
            '{}'
            '</a>',
            url,
            obj.title,
        )

    # =====================================================
    # Report Type
    # =====================================================

    @admin.display(
        description="نوع گزارش",
        ordering="report_type",
    )
    def report_type_display(
        self,
        obj,
    ):

        return obj.get_report_type_display()

    # =====================================================
    # Period
    # =====================================================

    @admin.display(
        description="دوره",
    )
    def period_display(
        self,
        obj,
    ):

        if obj.period_year and obj.period_month:

            from .periods import jalali_month_label

            return jalali_month_label(
                obj.period_year,
                obj.period_month,
            )

        if obj.period_year:
            return f"سال {obj.period_year}"

        return "-"

    # =====================================================
    # Report Format
    # =====================================================

    @admin.display(
        description="فرمت",
        ordering="report_format",
    )
    def report_format_display(
        self,
        obj,
    ):

        return obj.get_report_format_display()

    # =====================================================
    # Custom Admin URLs
    # =====================================================

    def get_urls(
        self,
    ):

        urls = super().get_urls()

        custom_urls = [

            path(
                "<path:object_id>/preview/",
                self.admin_site.admin_view(
                    self.preview_view
                ),
                name="reports_reporthistory_preview",
            ),

            path(
                "<path:object_id>/print/",
                self.admin_site.admin_view(
                    self.print_view
                ),
                name="reports_reporthistory_print",
            ),

            path(
                "<path:object_id>/pdf/",
                self.admin_site.admin_view(
                    self.pdf_view
                ),
                name="reports_reporthistory_pdf",
            ),

        ]

        return custom_urls + urls

    # =====================================================
    # Shared Report Loader
    # =====================================================

    def get_report(
        self,
        request,
        object_id,
    ):

        return self.get_object(
            request,
            object_id,
        )

    # =====================================================
    # Preview
    # =====================================================

    def preview_view(
        self,
        request,
        object_id,
    ):

        report = self.get_report(
            request,
            object_id,
        )

        if not report:
            raise Http404

        from .pdf_generator import (
            PDFReportGenerator,
        )

        generator = PDFReportGenerator()

        context = {
            **self.admin_site.each_context(
                request
            ),

            **generator.build_context(
                report.snapshot or {},
            ),

            "report_history": report,

        }

        return TemplateResponse(
            request,
            "reports/report_print.html",
            context,
        )
        
    # =====================================================
    # Print
    # =====================================================

    def print_view(
        self,
        request,
        object_id,
    ):

        report = self.get_report(
            request,
            object_id,
        )

        if not report:
            raise Http404

        from .pdf_generator import (
            PDFReportGenerator,
        )

        generator = PDFReportGenerator()

        context = {
            **self.admin_site.each_context(
                request
            ),

            **generator.build_context(
                report.snapshot or {},
                auto_print=True,
            ),

            "report_history": report,

        }

        return TemplateResponse(
            request,
            "reports/report_print.html",
            context,
        )
    
    # =====================================================
    # PDF
    # =====================================================

    def pdf_view(
        self,
        request,
        object_id,
    ):

        report = self.get_report(
            request,
            object_id,
        )

        if not report or not report.file_path:
            raise Http404

        try:
            file_object = ReportsService._get_report_file_object(
                report
            )
        except FileNotFoundError:
            raise Http404

        response = FileResponse(
            file_object,
            content_type="application/pdf",
        )

        response["Content-Disposition"] = (
            f'inline; filename="{report.file_name or "report.pdf"}"'
        )

        return response

    # =====================================================
    # Preview Link
    # =====================================================

    @admin.display(
        description="پیش‌نمایش",
    )
    def preview_link(
        self,
        obj,
    ):

        if not obj.pk:
            return "-"

        url = reverse(
            "admin:reports_reporthistory_preview",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}" '
            'target="_blank" '
            'style="font-weight:700;">'
            'مشاهده'
            '</a>',
            url,
        )
    
    # =====================================================
    # Print Link
    # =====================================================

    @admin.display(
        description="چاپ",
    )
    def print_link(
        self,
        obj,
    ):

        if not obj.pk:
            return "-"

        url = reverse(
            "admin:reports_reporthistory_print",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}" '
            'target="_blank" '
            'style="font-weight:700;">'
            'چاپ'
            '</a>',
            url,
        )
    
    # =====================================================
    # Permissions
    # =====================================================

    def has_add_permission(
        self,
        request,
    ):

        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):

        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):

        return False

    def has_view_permission(
        self,
        request,
        obj=None,
    ):

        return True


# ==========================================================
# Backup History Admin
# ==========================================================