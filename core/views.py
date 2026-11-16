import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import JobApplicationForm, ReservationForm
from .models import Branch, Dish, JobOpening, MenuCategory, MenuItem, Post, Review

logger = logging.getLogger(__name__)

# Recent Instagram posts (downloaded from @mbuzi_munch) shown in the social strip.
INSTAGRAM_IMAGES = [
    ("img/social/ig-01.jpg", "Grilled steak with masala chips and kachumbari"),
    ("img/social/ig-13.jpg", "Grilled kuku wings, served on the lawn"),
    ("img/social/ig-03.jpg", "Grilled kuku and fries on the terrace"),
    ("img/social/ig-04.jpg", "Platters are perfect for sharing"),
    ("img/social/ig-02.jpg", "Sticky toffee pudding with ice cream"),
    ("img/social/ig-08.jpg", "Inside Mbuzi Munch"),
    ("img/social/ig-12.jpg", "Grilled chicken wings with fresh lemonade"),
    ("img/social/ig-05.jpg", "The Mbuzi Munch burger"),
    ("img/social/ig-10.jpg", "Event catering spread"),
    ("img/social/ig-07.jpg", "Fresh lemonades"),
    ("img/social/ig-11.jpg", "Garden lunch by MM Catering"),
    ("img/social/ig-06.jpg", "Lemonades by the bar"),
]

# Private-party venue photos (Instagram post DXgeV1MjEMv) for the sliding banner.
PARTY_PHOTOS = [f"img/party/party-{n:02d}.jpg" for n in (1, 2, 4, 7, 3, 9, 5, 10, 6, 8, 11, 12)]

# Instagram photos shown on the menu page ("As seen on Instagram").
MENU_INSTAGRAM = [
    ("img/social/ig-13.jpg", "Kuku wings platter"),
    ("img/social/ig-01.jpg", "Steak, masala chips & kachumbari"),
    ("img/social/ig-02.jpg", "Sticky toffee pudding"),
    ("img/social/ig-12.jpg", "Grilled wings & lemonade"),
    ("img/social/ig-04.jpg", "Platters for sharing"),
    ("img/social/ig-05.jpg", "The burger"),
]

# Everyday life at the branches (branches page).
BRANCH_LIFE = [
    ("img/social/ig-08.jpg", "Inside Mbuzi Munch"),
    ("img/reels/reel-01.jpg", "Cheesy fries above the racecourse"),
    ("img/social/ig-03.jpg", "Lunch on the terrace"),
    ("img/reels/reel-06.jpg", "The kitchen team at work"),
    ("img/social/ig-07.jpg", "Lemonades by the bar"),
    ("img/reels/reel-09.jpg", "Fresh off the grill"),
]

# Reels downloaded from @mbuzi_munch and re-encoded for the web (static/video/reels).
REELS = {
    "matchday": {"video": "video/reels/reel-xp.mp4", "poster": "img/reels/reel-xp.jpg",
                 "caption": "Big match screenings at Mbuzi Munch"},
    "derby": {"video": "video/reels/reel-derby.mp4", "poster": "img/reels/reel-derby.jpg",
              "caption": "Derby day on the grill at Ngong Racecourse"},
    "cheesy": {"video": "video/reels/reel-01.mp4", "poster": "img/reels/reel-01.jpg",
               "caption": "Cheesy fries and chicken, with a racecourse view"},
    "pudding": {"video": "video/reels/reel-03.mp4", "poster": "img/reels/reel-03.jpg",
                "caption": "This is your sign to visit us. Sticky toffee pudding at Golf Park"},
    "vibes": {"video": "video/reels/reel-04.mp4", "poster": "img/reels/reel-04.jpg",
              "caption": "Great food, delicious food and great vibes"},
    "burger": {"video": "video/reels/reel-05.mp4", "poster": "img/reels/reel-05.jpg",
               "caption": "Big flavour. Bold cravings. Pure Mbuzi Munch!"},
    "kitchen": {"video": "video/reels/reel-06.mp4", "poster": "img/reels/reel-06.jpg",
                "caption": "Our team in action: things AI can't do"},
    "dining": {"video": "video/reels/reel-08.mp4", "poster": "img/reels/reel-08.jpg",
               "caption": "Wraps, coffee and good company"},
    "catering": {"video": "video/reels/reel-09.mp4", "poster": "img/reels/reel-09.jpg",
                 "caption": "MM Catering: events, brunch and parties"},
    "event": {"video": "video/reels/reel-11.mp4", "poster": "img/reels/reel-11.jpg",
              "caption": "Catering a garden lunch event"},
}


