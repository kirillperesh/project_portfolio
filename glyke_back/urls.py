from django.urls import path

from folio_back import views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path("", views.Home.as_view(), name="home"),
    path("sign_up", views.SignUpView.as_view(), name="sign_up"),
    path("sign_in", views.SignInView.as_view(), name="sign_in"),
    path("logout", LogoutView.as_view(), name="logout"),
]
