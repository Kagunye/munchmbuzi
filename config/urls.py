from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from core.sitemaps import PostSitemap, StaticSitemap

sitemaps = {"static": StaticSitemap, "news": PostSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    # Keep old Wix URLs working so existing links and Google results don't break.
    path("copy-of-mbuzi-munch-the-finest-nyama", RedirectView.as_view(pattern_name="core:branches", permanent=True)),
    path("contact-1", RedirectView.as_view(pattern_name="core:book", permanent=True)),
    path("copy-of-contact", RedirectView.as_view(pattern_name="core:careers", permanent=True)),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.page_not_found"
