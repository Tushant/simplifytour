from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User, Profile


class ProfileAdmin(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileAdmin, )
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('email', 'is_active', 'is_confirmed', )
    list_filter = ('email', 'is_active', 'is_confirmed',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {
         'fields': ('is_active', 'is_confirmed', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_confirmed', )}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)


    def get_inline_instances(self, request, obj=None):
        '''
            overriding to display the inlines only in the edit form. Otherwise we might get
            some problems because of how the Signals work. Remember that the Signal is
            responsible for creating the Profile instance.
        '''
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.register(User, CustomUserAdmin)
