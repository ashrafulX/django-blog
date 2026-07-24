from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Category, Tag, Blog, Advertisement, BlogView

# 1. Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')
    list_editable = ('display_order', 'is_active')

# 2. Tag Admin
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

# 3. Blog Admin
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'category', 
        'status_badge', 
        'view_analytics_link', 
        'is_featured', 
        'is_breaking_news', 
        'published_at'
    )
    list_display_links = ('title',)
    list_filter = ('status', 'category', 'is_featured', 'is_breaking_news', 'published_at')
    search_fields = ('title', 'slug', 'category__name', 'tags__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'reading_time', 'created_at', 'updated_at', 'image_preview')
    filter_horizontal = ('tags',)
    date_hierarchy = 'published_at'

    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'category', 'tags', 'author', 'short_description', 'content')
        }),
        ('Media Assets', {
            'fields': ('featured_image', 'image_preview', 'featured_image_alt', 'image_caption')
        }),
        ('Publishing Options', {
            'fields': ('status', 'published_at', 'is_featured', 'is_breaking_news')
        }),
        ('SEO Metadata', {
            'fields': ('seo_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Performance & Logs', {
            'fields': ('views', 'reading_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        if obj.status == 'published':
            return format_html(
                '<span style="background-color: #dcfce7; color: #16a34a; font-weight: 600; padding: 4px 12px; border-radius: 9999px; font-size: 12px;">{}</span>',
                'Published'
            )
        return format_html(
            '<span style="background-color: #f3f4f6; color: #4b5563; font-weight: 600; padding: 4px 12px; border-radius: 9999px; font-size: 12px;">{}</span>',
            'Draft'
        )
    status_badge.short_description = 'Status'

    def image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-height: 150px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.featured_image.url
            )
        return "No image uploaded"
    image_preview.short_description = 'Preview'

    def view_analytics_link(self, obj):
        count = obj.view_records.count()
        url = reverse('admin:blog_blogview_changelist') + f'?blog__id__exact={obj.id}'
        return format_html(
            '<a href="{}" style="color: #16a34a; font-weight: bold; text-decoration: underline;">{} Views</a>', 
            url, count
        )
    view_analytics_link.short_description = 'Total Views'

# 4. Advertisement Admin
@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'is_active', 'created_at')
    list_filter = ('position', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)

# 5. BlogView Admin
@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = ('blog', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at', 'blog')
    search_fields = ('ip_address', 'blog__title')
    readonly_fields = ('blog', 'ip_address', 'viewed_at')