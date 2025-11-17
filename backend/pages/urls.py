from django.urls import path

from pages.views import HomePageView, healthz


app_name = "pages"

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("home", HomePageView.as_view(), name="home"),
]
