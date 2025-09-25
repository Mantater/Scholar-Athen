from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("viewer/<int:paper_id>/", views.viewer_view, name="viewer"),
    path("export/<int:paper_id>/<str:fmt>/", views.export_view, name="export"),
    path('settings/', views.settings_view, name='settings'),
]
