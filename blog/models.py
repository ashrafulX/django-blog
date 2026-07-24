
from django.db import models
import math
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, UniqueConstraint
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field


# 1. Category Model
 
class Category(models.Model):
    """
    Hierarchical category grouping for blog posts.
    Supports one level of nesting (parent → child).
    Optimised for heavy read operations via composite index.
    """
    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=150, unique=True)
    parent_category = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("Parent Category"),
        help_text=_("Select a parent to create a sub-category."),
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Toggle to hide/show this category site-wide."),
    )
    display_order = models.PositiveIntegerField(
        _("Display Order"),
        default=0,
        help_text=_("Lower numbers appear first in menus."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["slug", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            # Bengali slug সরাসরি ব্যবহার করুন
            base_slug = self.name.lower().replace(' ', '-')
            self.slug = base_slug
        super().save(*args, **kwargs)
    # Validation
   
    def clean(self):
        super().clean()
        # Guard against direct self-reference
        if self.parent_category_id and self.parent_category_id == self.pk:
            raise ValidationError(
                {"parent_category": _("A category cannot be its own parent.")}
            )
        # Guard against deeper circular references (A → B → A)
        ancestor = self.parent_category
        while ancestor is not None:
            if ancestor.pk == self.pk:
                raise ValidationError(
                    {"parent_category": _("Circular reference detected in category hierarchy.")}
                )
            ancestor = ancestor.parent_category

    def __str__(self):
        if self.parent_category:
            return f"{self.parent_category.name} → {self.name}"
        return self.name


 
# 2. Tag Model
 
class Tag(models.Model):
    """
    Keyword/topic label attached to blog posts.
    slug carries an implicit db_index via unique=True.
    """
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ["name"]

    def __str__(self):
        return self.name


 
# 3. Blog Model
 
class Blog(models.Model):
    """
    Core article model.

    Key design decisions
    --------------------
    * reading_time  - auto-calculated in save() at 200 WPM; strip_tags()
                      prevents HTML inflating the word count.
    * slug          - auto-generated with a collision loop; truncated to
                      max_length - 10 to prevent StringDataRightTruncation.
    * published_at  - auto-stamped when status transitions to PUBLISHED so
                      ordering by published_at is always reliable.
    * views         - incremented via F() expression in a dedicated class
                      method to eliminate race conditions.
    * author        - uses SET_NULL + author_name fallback so posts survive
                      user deletion without losing the byline.
    """

    class StatusChoices(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

   
    # Core fields
   
    title = models.CharField(_("Title"), max_length=255)
    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        blank=True,
        help_text=_("Leave blank to auto-generate from title."),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="blogs",
        verbose_name=_("Category"),
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="blogs",
        blank=True,
        verbose_name=_("Tags"),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blogs",
        verbose_name=_("Author"),
    )

    # Preserves the byline even if the User account is deleted
    author_name = models.CharField(
        _("Author Name"),
        max_length=150,
        blank=True,
        help_text=_("Auto-filled from the linked user; editable as a fallback."),
    )

   
    # Content

    short_description = models.TextField(
        _("Short Description"),
        blank=True,
        help_text=_("Summary shown on list/homepage cards."),
    )
    content = CKEditor5Field(_("Content"), config_name="extends")

   
    # Media
   
    featured_image = models.ImageField(
        _("Featured Image"),
        upload_to="posts/%Y/%m/",
        blank=True,
        null=True,
    )
    featured_image_alt = models.CharField(
        _("Featured Image Alt Text"),
        max_length=255,
        blank=True,
        help_text=_("Accessibility and image-SEO description."),
    )
    image_caption = models.CharField(
        _("Image Caption"),
        max_length=255,
        blank=True,
        help_text=_("Optional caption displayed below the featured image."),
    )

   
    # Status & flags
   
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        db_index=True,
    )
    is_featured = models.BooleanField(_("Featured"), default=False, db_index=True)
    is_breaking_news = models.BooleanField(_("Breaking News"), default=False, db_index=True)

   
    # Computed / analytics
   
    reading_time = models.PositiveIntegerField(
        _("Reading Time (minutes)"),
        default=1,
        editable=False,
        help_text=_("Auto-calculated at 200 WPM; not editable directly."),
    )
    views = models.PositiveBigIntegerField(
        _("Views"),
        default=0,
        editable=False,
        help_text=_("Incremented atomically via increment_views(); never set directly."),
    )

   
    # SEO
   
    seo_title = models.CharField(_("SEO Title"), max_length=70, blank=True)
    meta_description = models.CharField(_("Meta Description"), max_length=160, blank=True)
    meta_keywords = models.CharField(_("Meta Keywords"), max_length=255, blank=True)
    canonical_url = models.URLField(
        _("Canonical URL"),
        blank=True,
        help_text=_("Set only to override the default canonical URL."),
    )

   
    # Timestamps
   
    published_at = models.DateTimeField(
        _("Published At"),
        blank=True,
        null=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Blog")
        verbose_name_plural = _("Blogs")
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["category", "status"]),
        ]

   
    # Save logic
   
    def save(self, *args, **kwargs):
        # 1. Sync author_name from linked User (only when author is set and
        #    author_name hasn't been manually overridden).
        if self.author and not self.author_name:
            self.author_name = self.author.get_full_name() or self.author.username

        # 2. Auto-stamp published_at on first publication.
        if self.status == self.StatusChoices.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()

        # 3. Auto-calculate reading time (strip HTML tags first).
        if self.content:
            word_count = len(strip_tags(self.content).split())
            self.reading_time = max(1, math.ceil(word_count / 200.0))

        if not self.slug:
            base_slug = self.title.lower().replace(' ', '-') or "post"
            max_length = self._meta.get_field("slug").max_length
            base_slug = base_slug[: max_length - 10]
            slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug


        super().save(*args, **kwargs)


class BlogView(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="view_records")
    ip_address = models.GenericIPAddressField(_("IP Address"))
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Blog View Record")
        verbose_name_plural = _("Blog View Records")
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.blog.title} viewed by {self.ip_address}"

    @property
    def display_author(self) -> str:
        """Returns the best available author label for templates."""
        return self.author_name or _("Anonymous")

    def __str__(self):
        return self.title


 
# 4. Advertisement Model
 
class Advertisement(models.Model):
    """
    Manages site-wide ad placements via predefined position slots.
    A partial unique constraint ensures only one *active* ad occupies
    each position at a time, while inactive records are retained for history.
    """

    class PositionChoices(models.TextChoices):
        HEADER = "header", _("Header")
        HOME_LEFT = "home_left", _("Homepage - Left")
        HOME_RIGHT = "home_right", _("Homepage - Right")
        ARTICLE_TOP = "article_top", _("Inside Article - Top")
        ARTICLE_BOTTOM = "article_bottom", _("Inside Article - Bottom")
        SIDEBAR = "sidebar", _("Sidebar")

    name = models.CharField(_("Ad Name"), max_length=150)
    position = models.CharField(
        _("Position"),
        max_length=50,
        choices=PositionChoices.choices,
        db_index=True,
    )
    adsense_code = models.TextField(
        _("AdSense Script / Code"),
        help_text=_(
            "Paste raw AdSense or custom HTML/JS here. "
            "Only trusted admin users should have access to this field."
        ),
    )
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Advertisement")
        verbose_name_plural = _("Advertisements")
        constraints = [
            UniqueConstraint(
                fields=["position"],
                condition=Q(is_active=True),
                name="unique_active_ad_per_position",
            )
        ]

    def __str__(self):
        return f"{self.name} — {self.get_position_display()}"