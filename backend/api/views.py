import csv

from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import AuthorOrReadOnly
from api.serializers import (
    CartSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    SubscriptionSerializer,
    SubscriptionShowSerializer,
    TagSerializer,
    UserSerializer,
)
from recipes.models import (
    Cart,
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from users.models import User


class UserViewSet(UserViewSet):
    """Для работы с пользователями и подписками."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (
        AuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly,
    )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        url_name='subscribe',
    )
    def add_or_delete_subscription(self, request, id):
        """Подписаться и отписаться от автора рецепта."""
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': request.user.id, 'author': id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Follow.objects.filter(
            user=request.user,
            author=author
        ).first()
        if not subscription:
            return Response(
                {'error': 'Подписка не существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def get_subscriptions(self, request):
        """Список авторов на которых подписан."""
        authors = User.objects.filter(following__user=request.user)
        paginator = PageLimitPagination()
        result_pages = paginator.paginate_queryset(
            queryset=authors, request=request
        )
        serializer = SubscriptionShowSerializer(
            result_pages, context={'request': request}, many=True
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        url_name='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_me(self, request):
        """Информация и редактирование текущего пользователя."""
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend, )
    search_fields = ('^name', )


class TagViewSet(ReadOnlyModelViewSet):
    """Для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(ModelViewSet):
    """Для работы с рецептами."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (
        AuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly
    )
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def add_to_list(self, request, pk, serializer_class):
        """Общая функция для добавления в избранное и в конзину."""
        serializer = serializer_class(
            data={'user': request.user.pk, 'recipe': pk}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        """Добавление и удаление рецепта в список покупок."""
        return self.add_to_list(request, pk, CartSerializer)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Добавление и удаление рецепта в избранное."""
        return self.add_to_list(request, pk, FavoriteSerializer)

    def delete_item_from_list(
            self, request, model_class, recipe, error_message):
        """Общая функция для удаления из избранного и корзины."""
        deleted_items, _ = model_class.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted_items:
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Для удаления из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        return self.delete_item_from_list(
            request, Favorite, recipe, 'Рецепта нет в избранном!'
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Для удаления из корзины."""
        recipe = get_object_or_404(Recipe, id=pk)
        return self.delete_item_from_list(
            request, Cart, recipe, 'Рецепта нет в списке покупок!'
        )

    def get_queryset(self):
        """Оптимизация запросов к базе данных."""
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient', 'tags'
        ).all()
        return recipes

    def get_serializer_class(self):
        """Выбор сериализатора для рецептов."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    @staticmethod
    def ingredients_to_csv(ingredients):
        """Для скачивания списка покупок."""
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="cart.csv"'},
        )
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(["Ингредиент", "Еденица измерения", "Кол-во"])
        for ingredient in ingredients:
            writer.writerow(ingredient[key] for key in ingredient)
        return response

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """
        Формирует список уникальных ингредиентов и суммы их количества.
        """
        ingredients = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(ingredient_amount_sum=Sum('amount'))
        return self.ingredients_to_csv(ingredients)
