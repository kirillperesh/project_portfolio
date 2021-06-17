from django.urls import path

from folio_back import views as old
from glyke_back import views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path("", old.Home.as_view(), name="home"),
    path("sign_up", old.SignUpView.as_view(), name="sign_up"),
    path("sign_in", old.SignInView.as_view(), name="sign_in"),
    path("logout", LogoutView.as_view(), name="logout"),

    path("add_product", views.add_product_dynamic_view, name="add_product")
]

