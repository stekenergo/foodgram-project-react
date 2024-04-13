import csv

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import AuthorOrReadOnly
from api.serializers import (CartSerializer, CustomUserSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             RecipeShortSerializer, SubscriptionSerializer,
                             SubscriptionShowSerializer, TagSerializer)
from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Cart, Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import User


class CustomUserViewSet(UserViewSet):
    """Для работы с пользователеми и подписками."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AuthorOrReadOnly,)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        url_name='subscribe',
    )
    def add_or_delete_subscription(self, request, id):
        """Подписка и отписка от автора рецепта."""
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': request.user.id, 'author': author.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            author_serializer = SubscriptionShowSerializer(
                author, context={'request': request}
            )
            return Response(
                author_serializer.data, status=status.HTTP_201_CREATED
            )

        # Проверяем, существует ли подписка перед удалением
        try:
            subscription = Follow.objects.get(user=request.user, author=author)
        except Follow.DoesNotExist:
            return Response(
                {"error": "Подписка не найдена."},
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
        """Список подписок на авторов."""
        authors = User.objects.filter(following__user=request.user)
        paginator = PageNumberPagination()
        result_pages = paginator.paginate_queryset(
            queryset=authors, request=request
        )
        serializer = SubscriptionShowSerializer(
            result_pages,
            context={'request': request},
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            serializer = CustomUserSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = CustomUserSerializer(
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
    permission_classes = (AuthorOrReadOnly,)
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        url_name='favorite',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def add_or_delete_favorite(self, request, pk):
        """Для добавления или удаления рецептов в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            favorite_serializer = RecipeShortSerializer(recipe)
            return Response(
                favorite_serializer.data, status=status.HTTP_201_CREATED
            )

        # Проверяем, добавлен ли рецепт в избранное пользователем
        if not Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists():
            return Response(
                {"error": "Рецепт не был добавлен в избранное пользователя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite_recipe = get_object_or_404(
            Favorite, user=request.user, recipe=recipe
        )
        favorite_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def add_or_delete_shopping_cart(self, request, pk):
        """Добавление в корзину или удаление из нее."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = CartSerializer(
                data={'user': request.user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            shopping_cart_serializer = RecipeShortSerializer(recipe)
            return Response(
                shopping_cart_serializer.data, status=status.HTTP_201_CREATED
            )

        # Проверка, был ли рецепт добавлен в корзину пользователем
        try:
            shopping_cart_recipe = Cart.objects.get(
                user=request.user,
                recipe=recipe
            )
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Рецепт был добавлен в корзину, удаляем его
        shopping_cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """Оптимизация запросов к базе данных."""
        recipes = Recipe.objects.prefetch_related(
            'recipeingredient_set__ingredient', 'tags'
        ).all()
        return recipes

    def get_serializer_class(self):
        """Выбор сериализатора для рецептов."""
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        """Добаляет данные перед вызовом save."""
        serializer.save(author=self.request.user)

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
            recipe__shopping_recipe__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(ingredient_amount_sum=Sum('amount'))

        return self.ingredients_to_csv(ingredients)
