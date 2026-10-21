from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
    DjangoModelPermissions
)
from .models import Genre, Book, Comment
from .serializers import GenreSerializer, GenreDetailSerializer, BookSerializer, BookDetailSerializer, CommentSerializer
from .permissions import IsOwnerOrReadOnly
from .pagination import GenrePagination, BookPagination, CommentPagination

class GenreViewSet(ModelViewSet):
    """
    Janrlar bilan ishlash.

    list:
    Janrlar ro'yxati. Nom bo'yicha qidirish: ?search=roman. Sahifalash: ?page=1&page_size=5.

    retrieve:
    Bitta janr va uning kitoblari.

    create:
    Yangi janr qo'shish. Ruxsat: add_genre huquqi.

    update:
    Janrni to'liq yangilash. Ruxsat: change_genre huquqi.

    partial_update:
    Janrni qisman yangilash. Ruxsat: change_genre huquqi.

    destroy:
    Janrni o'chirish. Ruxsat: delete_genre huquqi.
    """
    permission_classes = [DjangoModelPermissions]
    pagination_class = GenrePagination
    lookup_field = "id"
    lookup_url_kwarg = "genre_id"

    def get_queryset(self):
        genres = Genre.objects.prefetch_related("book_set").order_by("name")
        search = self.request.query_params.get("search")

        if self.action == "list":
            genres = genres.only("id", "name", "created")

        if search:
            genres = genres.filter(name__icontains=search)

        return genres

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GenreDetailSerializer
        return GenreSerializer


class BookViewSet(ModelViewSet):
    """
    Kitoblar bilan ishlash.

    list:
    Kitoblar ro'yxati. Janr bo'yicha filtr: ?genre=1. Nom bo'yicha qidirish: ?search=kun. Sahifalash: ?limit=5&offset=0.

    retrieve:
    Bitta kitob, uning janri va izohlar soni.

    create:
    Yangi kitob qo'shish. Ruxsat: add_book huquqi.

    update:
    Kitobni to'liq yangilash. Ruxsat: faqat admin.

    partial_update:
    Kitobni qisman yangilash. Ruxsat: faqat admin.

    destroy:
    Kitobni o'chirish. Ruxsat: faqat admin.
    """
    pagination_class = BookPagination
    lookup_field = "id"
    lookup_url_kwarg = "book_id"

    def get_queryset(self):
        books = Book.objects.select_related("genre").prefetch_related("genre__book_set", "comment_set").order_by("-created")
        genre_id = self.request.query_params.get("genre")
        search = self.request.query_params.get("search")

        if self.action == "list":
            books = books.defer("updated", "genre__updated")

        if genre_id and genre_id.isdigit():
            books = books.filter(genre_id=genre_id)

        if search:
            books = books.filter(title__icontains=search)

        return books

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action == "create":
            return [DjangoModelPermissions()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BookDetailSerializer
        return BookSerializer


class CommentViewSet(ModelViewSet):
    """
    Izohlar bilan ishlash.

    list:
    Izohlar ro'yxati. Kitob bo'yicha filtr: ?book=1. Yangilari birinchi chiqadi.

    retrieve:
    Bitta izoh.

    create:
    Izoh qoldirish. Tizimga kirgan foydalanuvchi bo'lishi kerak.

    update:
    Izohni to'liq yangilash. Faqat izoh egasi.

    partial_update:
    Izohni qisman yangilash. Faqat izoh egasi.

    destroy:
    Izohni o'chirish. Faqat izoh egasi.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = CommentPagination
    lookup_field = "id"
    lookup_url_kwarg = "comment_id"

    def get_queryset(self):
        comments = Comment.objects.select_related("user", "book").order_by("-created")
        book_id = self.request.query_params.get("book")

        if self.action == "list":
            comments = comments.only("id", "text", "created", "book_id", "user__username")

        if book_id and book_id.isdigit():
            comments = comments.filter(book_id=book_id)

        return comments

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
