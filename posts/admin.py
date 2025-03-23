from django.contrib import admin
from .models import Post, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')  # Поля, которые будут отображаться в списке
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at')  # Поля, отображаемые в списке
    list_filter = ('status', 'author')  # Фильтры для боковой панели
    search_fields = ('title', 'content')  # Поля для поиска

    # Если вы хотите настроить отображение формы редактирования
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'status', 'author', 'image', 'video', 'categories')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
