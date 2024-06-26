from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.constans import MIN_VALUE
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


class UserSerializer(UserSerializer):
    """Получение информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Истина, если автор в подписках иначе Ложь."""
        user = self.context.get('request').user
        return (
            not user.is_authenticated
            or user.follower.filter(author=obj).exists()
        )


class CreateUserSerializer(UserCreateSerializer):
    """Создание пользователей."""

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, value):
        if Favorite.objects.filter(
            user=value['user'], recipe=value['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже добавлен в избранное!'}
            )
        return value

    def to_representation(self, instance):
        return FavoriteAndShoppingCartResponseSerializer(instance).data


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = Cart
        fields = ('user', 'recipe')

    def validate(self, value):
        if Cart.objects.filter(
            user=value['user'], recipe=value['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже добавлен в список покупок!'}
            )
        return value

    def to_representation(self, instance):
        return FavoriteAndShoppingCartResponseSerializer(instance).data


class FavoriteAndShoppingCartResponseSerializer(serializers.Serializer):
    """Сериализатор для выдачи данных для избранного и списка покупок."""

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Отображение ингредиентов в создании рецепта."""

    name = serializers.ReadOnlyField(source='ingredient.name')
    id = serializers.ReadOnlyField(source='ingredient.id')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Добавление ингредиента в создании рецептов."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Проверка мин. значения количества ингредиента."""
        if int(value) < MIN_VALUE:
            raise serializers.ValidationError(
                'Добавьте количество ингредиента больше либо равное {}'
                .format(MIN_VALUE)
            )
        return value


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для превью рецептов."""

    name = serializers.CharField()
    cooking_time = serializers.IntegerField(min_value=MIN_VALUE)
    image = Base64ImageField(use_url=True, max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = ('name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Отображение рецептов."""

    author = UserSerializer()
    tags = TagSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        """Истина, если рецепт в избранном иначе Ложь."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.favorites.filter(
                user=request.user
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Истина, если рецепт в корзине, иначе Ложь."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.carts.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецептов."""

    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'cooking_time', 'text', 'tags', 'ingredients',
        )

    def to_representation(self, instance):
        """Если удачно создан или редактирован рецепт, менятся сериализатор."""
        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    def add_ingredients(self, ingredients, instance):
        """Добавление ингредиента в рецепт."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                ingredient=ingredient_data['ingredient'],
                recipe=instance,
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        """Создание рецепта."""
        validated_data['author'] = self.context['request'].user
        ingredients_data = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        self.add_ingredients(ingredients_data, instance)
        return instance

    def update(self, instance, validated_data):
        """Редактирование рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.clear()
        instance.ingredients.clear()
        for tag in tags_data:
            instance.tags.add(tag)
        self.add_ingredients(ingredients_data, instance)
        return super().update(instance, validated_data)

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        tags = attrs.get('tags')

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле!'}
            )

        ingredient_ids = [
            ingredient.get('ingredient').id for ingredient in ingredients
        ]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальными!'}
            )

        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Обязательное поле!'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальными!'}
            )

        return attrs

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                {'image': 'Обязательное поле!'}
            )
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Уже подписаны на этого автора.',
            ),
        ]

    def validate(self, data):
        """Проверка подписки на самого себя."""
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!',
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionShowSerializer(
            instance.author, context={'request': request}
        ).data


class SubscriptionShowSerializer(UserSerializer):
    """Отображение списка подписок на других авторов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes(self, object):
        """Список рецептов у автора на странице подписок."""
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        author_recipes = object.recipes.all()
        if limit:
            try:
                limit_int = int(limit)
                author_recipes = author_recipes[:limit_int]
            except ValueError:
                pass
        return RecipeShortSerializer(author_recipes, many=True).data

    def get_recipes_count(self, object):
        return Recipe.objects.filter(author=object).count()

    def to_representation(self, instance):
        """Переопределение метода для управления выводом."""
        data = super().to_representation(instance)
        return data
