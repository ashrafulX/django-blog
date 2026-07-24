from django.db.models import Q, F
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import DetailView, ListView
from .models import Advertisement, Blog, Category, Tag
from .signals import increment_blog_views


# Helpers

def _get_active_ads(*positions):
    """
    Fetch active advertisements for given positions.
    Only one active ad per position (enforced by model constraint).
    """
    qs = Advertisement.objects.filter(
        position__in=positions,
        is_active=True,
    ).only("position", "adsense_code", "name")
    return {ad.position: ad for ad in qs}


def _published():
    """Get queryset of published blog posts."""
    return Blog.objects.filter(status=Blog.StatusChoices.PUBLISHED)


def _list_qs():
    """
    Shared optimised queryset for all list views.
    Includes all necessary related data with minimal queries.
    """
    return (
        _published()
        .select_related("category", "author")
        .prefetch_related("tags")
        .only(
            "title", "slug", "short_description", "featured_image",
            "featured_image_alt", "published_at", "reading_time", "views",
            "is_featured", "is_breaking_news", "author_name",
            "category__name", "category__slug",
            "author__first_name", "author__last_name", "author__username",
        )
        .order_by("-published_at")
    )


# 1. Home View

@method_decorator(cache_page(60 * 5), name="dispatch")
@method_decorator(vary_on_cookie, name="dispatch")
class HomeView(ListView):
    model = Blog
    template_name = "blog/home.html"
    context_object_name = "latest_posts"
    paginate_by = 9

    def get_queryset(self):
        return _list_qs()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = _list_qs()
        context["breaking_news"]  = base_qs.filter(is_breaking_news=True)[:5]
        context["featured_posts"] = base_qs.filter(is_featured=True)[:6]
        context["categories"]     = Category.objects.filter(
            is_active=True, parent_category__isnull=True
        ).order_by("display_order")[:8]

        ads = _get_active_ads(
            Advertisement.PositionChoices.HEADER,
            Advertisement.PositionChoices.HOME_LEFT,
            Advertisement.PositionChoices.HOME_RIGHT,
        )
        context["ad_header"]     = ads.get(Advertisement.PositionChoices.HEADER)
        context["ad_home_left"]  = ads.get(Advertisement.PositionChoices.HOME_LEFT)
        context["ad_home_right"] = ads.get(Advertisement.PositionChoices.HOME_RIGHT)
        return context


# 2. Blog Detail View

class BlogDetailView(DetailView):
    model = Blog
    template_name = "blog/detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return _published().select_related("category", "author").prefetch_related("tags")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Track view atomically with IP-based duplicate prevention
        client_ip = self.get_client_ip()
        increment_blog_views(obj.pk, client_ip)
        
        return obj

    def get_client_ip(self):
        """
        Extract client IP from request.
        Handles X-Forwarded-For for proxies and load balancers.
        """
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        context["related_posts"] = (
            _published()
            .filter(category=post.category)
            .exclude(pk=post.pk)
            .only(
                "title", "slug", "featured_image", "featured_image_alt", 
                "published_at", "reading_time", "views"
            )
            .order_by("-published_at")[:4]
        )

        ads = _get_active_ads(
            Advertisement.PositionChoices.ARTICLE_TOP,
            Advertisement.PositionChoices.ARTICLE_BOTTOM,
            Advertisement.PositionChoices.SIDEBAR,
        )
        context["ad_article_top"]    = ads.get(Advertisement.PositionChoices.ARTICLE_TOP)
        context["ad_article_bottom"] = ads.get(Advertisement.PositionChoices.ARTICLE_BOTTOM)
        context["ad_sidebar"]        = ads.get(Advertisement.PositionChoices.SIDEBAR)
        return context


# 3. Category Post List View

class CategoryPostListView(ListView):
    model = Blog
    template_name = "blog/category.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_category(self):
        if not hasattr(self, "_category"):
            self._category = get_object_or_404(Category, slug=self.kwargs["slug"], is_active=True)
        return self._category

    def get_queryset(self):
        category = self.get_category()
        child_ids = list(category.children.filter(is_active=True).values_list("pk", flat=True))
        return _list_qs().filter(category__in=[category.pk] + child_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"]         = self.get_category()
        context["child_categories"] = self.get_category().children.filter(is_active=True)
        ads = _get_active_ads(Advertisement.PositionChoices.SIDEBAR)
        context["ad_sidebar"] = ads.get(Advertisement.PositionChoices.SIDEBAR)
        return context


# 4. Tag Post List View

class TagPostListView(ListView):
    model = Blog
    template_name = "blog/tag.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_tag(self):
        if not hasattr(self, "_tag"):
            self._tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return self._tag

    def get_queryset(self):
        return _list_qs().filter(tags=self.get_tag())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.get_tag()
        ads = _get_active_ads(Advertisement.PositionChoices.SIDEBAR)
        context["ad_sidebar"] = ads.get(Advertisement.PositionChoices.SIDEBAR)
        return context


# 5. Search View

class SearchView(ListView):
    model = Blog
    template_name = "blog/search.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_query(self):
        return " ".join(self.request.GET.get("q", "").split())

    def get(self, request, *args, **kwargs):
        if not self.get_query():
            return redirect("blog:home")
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        q = self.get_query()
        return _list_qs().filter(
            Q(title__icontains=q)
            | Q(short_description__icontains=q)
            | Q(content__icontains=q)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"]        = self.get_query()
        context["result_count"] = self.get_queryset().count()
        return context


# 6. Featured Posts View

class FeaturedPostListView(ListView):
    model = Blog
    template_name = "blog/featured.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return _list_qs().filter(is_featured=True)


# 7. Breaking News View

class BreakingNewsListView(ListView):
    model = Blog
    template_name = "blog/breaking_news.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return _list_qs().filter(is_breaking_news=True)
