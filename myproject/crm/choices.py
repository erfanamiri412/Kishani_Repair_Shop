from django.db import models

class BaseTextChoices(models.TextChoices):
    """
    Base class for all CRM enums.
    Provides reusable helper methods.
    """

    @classmethod
    def values(cls):
        """
        Returns all enum values as a set.
        """

        return {value for value, _ in cls.choices}

    @classmethod
    def labels(cls):
        """
        Returns all labels.
        """

        return {label for _, label in cls.choices}

    @classmethod
    def choices_dict(cls):
        """
        Returns choices as dictionary.
        """

        return dict(cls.choices)

    @classmethod
    def exists(cls, value):
        """
        Checks if value exists.
        """

        if value is None:
            return False

        return str(value).strip().lower() in cls.values()

    @classmethod
    def normalize(cls, value, default=None):
        """
        Normalizes enum values.

        Raises ValueError if invalid.
        """

        if value is None:

            if default is not None:
                return default

            return None

        value = str(value).strip().lower()

        if value not in cls.values():

            raise ValueError(

                f"{value} is not a valid {cls.__name__}"

            )

        return value
   

class AutomationEvent(BaseTextChoices):

    FOLLOWUP_CREATED = (

        "followup_created",

        "Follow-up Created",

    )

    FOLLOWUP_COMPLETED = (

        "followup_completed",

        "Follow-up Completed",

    )

    STATUS_CHANGED = (

        "status_changed",

        "Status Changed",

    )

    INTERACTION_CREATED = (

        "interaction_created",

        "Interaction Created",

    )

    @classmethod
    def values(cls):

        return {value for value, _ in cls.choices}
    

class AuditAction(BaseTextChoices):

    STATUS_CHANGED = (

        "STATUS_CHANGED",

        "Status Changed",

    )

    FOLLOWUP_CREATED = (

        "FOLLOWUP_CREATED",

        "Follow-up Created",

    )

    FOLLOWUP_COMPLETED = (

        "FOLLOWUP_COMPLETED",

        "Follow-up Completed",

    )

    INTERACTION_CREATED = (

        "INTERACTION_CREATED",

        "Interaction Created",

    )

    REMINDER_CREATED = (

        "REMINDER_CREATED",

        "Reminder Created",

    )

    REMINDER_COMPLETED = (

        "REMINDER_COMPLETED",

        "Reminder Completed",

    )


    @classmethod
    def values(cls):

        return {value for value, _ in cls.choices}


class ServiceType(BaseTextChoices):

    DIAGNOSTIC = (
        "diagnostic",
        "عیب‌یابی",
    )

    PERIODIC_SERVICE = (
        "periodic_service",
        "سرویس دوره‌ای",
    )

    ENGINE_TUNING = (
        "engine_tuning",
        "تنظیم موتور",
    )

    ENGINE_REPAIR = (
        "engine_repair",
        "تعمیر موتور",
    )

    CLUTCH = (
        "clutch",
        "کیت کلاچ",
    )

    OTHER = (
        "other",
        "سایر",
    )
