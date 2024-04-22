from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Кастомные настройки административного интерфейса для модели User."""
    list_display = ('username', 'email', 'recipe_count', 'follower_count')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    @admin.display(description='Количество рецептов')
    def recipe_count(self, obj):
        """Функция для отображения количества рецептов."""
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def follower_count(self, obj):
        """Функция для отображения количества подписчиков."""
        return obj.following.count()
