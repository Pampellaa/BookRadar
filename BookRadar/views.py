import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Avg, FloatField
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from BookRadar.forms import LoginForm, RegisterForm
from BookRadar.models import Book, Review, BOOK_TYPES
from BookRadar.forms import OpinionAddForm

import requests
from django.http import JsonResponse


class IndexView(View):
    def get(self, request):
        carousel_books = list(Book.objects.all())
        random.shuffle(carousel_books)
        carousel_books = carousel_books[:3]

        books  = Book.objects.all()
        best_books = books.order_by('-average_rating')[:11]

        reviews = Review.objects.all().order_by('-created')[:3]

        ctx = {'carousel_books':carousel_books, 'best_books':best_books, 'reviews':reviews, 'books':books, 'types':BOOK_TYPES}
        return render(request, 'index.html', ctx)

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
        form.add_error('username', 'Invalid login details. Try again.')
        return render(request, 'login.html', {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('index')

class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = User.objects.create(username=username)
            user.set_password(password)
            user.save()
            login(request, user)
            return redirect('login')
        return render(request, 'register.html', {'form': form})

class AddOpinionView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_authenticated:
            search_author = request.GET.get('author')
            url = f'https://www.googleapis.com/books/v1/volumes?q={search_author}&maxResults=40'

            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()

                books = []
                if 'items' in data:
                    for item in data['items']:
                        title = item['volumeInfo']['title'][:100]
                        authors = item['volumeInfo'].get('authors', [])
                        books.append({'title': title, 'authors': ", ".join(authors) if authors else ""})
                else:
                    return JsonResponse({'error': 'Failed to fetch data from Google Books API'}, status=500)

                return render(request, 'add_review.html', {'books': books})
            else:
                return JsonResponse({'error': 'Failed to connect to Google Books API'}, status=500)
        else:
            return redirect('login')




class BookTypeView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            book_type = kwargs['book_type']
            books = Book.objects.filter(type=book_type).order_by('-ranking')
            type_name = dict(BOOK_TYPES).get(book_type)
            return render(request, 'book_type.html', {'books': books, 'type_name': type_name})
        else:
            return redirect('login')


    # def post(self, request):
    #     user = request
    #     form = OpinionAddForm(request.POST)
    #     if form.is_valid():


def fetch_books(request):
    search_query = request.GET.get('search_query', '').strip()
    if not search_query:
        return render(request, 'books.html', {'books': [], 'search_query': ''})

    url = f'https://www.googleapis.com/books/v1/volumes?q={search_query}&maxResults=40'
    response = requests.get(url)
    data = response.json()

    google_books = []
    if 'items' in data:
        for item in data['items']:
            title = item['volumeInfo'].get('title', 'Unknown')[:100]
            authors = ", ".join(item['volumeInfo'].get('authors', ['Unknown']))
            publisher = item['volumeInfo'].get('publisher', 'Unknown')
            published_date = item['volumeInfo'].get('publishedDate', 'Unknown')
            year = published_date[:4] if published_date and len(published_date) >= 4 else 'Unknown'
            rating = item['volumeInfo'].get('averageRating', 0)

            if not Book.objects.filter(title=title, author=authors).exists():
                google_books.append({
                    'title': title,
                    'authors': authors,
                    'publisher': publisher,
                    'year': year,
                    'average_rating': rating,
                })

    db_books = Book.objects.filter(title__icontains=search_query)

    db_titles = set(db_books.values_list('title', flat=True))
    google_books = [book for book in google_books if book['title'] not in db_titles]

    books = db_books.values('title', 'author', 'publisher', 'year', 'average_rating')
    books = list(books) + google_books
    books.sort(key=lambda x: x.get('authors', ''))

    return render(request, 'books.html', {'books': books, 'search_query': search_query})

class Add_review(LoginRequiredMixin, View):
    def post(self, request):
        title = request.POST.get('title')
        authors = request.POST.get('authors')
        publisher = request.POST.get('publisher')
        year = request.POST.get('year')
        rating = request.POST.get('rating')
        average_rating = request.POST.get('average_rating')
        comment = request.POST.get('comment')
        search_query = request.GET.get('search_query')

        try:
            year = int(year)
        except ValueError:
            year = None

        book, created = Book.objects.get_or_create(
            title=title,
            author=authors,
            defaults={'publisher': publisher, 'year': year}
        )

        user = request.user

        if book and rating and comment:
            review = Review(book=book, user=user, rating=rating, comment=comment)
            review.save()
            book.update_average_rating()

            return redirect(reverse('books') + f'?search_query={search_query}')
        else:
            return HttpResponseBadRequest("Invalid data")
