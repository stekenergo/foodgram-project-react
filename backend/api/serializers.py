from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Cart, Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import User

from api.constans import MIN_VALUE


class CustomUserSerializer(UserSerializer):
    """Получение информации о пользователе."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """
        Истина, если автор в подписках у пользователя
        и Ложь, если нет.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomCreateUserSerializer(UserCreateSerializer):
    """Создание пользователей"""
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для покупок"""
    class Meta:
        model = Cart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Данный рецепт уже добавлен',
            )
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок"""
    class Meta:
        model = Favorite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Данный рецепт уже добавлен'
            )
        ]


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для для ингредиентов"""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тегов"""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Отображение ингредиентов в создании рецепта"""
    name = serializers.ReadOnlyField(source='ingredient.name')
    id = serializers.ReadOnlyField(source='ingredient.id')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Добавление ингредиента в создании рецептов"""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для превью рецептов"""
    image = Base64ImageField(use_url=True, max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Отображение рецептов"""
    author = CustomUserSerializer()
    tags = TagSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipeingredient_set',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        """
        Истина, если рецепт в избранном у пользователя
        Ложь, если нет.
        """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Истина, если рецепт в корзине пользователя
        Ложь, если нет.
        """

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Cart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецептов"""
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'name', 'image', 'cooking_time', 'text', 'tags', 'ingredients',
        )

    def to_representation(self, instance):
        """
        При удачном создании или редактировании рецепта, менятся сериализатор.
        """
        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    @staticmethod
    def add_ingredients(ingredients, instance):
        """Добавление ингредиента в рецепт."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                ingredient=ingredient_data['ingredient'],
                recipe=instance,
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients
        ])

    def validate_ingredients(self, ingredients):
        """
        Проверка наличия ингредиента при создании или редактировании рецепта.
        """
        list_ingredients = [
            ingredient.get('id') for ingredient in ingredients
        ]
        if not list_ingredients:
            raise serializers.ValidationError(
                "Добавьте ингредиент."
            )
        elif len(list_ingredients) != len(set(list_ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты повторяются.'
            )
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < MIN_VALUE:
                raise serializers.ValidationError(
                    'Добавьте количество ингредиента'
                )
        return ingredients

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        self.add_ingredients(ingredients, instance)
        return instance

    def update(self, instance, validated_data):
        """Редактирование рецепта."""
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time,
        )
        instance.tags.clear()
        instance.ingredients.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.add(*tags)
        recipe = instance
        self.add_ingredients(ingredients, recipe)
        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    class Meta:
        model = Follow
        fields = '__all__'
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


class SubscriptionShowSerializer(CustomUserSerializer):
    """Индикация списка подписок на других авторов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, object):
        """Список рецептов у автора на странице подписок."""
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        author_recipes = object.recipes.all()
        if limit:
            author_recipes = author_recipes[:int(limit)]
        return RecipeShortSerializer(author_recipes, many=True).data

    def get_recipes_count(self, object):
        return object.recipes.count()
