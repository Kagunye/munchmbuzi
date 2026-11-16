from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Post


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["core:home", "core:experience", "core:menu", "core:branches", "core:book", "core:events",
                "core:about", "core:careers", "core:news"]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Post.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.published_at
