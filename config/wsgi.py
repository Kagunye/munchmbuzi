"""
WSGI config for the Mbuzi Munch website.

It exposes the WSGI callable as ``application`` (and ``app`` for Vercel).
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()


def _bootstrap_database():
    """On Vercel, make sure the database is ready when a server starts:
    apply any missing migrations and load the site content if it's empty.
    This covers a database that was connected after the last build."""
    from django.conf import settings

    if not getattr(settings, "ON_VERCEL", False) or os.environ.get("MBUZI_SKIP_BOOTSTRAP"):
        return
    log = logging.getLogger("mbuzimunch.bootstrap")
    try:
        from django.core.management import call_command

        call_command("migrate", interactive=False, verbosity=0)
        from core.models import Branch

        if not Branch.objects.exists():
            log.warning("Database is empty: loading Mbuzi Munch content.")
            call_command("seed_site", verbosity=0)
    except Exception:  # never stop the site from starting; the error goes to the logs
        log.exception("Database bootstrap failed")


_bootstrap_database()

# Vercel's Python runtime looks for a variable called "app".
app = application
