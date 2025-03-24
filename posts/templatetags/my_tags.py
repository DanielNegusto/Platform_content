from django import template

register = template.Library()


@register.filter()
def media_filter(path):
    """
    Фильтр для добавления префикса к пути медиафайла.
    """
    if path:
        return f"/media/{path}"  # Убедитесь, что путь начинается с /
    return "#"