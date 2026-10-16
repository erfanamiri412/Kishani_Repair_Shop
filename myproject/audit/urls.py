from django.urls import path
from .views import part_price

urlpatterns = [
    path(
        "part-price/",
        part_price,
        name="part_price",
    ),
]