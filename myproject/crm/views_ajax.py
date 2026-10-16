from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from crm.models import CustomerVehicle


def customer_vehicles(request, customer_id):

    vehicles = (
        CustomerVehicle.objects
        .filter(
            customer_id=customer_id
        )
        .order_by(
            "brand",
            "model",
        )
    )

    data = []

    for vehicle in vehicles:

        vehicle_name = " ".join(
            part
            for part in (
                vehicle.brand,
                vehicle.model,
            )
            if part
        )

        if vehicle.plate_number:
            vehicle_name = (
                f"{vehicle_name} "
                f"({vehicle.plate_number})"
            )

        data.append(
            {
                "id": vehicle.pk,
                "text": vehicle_name.strip(),
            }
        )

    return JsonResponse(
        data,
        safe=False,
    )