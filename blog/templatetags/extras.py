from django import template
from blog.models import Category  # ক্যাটাগরি মডেলটি ইমপোর্ট করা হলো

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replaces or adds query parameters in the current URL.
    Usage: {% url_replace page=page_obj.next_page_number %}
    """
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()


@register.filter
def reading_label(minutes):
    """Returns '1 min read', '5 min read', etc."""
    return f"{minutes} min read"


@register.simple_tag
def get_menu_categories():
    
    return Category.objects.filter(
        is_active=True, 
        parent_category__isnull=True
    ).order_by('display_order')