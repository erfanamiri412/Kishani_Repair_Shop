from communications.services import CommunicationService

from .engine import MaintenanceEngine


def run_daily_cycle(*, as_of=None, dry_run=False, limit=100):
    """اجرای تحلیل روزانه و پردازش صف پیامک با رعایت بازه قواعد هوشمند."""
    evaluation = MaintenanceEngine().evaluate(
        as_of=as_of,
        dry_run=dry_run,
    )

    if dry_run:
        sending = {
            "total": 0,
            "success_count": 0,
            "failed_count": 0,
        }
    else:
        sending = CommunicationService().send_pending_messages(
            limit=limit,
        )

    return {
        "evaluation": evaluation,
        "sending": sending,
    }
