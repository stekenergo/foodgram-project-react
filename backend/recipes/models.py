from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from recipes.constans import MAX_LENGTH_COLOR, MAX_LENGTH_NAME, MIN_VALUE

User = get_user_model()


class Tag(models.Model):
    """Тег."""
    name = models.CharField(max_length=MAX_LENGTH_NAME, unique=True)
    color = models.CharField(max_length=MAX_LENGTH_COLOR, unique=True)
    slug = models.SlugField(max_length=MAX_LENGTH_NAME, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Recipe(models.Model):
    """Рецепты."""
    name = models.CharField(max_length=MAX_LENGTH_NAME)
    tags = models.ManyToManyField(Tag)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (минут)',
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message=f'Не может быть меньше {MIN_VALUE}.'
            ),
        ],
    )
    image = models.ImageField(
        verbose_name='Изображение рецепта',
        upload_to='recipes/',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиенты."""
    name = models.CharField(max_length=MAX_LENGTH_NAME)
    measurement_unit = models.CharField(max_length=MAX_LENGTH_NAME)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Кол-во ингредиента в рецепте."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        verbose_name='Кол-во ингредиента в рецепте.',
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message=f'Не может быть меньше {MIN_VALUE}.'
            ),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient',
            ),
        ]

    def __str__(self):
        return f'{self.recipe} готовят из {self.ingredient}'


class Follow(models.Model):
    """Подписки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка на автора'
        verbose_name_plural = 'Подписки на авторов'
        ordering = ['-author']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow',
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='can_not_follow_yourself',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'


class Cart(models.Model):
    """Покупки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_recipe',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart',
            )
        ]

    def __str__(self):
        return f'{self.user} добавлено в корзину {self.recipe}'


class Favorite(models.Model):
    """Избранное."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            )
        ]

    def __str__(self):
        return f'{self.user} добавлено в избраное {self.recipe}'
