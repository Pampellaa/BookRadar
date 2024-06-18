from django.apps import AppConfig


class BookradarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BookRadar'

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BookRadar'

    def ready(self):
        import BookRadar.signals
