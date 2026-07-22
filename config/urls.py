"""URL configuration for Brainiac Proctored Smart Assessment Portal."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('assessments/', include('assessments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
