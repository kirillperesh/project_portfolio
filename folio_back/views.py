from typing import ContextManager
from django.http import HttpResponse, HttpRequest, Http404, request
from django.shortcuts import redirect, render, resolve_url
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.urls import reverse
from urllib.parse import urlencode
from django.shortcuts import get_object_or_404, get_list_or_404


from .models import Tile
from .forms import AddEditTileForm, RegisterForm, SignInForm
from folio_back import models


class Home(TemplateView):
    http_method_names = ['get', ]
    template_name = 'home.html'
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class SignUpView(CreateView):
    http_method_names = ['get', 'post']
    model = User
    form_class = RegisterForm
    template_name = 'sign_up.html'

class SignInView(LoginView):
    http_method_names = ['get', 'post']
    authentication_form = SignInForm
    template_name = 'sign_in.html'

class AddTileView(LoginRequiredMixin,CreateView):
    http_method_names = ['get', 'post']
    model = Tile
    form_class = AddEditTileForm
    template_name = 'add_edit_tile.html'
    success_url = '/tiles'

    def post(self, request: HttpRequest, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            tile_instance = form.save(commit=False)
            tile_instance.author = request.user
            tile_instance.save()
            return redirect(self.success_url)
        else:
            self.form_invalid(form)

class EditTileView(UpdateView):
    http_method_names = ['get', 'post']
    model = Tile
    form_class = AddEditTileForm
    template_name = 'add_edit_tile.html'
    success_url = '/tiles'

class TilesView(ListView):
    http_method_names = ['get', ]
    model = Tile
    queryset = model.objects.filter(is_active=True)
    ordering = '-last_modified'
    paginate_by = 8
    template_name = 'tiles.html'
    context_object_name = 'tiles'

    def get_context_data(self, **kwargs):
        context = super(TilesView, self).get_context_data(**kwargs)
        for tile in context['tiles']:
            if self.request.user.is_staff or self.request.user == tile.author:
               tile.perm_edit = True
               tile.perm_del = True
        return context

class ProfileTilesView(TilesView):
    """Based on generic ListView"""

    template_name = 'profile_tiles.html'

    def get_queryset(self):
        author=get_object_or_404(User, username=self.kwargs['username'])
        self.queryset = Tile.objects.filter(author=author)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super(ProfileTilesView, self).get_context_data(**kwargs)
        context['author'] = self.kwargs['username']
        return context

class DeleteTileView(LoginRequiredMixin, RedirectView):
    http_method_names = ['get',]
    pattern_name = 'tiles'

    def get_redirect_url(self, *args, **kwargs):
        if 'slug' not in self.request.GET:
            return f"{reverse('smth_went_wrong')}?{urlencode({'error_suffix': 'tile to delete'})}"
        tile_to_delete = get_object_or_404(Tile, slug=self.request.GET['slug'])
        if self.request.user.is_staff or self.request.user == tile_to_delete.author:
            tile_to_delete.is_active = True if self.request.GET.__contains__('recover') else False
            tile_to_delete.save()
        if self.pattern_name:
            url = reverse(self.pattern_name)
            return url
        raise Http404


