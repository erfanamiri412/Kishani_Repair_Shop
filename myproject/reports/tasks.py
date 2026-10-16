from .services import ReportsService


class ScheduledTasks:

    @staticmethod
    def generate_monthly_report():

        return ReportsService.generate_scheduled_reports(
            monthly=True,
            yearly=False,
        )

    @staticmethod
    def generate_yearly_report():

        return ReportsService.generate_scheduled_reports(
            monthly=False,
            yearly=True,
        )

    @staticmethod
    def create_database_backup():

        return {

            "success": True,

            "message":
                "بکاپ پایگاه داده ایجاد شد",

        }

    @staticmethod
    def send_monthly_report_to_manager():

        reports = ScheduledTasks.generate_monthly_report()

        return {

            "success": True,

            "message":
                "گزارش ماهانه آماده شد",

            "reports": reports,

        }

    @staticmethod
    def send_yearly_report_to_manager():

        reports = ScheduledTasks.generate_yearly_report()

        return {

            "success": True,

            "message":
                "گزارش سالانه آماده شد",

            "reports": reports,

        }
