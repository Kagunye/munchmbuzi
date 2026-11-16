from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("our-story/", views.about, name="about"),
    path("experience/", views.experience, name="experience"),
    path("menu/", views.menu, name="menu"),
    path("branches/", views.branches, name="branches"),
    path("book/", views.book, name="book"),
    path("book/thank-you/", views.book_thanks, name="book_thanks"),
    path("events/", views.events, name="events"),
    path("careers/", views.careers, name="careers"),
    path("news/", views.news, name="news"),
    path("news/<slug:slug>/", views.post_detail, name="post_detail"),
]
