class CRMEvents:

    FOLLOWUP_CREATED = "followup_created"

    FOLLOWUP_COMPLETED = "followup_completed"

    FOLLOWUP_CANCELLED = "followup_cancelled"

    REMINDER_CREATED = "reminder_created"

    REMINDER_COMPLETED = "reminder_completed"

    INTERACTION_CREATED = "interaction_created"

    STATUS_CHANGED = "status_changed"

    CUSTOMER_ASSIGNED = "customer_assigned"

    CUSTOMER_BLACKLISTED = "customer_blacklisted"

    SYSTEM_GENERATED_FOLLOWUP = "system_generated_followup"

    USER_INTERACTION_CREATED = "user_interaction_created"

    SYSTEM_INTERACTION_CREATED = "system_interaction_created"


class CRMAuditActions:

    STATUS_CHANGED = "STATUS_CHANGED"

    SERVICE_REQUEST_CREATED = "SERVICE_REQUEST_CREATED"

    FOLLOWUP_CREATED = "FOLLOWUP_CREATED"

    FOLLOWUP_COMPLETED = "FOLLOWUP_COMPLETED"

    FOLLOWUP_CANCELLED = "FOLLOWUP_CANCELLED"

    INTERACTION_CREATED = "INTERACTION_CREATED"

    REMINDER_CREATED = "REMINDER_CREATED"

    REMINDER_COMPLETED = "REMINDER_COMPLETED"
class CRMLimits:

    INTERACTION_SUBJECT = 255

    INTERACTION_MESSAGE = 10000

    INTERACTION_RESULT = 5000

    FOLLOWUP_TITLE = 255

    FOLLOWUP_DESCRIPTION = 10000

    CUSTOMER_NOTE = 10000

class CRMDefaults:

    FOLLOWUP_AFTER_DAYS = 7

    REMINDER_AFTER_DAYS = 7

    PAGE_SIZE = 25

class CRMSources:

    CRM = "crm"

    WEBSITE = "website"

    API = "api"

    AI = "ai"

    SYSTEM = "system"