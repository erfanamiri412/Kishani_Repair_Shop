from django.http import JsonResponse
from inventory.models import Part


def part_price(request):

    part_id = request.GET.get("part_id")

    if not part_id:
        return JsonResponse({
            "price": 0,
        })

    try:
        part = Part.objects.get(
            pk=part_id
        )
    except Part.DoesNotExist:
        return JsonResponse({
            "price": 0,
        })

    return JsonResponse({
        "price": int(
            part.sale_price or 0
        ),
    })