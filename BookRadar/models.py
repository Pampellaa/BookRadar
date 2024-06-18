from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

BOOK_TYPES = [
    (1, 'Romance'),
    (2, 'Thriller'),
    (3, 'Science Fiction'),
    (4, 'Fantasy'),
    (5, 'Mystery'),
    (6, 'Horror'),
    (7, 'Comedy'),
    (8, 'Historical Fiction'),
    (9, 'Non-Fiction')
]

# models.py
from django.db import models
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User  # Assuming User model import

class Book(models.Model):
    title = models.CharField(max_length=64)
    author = models.CharField(max_length=64)
    publisher = models.CharField(max_length=64, null=True)
    year = models.IntegerField(null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    type = models.IntegerField(choices=BOOK_TYPES, null=True)

    def __str__(self):
        return self.title


    def update_average_rating(self):
        average_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        self.average_rating = average_rating
        self.save()

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.book.update_average_rating()
