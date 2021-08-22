from django.urls import path

# from folio_back import views as old
from glyke_back import views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path("", views.Home.as_view(), name="home"),
    path("sign_up", views.SignUpView.as_view(), name="sign_up"),
    path("sign_in", views.SignInView.as_view(), name="sign_in"),
    path("logout", LogoutView.as_view(), name="logout"),

    path("add_product", views.add_product_dynamic_view, name="add_product"),
    path("edit_product/<int:id>", views.edit_product_dynamic_view, name="edit_product"),
    path("product/<int:id>", views.ProductDetailView.as_view(), name="product_details"),
    path("delete_product/<int:id>", views.delete_product_view, name="delete_product"),
    path("products", views.ProductsView.as_view(), name="products"),
    path("products_staff", views.ProductsStaffView.as_view(), name="products_staff"),
    
    path("cart", views.cart_view, name="cart"),
    path("add_to_cart", views.AddToCartView.as_view(), name="add_to_cart"),
    path("clear_cart/<int:id>", views.clear_cart_view, name="clear_cart"),
]

