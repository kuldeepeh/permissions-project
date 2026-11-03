from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/capture/", views.capture_event, name="capture_event"),
]
