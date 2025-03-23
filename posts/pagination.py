from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 10  # Количество объектов на странице
    page_size_query_param = 'page_size'  # Позволяет клиенту задавать размер страницы
    max_page_size = 100