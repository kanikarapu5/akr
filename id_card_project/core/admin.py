from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Partner, Institution, Student

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')

class StudentAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'student_name', 'institution', 'partner', 'class_name')
    list_filter = ('class_name', 'institution', 'partner')
    search_fields = ('student_name', 'father_name', 'unique_id')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Partner)
admin.site.register(Institution)
admin.site.register(Student, StudentAdmin)
