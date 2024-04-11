from foodgram.constants import PAGE_SIZE
from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Пользовательская пагинация."""
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
