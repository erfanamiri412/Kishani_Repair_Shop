class ServiceRequestWorkflow:

    STEPS = (

        "create_followup",

        "create_reminder",

        "create_audit",

        "create_notifications",

        "run_automation",

    )

    @classmethod
    def execute(
        cls,
        service,
        context,
    ):

        for step in cls.STEPS:

            getattr(
                service,
                f"_{step}",
            )(context)

