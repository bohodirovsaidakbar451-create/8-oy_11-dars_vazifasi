from rest_framework.test import APITestCase
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth.models import User, Permission

from .models import Genre, Book
from .serializers import BookDetailSerializer


class BookTestCase(APITestCase):
    def setUp(self):
        cache.clear()

        self.user1 = User.objects.create_user(username="Toxir", password="toxir12345")
        self.admin = User.objects.create_user(username="Admin", password="admin12345", is_staff=True, is_superuser=True)
        self.moder = User.objects.create_user(username="Moder", password="moder12345")
        self.moder.user_permissions.add(Permission.objects.get(codename="add_book"))

        self.genre1 = Genre.objects.create(name="Roman")
        self.genre2 = Genre.objects.create(name="Detektiv")

        self.book1 = Book.objects.create(title="O'tkan kunlar", author="Abdulla Qodiriy", price=50000, published_year=1926, genre=self.genre1)
        self.book2 = Book.objects.create(title="Mehrobdan chayon", author="Abdulla Qodiriy", price=45000, published_year=1929, genre=self.genre1)
        self.book3 = Book.objects.create(title="Sherlok Holms", author="Artur Konan Doyl", price=60000, published_year=1892, genre=self.genre2)

        self.data = {
            'title': "Sariq devni minib",
            'author': "Xudoyberdi To'xtaboyev",
            'price': 40000,
            'published_year': 1976,
            'genre': self.genre1.id
        }

    def login(self, username, password):
        url = reverse('jwt-create')
        response = self.client.post(url, data={'username': username, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {response.data['access']}")

    def test_jwt_create(self):
        url = reverse('jwt-create')

        response = self.client.post(url, data={'username': 'Toxir', 'password': 'toxir12345'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_create_wrong_password(self):
        url = reverse('jwt-create')

        response = self.client.post(url, data={'username': 'Toxir', 'password': 'notogri123'})

        self.assertEqual(response.status_code, 401)

    def test_jwt_refresh(self):
        url = reverse('jwt-create')
        token = self.client.post(url, data={'username': 'Toxir', 'password': 'toxir12345'})

        response = self.client.post(reverse('jwt-refresh'), data={'refresh': token.data['refresh']})

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_get(self):
        url = reverse('book-list')

        self.login('Toxir', 'toxir12345')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        serializer = BookDetailSerializer([self.book3, self.book2, self.book1], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_search(self):
        url = reverse('book-list')

        self.login('Toxir', 'toxir12345')
        response = self.client.get(url, data={'search': 'kun'})

        self.assertEqual(response.status_code, 200)
        serializer = BookDetailSerializer([self.book1], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_filter(self):
        url = reverse('book-list')

        self.login('Toxir', 'toxir12345')
        response = self.client.get(url, data={'genre': self.genre1.id})

        self.assertEqual(response.status_code, 200)
        serializer = BookDetailSerializer([self.book2, self.book1], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_detail(self):
        url = reverse('book-detail', args=[self.book1.id])

        self.login('Toxir', 'toxir12345')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        serializer = BookDetailSerializer(self.book1)
        self.assertEqual(response.data, serializer.data)

    def test_post_admin(self):
        url = reverse('book-list')

        self.login('Admin', 'admin12345')
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Book.objects.count(), 4)
        self.assertEqual(response.data['title'], "Sariq devni minib")

    def test_post_moder(self):
        url = reverse('book-list')

        self.login('Moder', 'moder12345')
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Book.objects.count(), 4)

    def test_post_user(self):
        url = reverse('book-list')

        self.login('Toxir', 'toxir12345')
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Book.objects.count(), 3)

    def test_post_without_token(self):
        url = reverse('book-list')

        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Book.objects.count(), 3)

    def test_post_invalid(self):
        url = reverse('book-list')
        self.data['price'] = -1

        self.login('Admin', 'admin12345')
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Book.objects.count(), 3)

    def test_put_admin(self):
        url = reverse('book-detail', args=[self.book1.id])
        self.data['title'] = "O'tkan kunlar"
        self.data['price'] = 70000

        self.login('Admin', 'admin12345')
        response = self.client.put(url, data=self.data)

        self.assertEqual(response.status_code, 200)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.price, 70000)

    def test_patch_admin(self):
        url = reverse('book-detail', args=[self.book1.id])

        self.login('Admin', 'admin12345')
        response = self.client.patch(url, data={'price': 80000})

        self.assertEqual(response.status_code, 200)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.price, 80000)

    def test_put_moder(self):
        url = reverse('book-detail', args=[self.book1.id])

        self.login('Moder', 'moder12345')
        response = self.client.put(url, data=self.data)

        self.assertEqual(response.status_code, 403)

    def test_put_user(self):
        url = reverse('book-detail', args=[self.book1.id])

        self.login('Toxir', 'toxir12345')
        response = self.client.put(url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.price, 50000)

    def test_put_without_token(self):
        url = reverse('book-detail', args=[self.book1.id])

        response = self.client.put(url, data=self.data)

        self.assertEqual(response.status_code, 401)

    def test_delete_admin(self):
        url = reverse('book-detail', args=[self.book1.id])

        self.login('Admin', 'admin12345')
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Book.objects.count(), 2)

    def test_delete_user(self):
        url = reverse('book-detail', args=[self.book1.id])

        self.login('Toxir', 'toxir12345')
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Book.objects.count(), 3)

    def test_delete_without_token(self):
        url = reverse('book-detail', args=[self.book1.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Book.objects.count(), 3)
