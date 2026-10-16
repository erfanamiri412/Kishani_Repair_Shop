class BasePipeline:

    STEPS = ()

    @classmethod
    def execute(
        cls,
        *,
        service,
        context,
    ):

        for step in cls.STEPS:

            method = getattr(

                service,

                f"_{step}",

            )

            result = method(

                context=context,

            )

            if result is not None:

                setattr(

                    context,

                    step,

                    result,

                )

        return context
    
class ServiceRequestPipeline(BasePipeline):

    STEPS = (

        "create_followup",

        "create_reminder",

        "create_audit",

        "create_notifications",

        "run_automation",

    )