def reels(*keys):
    return [REELS[k] for k in keys]


def _notify(subject, body, recipients):
    recipients = [r for r in recipients if r]
    if not recipients:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception:  # never lose a booking because email is misconfigured
        logger.exception("Could not send notification email: %s", subject)


def home(request):
    context = {
        "dishes": Dish.objects.filter(featured=True, kind=Dish.FOOD)[:10],
        "drinks": Dish.objects.filter(featured=True, kind=Dish.DRINK)[:5],
        "branches": Branch.objects.filter(is_active=True),
        "reviews": Review.objects.filter(is_published=True).select_related("branch")[:8],
        "posts": Post.objects.filter(is_published=True)[:2],
        "instagram": INSTAGRAM_IMAGES,
        "reels": reels("cheesy", "pudding", "vibes", "burger"),
        "party_photos": PARTY_PHOTOS,
        "form": ReservationForm(),
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html", {
        "dishes": Dish.objects.filter(kind=Dish.FOOD)[:3],
    })


def menu(request):
    categories = MenuCategory.objects.prefetch_related("items")
    sections = []
    for key, label in MenuCategory.SECTION_CHOICES:
        cats = [c for c in categories if c.section == key]
        if cats:
            sections.append({"key": key, "label": label, "categories": cats})
    return render(request, "core/menu.html", {
        "sections": sections,
        "insta_dishes": MENU_INSTAGRAM,
    })


def branches(request):
    return render(request, "core/branches.html", {
        "branches": Branch.objects.filter(is_active=True),
        "reviews": Review.objects.filter(is_published=True).select_related("branch"),
        "life": BRANCH_LIFE,
        "reels": reels("dining", "kitchen"),
    })


def book(request):
    initial = {}
    if branch_slug := request.GET.get("branch"):
        initial["branch"] = Branch.objects.filter(slug=branch_slug).first()
    if occasion := request.GET.get("occasion"):
        initial["occasion"] = occasion
    if notes := request.GET.get("notes"):  # e.g. a plate built on the experience page
        initial["notes"] = notes[:500]

    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("website"):  # bot
                return redirect("core:book_thanks")
            r = form.save()
            _notify(
                f"New booking: {r.name} – {r.date:%a %d %b} {r.time:%H:%M} ({r.guests} guests)",
                (
                    f"Branch: {r.branch}\nName: {r.name}\nPhone: {r.phone}\nEmail: {r.email or '-'}\n"
                    f"Date: {r.date:%A %d %B %Y} at {r.time:%H:%M}\nGuests: {r.guests}\n"
                    f"Occasion: {r.get_occasion_display()}\nNotes: {r.notes or '-'}\n"
                ),
                [r.branch.email],
            )
            request.session["last_booking_id"] = r.pk
            return redirect("core:book_thanks")
    else:
        form = ReservationForm(initial=initial)
    return render(request, "core/book.html", {"form": form})


def book_thanks(request):
    from .models import Reservation

    booking = None
    if pk := request.session.get("last_booking_id"):
        booking = Reservation.objects.filter(pk=pk).select_related("branch").first()
    return render(request, "core/book_thanks.html", {"booking": booking})


def events(request):
    return render(request, "core/events.html", {
        "branches": Branch.objects.filter(is_active=True),
        "gallery": ["img/social/ig-10.jpg", "img/social/ig-11.jpg", "img/social/ig-12.jpg"],
        "reels": reels("catering", "event"),
        "derby_reels": reels("derby"),
        "party_photos": PARTY_PHOTOS,
    })


