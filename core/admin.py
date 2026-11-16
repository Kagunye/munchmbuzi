from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Branch, Dish, JobApplication, JobOpening, MenuCategory, MenuItem, MusicTrack, Post, Reservation,
    Review,
)

admin.site.site_header = "Mbuzi Munch admin"
admin.site.site_title = "Mbuzi Munch"
admin.site.index_title = "Manage the website"


def thumb(obj, field="image", size=56):
    f = getattr(obj, field, None)
    if f:
        return format_html('<img src="{}" style="height:{}px;width:{}px;object-fit:cover;border-radius:6px">', f.url, size, size)
    return "—"


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "area", "city", "phone", "is_new", "is_active", "order")
    list_editable = ("is_new", "is_active", "order")
    list_display_links = ("preview", "name")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="")
    def preview(self, obj):
        return thumb(obj)


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "kind", "price", "featured", "order")
    list_editable = ("featured", "order")
    list_display_links = ("preview", "name")
    list_filter = ("kind", "featured")

    @admin.display(description="")
    def preview(self, obj):
        return thumb(obj)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ("name", "description", "price", "serves", "is_vegetarian", "is_spicy", "is_available", "order")


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "item_count", "order")
    list_editable = ("order",)
    list_filter = ("section",)
    inlines = [MenuItemInline]

    @admin.display(description="Items")
    def item_count(self, obj):
        return obj.items.count()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_available", "is_vegetarian", "is_spicy")
    list_editable = ("price", "is_available")
    list_filter = ("category__section", "category", "is_available", "is_vegetarian")
    search_fields = ("name", "description")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author", "branch", "rating", "is_published", "order")
    list_editable = ("is_published", "order")
    list_filter = ("branch", "is_published")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_published")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ("title", "branch", "is_open", "order")
    list_editable = ("is_open", "order")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("name", "branch", "date", "time", "guests", "occasion", "phone", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "branch", "occasion", "date")
    search_fields = ("name", "phone", "email")
    date_hierarchy = "date"


@admin.register(MusicTrack)
class MusicTrackAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "is_active", "uploaded_at", "player")
    list_editable = ("is_active",)

    @admin.display(description="Preview")
    def player(self, obj):
        if obj.audio:
            return format_html('<audio controls preload="none" src="{}" style="height:32px"></audio>', obj.audio.url)
        return "—"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "position", "phone", "email", "start_date", "created_at")
    search_fields = ("first_name", "last_name", "email", "position")
    list_filter = ("position", "opening")
