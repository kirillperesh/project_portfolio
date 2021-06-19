from django.http import HttpResponse
from django.views.generic import TemplateView


def custom_404_view(request, exception):
    response = HttpResponse('custom 404')
    response.status_code = 404
    return response

class SmthWentWrong(TemplateView):
    http_method_names = ['get', ]
    template_name = 'smth_went_wrong.html'
