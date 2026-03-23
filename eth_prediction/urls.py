# eth_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('predict.urls')),  # Include the prediction app's URLs
]
