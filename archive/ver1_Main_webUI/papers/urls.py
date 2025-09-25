# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),  # handles upload + export
    path("viewer/<int:paper_id>/", views.viewer_view, name="viewer"),
    path('settings/', views.settings_view, name='settings'),
]
