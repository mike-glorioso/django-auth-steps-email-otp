from django.urls import path

from . import views

app_name = "accounts"


def register_robots():
    return [("User-Agent *", "Disallow /admin/")]


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("setup/", views.setup_view, name="setup"),
    path("logout/", views.logout_view, name="logout"),
]
