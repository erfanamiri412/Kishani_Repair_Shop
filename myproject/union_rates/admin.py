# from django.contrib import admin

# from .models import Vehicle, UnionService, UnionRate



# @admin.register(Vehicle)
# class VehicleAdmin(admin.ModelAdmin):

#     list_display = (

#         "name",
#         "engine",

#     )


#     search_fields = (

#         "name",
#         "engine",

#     )




# @admin.register(UnionService)
# class UnionServiceAdmin(admin.ModelAdmin):

#     list_display = (

#         "title",
#         "category",

#     )


#     search_fields = (

#         "title",

#     )





# @admin.register(UnionRate)
# class UnionRateAdmin(admin.ModelAdmin):


#     list_display = (

#         "vehicle",
#         "service",
#         "price",
#         "year",

#     )


#     list_filter = (

#         "year",
#         "vehicle",

#     )


#     search_fields = (

#         "vehicle__name",
#         "service__title",

#     )


#     ordering = (

#         "-year",

#     )
