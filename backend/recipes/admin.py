from django.contrib import admin
from recipes.constans import MIN_VALUE
from recipes.models import (Cart, Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = MIN_VALUE
    extra = MIN_VALUE


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'get_tags', 'get_ingredients', 'count_favorites',
        'pub_date',
    )
    list_filter = ('name', 'author', 'tags')
    inlines = (RecipeIngredientInline, )

    def count_favorites(self, obj):
        return obj.favorites.count()

    count_favorites.short_description = 'Кол-во добавлений в избранное'

    def get_tags(self, obj):
        return '\n'.join(obj.tags.values_list('name', flat=True))

    get_tags.short_description = 'Теги'

    def get_ingredients(self, obj):
        return '\n'.join(obj.ingredients.values_list('name', flat=True))

    get_ingredients.short_description = 'Ингредиенты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