def careers(request):
    openings = JobOpening.objects.filter(is_open=True).select_related("branch")
    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data.get("website"):
                return redirect(reverse("core:careers") + "?sent=1")
            app = form.save(commit=False)
            app.opening = openings.filter(title__iexact=app.position).first()
            app.save()
            _notify(
                f"Job application: {app.first_name} {app.last_name} – {app.position}",
                (
                    f"Name: {app.first_name} {app.last_name}\nEmail: {app.email}\nPhone: {app.phone}\n"
                    f"Position: {app.position}\nStart date: {app.start_date or '-'}\n"
                    f"CV attached in admin: {'yes' if app.cv else 'no'}\n\n{app.message}"
                ),
                [settings.CAREERS_EMAIL],
            )
            messages.success(request, "Thanks for applying! Our team will be in touch if your profile is a match.")
            return redirect(reverse("core:careers") + "#apply")
    else:
        form = JobApplicationForm(initial={"position": request.GET.get("position", "")})
    return render(request, "core/careers.html", {
        "openings": openings, "form": form, "reels": reels("kitchen", "vibes"),
    })


def news(request):
    return render(request, "core/news.html", {"posts": Post.objects.filter(is_published=True)})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    others = Post.objects.filter(is_published=True).exclude(pk=post.pk)[:2]
    return render(request, "core/post_detail.html", {"post": post, "others": others})


# "Build your plate" options on the experience page: (menu category, menu item, label, photo).
# Prices are read live from the menu, so editing a price in admin updates the experience too.
BUILDER = {
    "nyama": [
        ("Specialities", "Mbuzi Leg Deluxe", "Mbuzi Leg Deluxe", "img/mbuzi-leg.jpg"),
        ("Specialities", "T-Bone (400 grammes)", "T-Bone Steak", "img/tbone-fries.jpg"),
        ("Kuku Kitamu from our Pans & Grills", "Kuku Choma", "Kuku Choma (half)", "img/chicken-platter.jpg"),
        ("Fish", "Fried Whole Tilapia", "Whole Tilapia", "img/tilapia-platter.jpg"),
        ("Wraps & Quesadillas", "Choma Wrap", "Choma Wrap", "img/wraps-fries.jpg"),
        ("Burgers", "Boran Big Beefy", "Boran Big Beefy", "img/burger.jpg"),
    ],
    "side": [
        ("Sides & Snacks", "Ugali", "Ugali", ""),
        ("Sides & Snacks", "Our Legendary Chips", "Legendary Chips", ""),
        ("Sides & Snacks", "Masala Chips", "Masala Chips", "img/masala-chips.jpg"),
        ("Sides & Snacks", "Ugali Chips", "Ugali Chips", ""),
        ("Sides & Snacks", "Kachumbari", "Kachumbari", ""),
        ("Sides & Snacks", "Greens", "Greens", ""),
    ],
    "drink": [
        ("Iced Drinks", "Iced Tea", "Iced Tea", "img/drink-iced-tea.jpg"),
        ("Mocktails", "Virgin Mojito", "Virgin Mojito", "img/drink-mojito.jpg"),
        ("Soft Drinks", "Strawberry Lemonade", "Strawberry Lemonade", "img/drink-juice.jpg"),
        ("Milkshakes", "Mocha", "Mocha Milkshake", "img/drink-milkshake.jpg"),
        ("Cocktails", "Kenyan Dawa", "Kenyan Dawa", "img/drink-cocktail.jpg"),
        ("Beers", "Tusker Draft 500ml", "Tusker Draft", ""),
    ],
}


def _first_price(text):
    digits = ""
    for ch in text:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits) if digits else None


def experience(request):
    from django.templatetags.static import static

    items = {(i.category.name, i.name): i for i in MenuItem.objects.select_related("category")}
    builder = {}
    for group, options in BUILDER.items():
        builder[group] = []
        for cat, name, label, img in options:
            item = items.get((cat, name))
            if item and item.is_available and (price := _first_price(item.price)):
                builder[group].append({
                    "id": item.pk, "label": label, "price": price,
                    "img": static(img) if img else "", "serves": item.serves,
                })
    return render(request, "core/experience.html", {
        "builder": builder,
        "branches": Branch.objects.filter(is_active=True),
        "reels": reels("matchday", "cheesy"),
    })


def page_not_found(request, exception):
    return render(request, "404.html", status=404)
