"""
Signals for blog app - handles view tracking and other automated tasks.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Blog, BlogView


@receiver(post_save, sender=Blog)
def initialize_published_timestamp(sender, instance, created, **kwargs):
    """
    Automatically set published_at timestamp when status changes to PUBLISHED.
    (Note: This is already handled in the Blog.save() method, but kept for clarity)
    """
    pass  # Logic is in Blog.save()


def increment_blog_views(blog_id, ip_address):
    """
    Atomically increment blog views and track unique visitors.
    Prevents duplicate counting from rapid refreshes by tracking IP + time window.
    
    Args:
        blog_id: The Blog instance ID
        ip_address: The visitor's IP address
    
    Returns:
        tuple: (created, view_record) - created indicates if this was a new view record
    """
    # Check if this IP viewed this blog in the last 60 seconds
    sixty_seconds_ago = timezone.now() - timedelta(seconds=60)
    
    recent_view = BlogView.objects.filter(
        blog_id=blog_id,
        ip_address=ip_address,
        viewed_at__gte=sixty_seconds_ago
    ).exists()
    
    if not recent_view:
        # Create new view record and increment counter
        from django.db.models import F
        
        view_record = BlogView.objects.create(
            blog_id=blog_id,
            ip_address=ip_address
        )
        
        # Atomic view count increment
        Blog.objects.filter(pk=blog_id).update(views=F('views') + 1)
        
        return True, view_record
    
    return False, None
