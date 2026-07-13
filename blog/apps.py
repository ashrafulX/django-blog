from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'
    verbose_name = 'Blog Management'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures signal handlers are registered when Django starts.
        """
        import blog.signals  # noqa
