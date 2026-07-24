from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("",                              views.HomeView.as_view(),           name="home"),
    path("search/",                       views.SearchView.as_view(),         name="search"),
    path("featured/",                     views.FeaturedPostListView.as_view(), name="featured"),
    path("breaking-news/",                views.BreakingNewsListView.as_view(), name="breaking_news"),
    path("category/<slug:slug>/",         views.CategoryPostListView.as_view(), name="category"),
    path("tag/<slug:slug>/",              views.TagPostListView.as_view(),     name="tag"),
    path("<path:slug>/", views.BlogDetailView.as_view(), name="detail"),
]