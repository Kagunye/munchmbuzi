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


def asset_version():
    """Changes whenever the site's CSS/JS changes, so browsers never run stale copies."""
    from django.conf import settings

    base = Path(settings.BASE_DIR) / "static"
    stamps = [int((base / f).stat().st_mtime) for f in ASSET_FILES if (base / f).exists()]
    return str(max(stamps)) if stamps else "1"


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
