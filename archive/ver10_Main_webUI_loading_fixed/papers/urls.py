# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path("loading/<int:paper_id>/", views.loading_page, name="loading_page"),
    path("check_status/<int:paper_id>/", views.check_processing_status, name="check_processing_status"),
    path("viewer/", views.viewer_default_view, name="viewer"),
    path("viewer/<int:paper_id>/", views.viewer_view, name="viewer_detail"),
    path('settings/', views.settings_view, name='settings'),
]
