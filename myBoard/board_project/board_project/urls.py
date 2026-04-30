# myDjango/writing_project/writing_project/urls.py

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("board.urls")),
]
