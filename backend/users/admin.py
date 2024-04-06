from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from users.models import User


@register(User)
class MyUserAdmin(UserAdmin):
    """Сортировка по имени и email."""
    list_filter = ("email", "username")
