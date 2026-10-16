from django.contrib import admin
from django.utils.html import format_html

from .services import DashboardService


class DashboardAdminSite(admin.AdminSite):

    site_header = "پنل مدیریت تعمیرگاه کیشانی"
    site_title = "داشبورد مدیریت"
    index_title = "داشبورد مدیریتی"


admin_site = DashboardAdminSite(name="dashboard_admin")


@admin.register_view(
    route="dashboard/",
    name="dashboard",
)
def dashboard_view(request):

    stats = DashboardService.آمار_کامل_داشبورد()

    return format_html(
        f"""
        <div style="direction:rtl;padding:20px">

            <h1>📊 داشبورد مدیریتی</h1>

            <hr>

            <h2>💰 اطلاعات مالی</h2>

            <ul>
                <li>درآمد امروز: {stats['درآمد_امروز']:,}  تومان</li>
                <li>درآمد ماه: {stats['درآمد_ماه']:,}  تومان</li>
                <li>درآمد سال: {stats['درآمد_سال']:,}  تومان</li>
                <li>سود ماه: {stats['سود_ماه']:,}  تومان</li>
                <li>سود سال: {stats['سود_سال']:,}  تومان</li>
            </ul>

            <hr>

            <h2>🚗 وضعیت تعمیرگاه</h2>

            <ul>
                <li>خودروهای پذیرش شده امروز:
                    {stats['خودروهای_پذیرش_شده']}
                </li>

                <li>خودروهای تحویل شده امروز:
                    {stats['خودروهای_تحویل_شده']}
                </li>

                <li>خودروهای در حال تعمیر:
                    {stats['خودروهای_درحال_تعمیر']}
                </li>

                <li>فاکتورهای تسویه نشده:
                    {stats['فاکتورهای_تسویه_نشده']}
                </li>
            </ul>

            <hr>

            <h2>👨‍🔧 عملکرد پرسنل</h2>

            <ul>

                <li>
                    بهترین تکنسین:
                    {stats['بهترین_تکنسین']}
                </li>

                <li>
                    محبوب‌ترین خدمت:
                    {stats['محبوب_ترین_خدمت']}
                </li>

                <li>
                    میانگین رضایت مشتری:
                    {round(stats['میانگین_رضایت_مشتریان'], 2)}
                </li>

                <li>
                    مراجعات مجدد:
                    {stats['مراجعات_مجدد']}
                </li>

            </ul>

        </div>
        """
    )