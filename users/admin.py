from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, LoginHistory

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'is_staff', 'is_active', 'last_login')
    list_filter = ('is_staff', 'is_active')

    search_fields = ('username',)
    
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Login history', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password'),
        }),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time')
    list_filter = ('login_time',)
    search_fields = ('user__username',)
    
    readonly_fields = ('user', 'login_time')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False