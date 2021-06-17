from django.http import HttpResponse


def custom_404_view(request, exception):
    response = HttpResponse('custom 404')
    response.status_code = 404
    return response
