from django.contrib import admin
from .models import User, Subscription


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    list_filter = ('is_active', 'is_staff', 'is_superuser')

    fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'avatar', 'description', 'consent_personal_data')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'password')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'last_code_sent')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed_to', 'created_at')  # Поля, которые будут отображаться в списке
    list_filter = ('user', 'subscribed_to')  # Фильтры для удобства поиска
    search_fields = ('user__email', 'subscribed_to__email')  # Поиск по email пользователя


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
