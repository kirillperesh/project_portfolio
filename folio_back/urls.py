from django.urls import path

from folio_back import views


urlpatterns = [
    path("portfolio", views.Home.as_view(), name="portfolio"),
    path("add_tile", views.AddTileView.as_view(), name="add_tile"),
    path("<slug:slug>/edit_tile", views.EditTileView.as_view(), name="edit_tile"),
    path("delete_tile", views.DeleteTileView.as_view(), name="delete_tile"),
    path("tiles", views.TilesView.as_view(), name="tiles"),
    path("<str:username>/tiles", views.ProfileTilesView.as_view(), name="profile_tiles"),
]
