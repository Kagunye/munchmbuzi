import datetime
import shutil
import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Branch, JobApplication, MenuItem, Post, Reservation

TEMP_MEDIA = tempfile.mkdtemp(prefix="mm-test-media-")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def test_pages_render(self):
        for name in ["home", "experience", "menu", "branches", "book", "events", "about", "careers", "news", "book_thanks"]:
            with self.subTest(page=name):
                r = self.client.get(reverse(f"core:{name}"))
                self.assertEqual(r.status_code, 200)

    def test_post_detail_and_sitemap(self):
        post = Post.objects.first()
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)
        self.assertContains(self.client.get("/sitemap.xml"), post.slug)
        self.assertEqual(self.client.get("/robots.txt").status_code, 200)

    def test_old_wix_urls_redirect(self):
        self.assertRedirects(self.client.get("/contact-1"), reverse("core:book"), status_code=301)
        self.assertRedirects(self.client.get("/copy-of-contact"), reverse("core:careers"), status_code=301)

    def test_seed_is_idempotent(self):
        before = MenuItem.objects.count()
        call_command("seed_site", verbosity=0)
        self.assertEqual(MenuItem.objects.count(), before)
        self.assertEqual(Branch.objects.count(), 4)

    def test_experience_builder_uses_menu_prices(self):
        r = self.client.get(reverse("core:experience"))
        builder = r.context["builder"]
        self.assertEqual({len(builder[g]) for g in ("nyama", "side", "drink")}, {6})
        leg = next(o for o in builder["nyama"] if o["label"] == "Mbuzi Leg Deluxe")
        self.assertEqual(leg["price"], 2600)
        kuku = next(o for o in builder["nyama"] if o["label"].startswith("Kuku"))
        self.assertEqual(kuku["price"], 1100)  # "1100 / 2200" -> half chicken price

    def test_book_prefills_notes(self):
        r = self.client.get(reverse("core:book") + "?notes=Mbuzi%20Leg%20Deluxe")
        self.assertContains(r, "Mbuzi Leg Deluxe")

    def test_menu_shows_prices(self):
        r = self.client.get(reverse("core:menu"))
        self.assertContains(r, "Nyama Feast Platter")
        self.assertContains(r, "4300")

    def _booking(self, **overrides):
        data = {
            "branch": Branch.objects.get(slug="golf-park").pk,
            "date": (timezone.localdate() + datetime.timedelta(days=2)).isoformat(),
            "time": "13:00", "guests": 4, "occasion": "dining",
            "name": "Test Guest", "phone": "0712 345 678", "email": "", "notes": "",
        }
        data.update(overrides)
        return data

    def test_booking_saved(self):
        r = self.client.post(reverse("core:book"), self._booking())
        self.assertRedirects(r, reverse("core:book_thanks"))
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertContains(self.client.get(reverse("core:book_thanks")), "Golf Park")

    def test_booking_rejects_past_date(self):
        past = (timezone.localdate() - datetime.timedelta(days=1)).isoformat()
        r = self.client.post(reverse("core:book"), self._booking(date=past))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_booking_honeypot(self):
        self.client.post(reverse("core:book"), self._booking(website="spam"))
        self.assertEqual(Reservation.objects.count(), 0)

    def test_job_application(self):
        r = self.client.post(reverse("core:careers"), {
            "first_name": "Jane", "last_name": "Doe", "email": "jane@example.com",
            "phone": "0712345678", "position": "Chef", "start_date": "", "message": "Hi",
        })
        self.assertEqual(r.status_code, 302)
        app = JobApplication.objects.get()
        self.assertEqual(app.opening.title, "Chef")
