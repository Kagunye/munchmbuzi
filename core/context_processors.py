import os
from pathlib import Path

from django.utils import timezone

from .models import Branch, MusicTrack

SOCIAL_LINKS = [
    {"name": "Instagram", "icon": "instagram", "url": "https://www.instagram.com/mbuzi_munch/"},
    {"name": "Facebook", "icon": "facebook", "url": "https://www.facebook.com/mbuzimunch/"},
    {"name": "X / Twitter", "icon": "x", "url": "https://twitter.com/MbuziMunch"},
    {
        "name": "TripAdvisor",
        "icon": "tripadvisor",
        "url": "https://www.tripadvisor.co.uk/Restaurant_Review-g12559418-d19866300-Reviews-Mbuzi_Munch_Galleria-Karen_Nairobi.html",
    },
]

DELIVERY_PARTNERS = [
    {"name": "Bolt Food", "logo": "img/bolt.png", "url": "https://food.bolt.eu/en-us/"},
    {"name": "Glovo", "logo": "img/glovo.png", "url": "https://glovoapp.com/"},
    {"name": "Uber Eats", "logo": "img/ubereats.png", "url": "https://www.ubereats.com/ke"},
]


ASSET_FILES = ("css/site.css", "js/site.js", "js/music.js", "js/experience.js")


_version_cache = {}


def asset_version():
    """A short hash of the site's CSS/JS contents, used as ?v= on their URLs.
    It changes whenever those files change, so browsers never keep a stale copy.
    (Content, not timestamps: deployment bundles don't keep real file times.)"""
    import hashlib

    from django.conf import settings

    base = Path(settings.BASE_DIR) / "static"
    files = [base / f for f in ASSET_FILES if (base / f).exists()]
    key = tuple((str(f), f.stat().st_mtime_ns, f.stat().st_size) for f in files)
    if key not in _version_cache:
        digest = hashlib.sha1()
        for f in files:
            digest.update(f.read_bytes())
        # last resort on a host without the files: the deployed commit
        fallback = os.environ.get("VERCEL_GIT_COMMIT_SHA", "1")[:10]
        _version_cache.clear()
        _version_cache[key] = digest.hexdigest()[:10] if files else fallback
    return _version_cache[key]


def site(request):
    return {
        "asset_v": asset_version(),
        "music_track": MusicTrack.objects.filter(is_active=True).exclude(audio="").first(),
        "nav_branches": Branch.objects.filter(is_active=True),
        "social_links": SOCIAL_LINKS,
        "delivery_partners": DELIVERY_PARTNERS,
        "current_year": timezone.localdate().year,
        "menu_pdf": "docs/mbuzi-munch-menu.pdf",
    }
