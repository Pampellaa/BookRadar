from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Review, Book
from django.db.models import Avg

@receiver(post_save, sender=Review)
def update_book_average_rating(sender, instance, **kwargs):
    book = instance.book
    book.update_average_rating()