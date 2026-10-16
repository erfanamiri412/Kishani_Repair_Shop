# from constants import CRMEvents

# class AutomationBuilder:

#     @staticmethod
#     def interaction_created(
#         *,
#         normalized_data,
#         is_system=False,
#         followup=None,
#         reminder=None,
#     ):

#         events = []

#         events.append({

#             "event": CRMEvents.INTERACTION_CREATED,

#             "payload": normalized_data,

#         })

#         if is_system:

#             events.append({

#                 "event": CRMEvents.SYSTEM_INTERACTION_CREATED,

#                 "payload": normalized_data,

#             })

#         else:

#             events.append({

#                 "event": CRMEvents.USER_INTERACTION_CREATED,

#                 "payload": normalized_data,

#             })

#         if followup:

#             events.append({

#                 "event": "interaction_followup_related",

#                 "payload": normalized_data,

#             })

#         if reminder:

#             events.append({

#                 "event": "interaction_reminder_related",

#                 "payload": normalized_data,

#             })

#         return events