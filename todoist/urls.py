from django.contrib import admin
from django.urls import path, include, re_path

from todolist.api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('admin_tools_stats/', include('admin_tools_stats.urls')),
    path('admin_tools/', include('admin_tools.urls')),
]
