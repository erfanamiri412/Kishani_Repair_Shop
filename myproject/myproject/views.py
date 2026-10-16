from django.shortcuts import render


def home(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def service_request(request):
    return render(request, 'request.html')


def services(request):
    return render(request, 'services.html')


def service_details_1(request):
    return render(request, 'service-details-1.html')


def service_details_2(request):
    return render(request, 'service-details-2.html')


def service_details_3(request):
    return render(request, 'service-details-3.html')


def service_details_4(request):
    return render(request, 'service-details-4.html')


def service_details_5(request):
    return render(request, 'service-details-5.html')


def service_details_6(request):
    return render(request, 'service-details-6.html')