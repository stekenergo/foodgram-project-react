from django.contrib import admin
from django.contrib.admin import register

from users.models import User


@register(User)
class MyUserAdmin(admin.ModelAdmin):
    """Настройки административного интерфейса для модели User."""
    list_display = ('username', 'email', 'recipe_count', 'follower_count')

    def recipe_count(self, obj):
        """Функция для отображения количества рецептов."""
        return obj.recipes.count()

    def follower_count(self, obj):
        """Функция для отображения количества подписчиков."""
        return obj.following.count()

    recipe_count.short_description = 'Количество рецептов'
    follower_count.short_description = 'Количество подписчиков'
