from django.http import HttpResponse
from django.views.generic import TemplateView


def custom_404_view(request, exception):
    response = HttpResponse('custom 404')
    response.status_code = 404
    return response

class SmthWentWrong(TemplateView):
    http_method_names = ['get', ]
    template_name = 'smth_went_wrong.html'
    def get(self, request, *args, **kwargs):
        print(kwargs)
        print(request.GET)
        print(self.kwargs)
        # self.extra_context = {'error_suffix': kwargs['error_suffix']}
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print(self.kwargs)
        return super().get_context_data(**kwargs)
