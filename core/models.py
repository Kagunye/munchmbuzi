from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Ordered(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class Branch(Ordered):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, blank=True)
    area = models.CharField(max_length=120, help_text="e.g. Ngong Racecourse, Langata Road")
    city = models.CharField(max_length=60)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    image = models.ImageField(upload_to="branches/", blank=True)
    video = models.FileField(upload_to="branches/video/", blank=True,
                             help_text="Optional vertical reel (MP4) shown beside the branch photo.")
    video_poster = models.ImageField(upload_to="branches/video/", blank=True,
                                     help_text="Still image shown before the video plays.")
    tagline = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    hours_weekday = models.CharField("Sun–Thu hours", max_length=40, default="10:00 – 22:00")
    hours_weekend = models.CharField("Fri–Sat hours", max_length=40, default="10:00 – 23:00")
    map_query = models.CharField(
        max_length=200, blank=True, help_text="Text searched on Google Maps for the embedded map."
    )
    is_new = models.BooleanField("Show 'New' badge", default=False)
    is_active = models.BooleanField(default=True)

    class Meta(Ordered.Meta):
        verbose_name_plural = "branches"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:branches") + f"#{self.slug}"

    @property
    def phone_link(self):
        digits = "".join(ch for ch in self.phone if ch.isdigit())
        if digits.startswith("0"):
            digits = "254" + digits[1:]
        return f"+{digits}"

    @property
    def whatsapp_link(self):
        return f"https://wa.me/{self.phone_link.lstrip('+')}"


class Dish(Ordered):
    FOOD, DRINK = "food", "drink"
    KIND_CHOICES = [(FOOD, "Food"), (DRINK, "Drink")]

    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    price = models.CharField(max_length=40, blank=True, help_text="Shown as KES, e.g. 2600")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=FOOD)
    image = models.ImageField(upload_to="dishes/")
    featured = models.BooleanField(default=True, help_text="Show on the home page.")

    class Meta(Ordered.Meta):
        verbose_name_plural = "signature dishes"

    def __str__(self):
        return self.name


class MenuCategory(Ordered):
    MAINS, BREAKFAST, DRINKS, BAR = "mains", "breakfast", "drinks", "bar"
    SECTION_CHOICES = [
        (MAINS, "Food"),
        (BREAKFAST, "Breakfast"),
        (DRINKS, "Soft drinks & coffee"),
        (BAR, "Bar, wine & cocktails"),
    ]

    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default=MAINS)
    name = models.CharField(max_length=80)
    slug = models.SlugField(blank=True)
    note = models.TextField(blank=True)
    price_label = models.CharField(
        max_length=40, blank=True, help_text="e.g. Shot/Bottle, Glass/Bottle, Cup/Pot"
    )

    class Meta(Ordered.Meta):
        verbose_name_plural = "menu categories"

    def __str__(self):
        return f"{self.get_section_display()} · {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.section}-{self.name}")
        super().save(*args, **kwargs)


class MenuItem(Ordered):
    category = models.ForeignKey(MenuCategory, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    price = models.CharField(max_length=60, help_text="e.g. 950, 2350/1250/750, 300/5000")
    serves = models.CharField(max_length=40, blank=True, help_text="e.g. Serves 2-3")
    is_vegetarian = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Review(Ordered):
    author = models.CharField(max_length=60)
    text = models.TextField()
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL)
    rating = models.PositiveSmallIntegerField(default=5)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.author}: {self.text[:40]}"

    @property
    def stars(self):
        return range(self.rating)


class Post(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True, blank=True, max_length=180)
    excerpt = models.TextField(max_length=400)
    body = models.TextField(help_text="Separate paragraphs with a blank line. Lines starting with '## ' become headings, '- ' become bullet points.")
    image = models.ImageField(upload_to="news/", blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:180]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:post_detail", args=[self.slug])


class JobOpening(Ordered):
    title = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL,
                               help_text="Leave empty for any branch.")
    summary = models.TextField()
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Reservation(models.Model):
    OCCASIONS = [
        ("dining", "Table booking"),
        ("birthday", "Birthday / celebration"),
        ("corporate", "Corporate / team lunch"),
        ("private", "Private party / event space"),
    ]
    STATUSES = [("new", "New"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="reservations")
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField(default=2)
    occasion = models.CharField(max_length=20, choices=OCCASIONS, default="dining")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.branch} · {self.date} {self.time:%H:%M}"


class MusicTrack(models.Model):
    """Background music for the floating Mbuzi play button.

    The newest active track is played. With no active track the site falls back
    to an original groove synthesised in the browser (no licensing needed).
    Only upload music you have the rights to play publicly.
    """

    title = models.CharField(max_length=100, default="Mbuzi Munch vibes")
    artist = models.CharField(max_length=100, blank=True)
    audio = models.FileField(upload_to="music/", help_text="MP3 or M4A, ideally under 8 MB.")
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} – {self.artist}" if self.artist else self.title


class JobApplication(models.Model):
    opening = models.ForeignKey(JobOpening, null=True, blank=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    position = models.CharField("Position applying for", max_length=100)
    start_date = models.DateField("Available start date", null=True, blank=True)
    cv = models.FileField("CV (PDF or Word)", upload_to="applications/", blank=True)
    message = models.TextField("Tell us about yourself", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} · {self.position}"
