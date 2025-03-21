from django.contrib import admin
from .models import AuthLogin,Role,Permission, UserActivityLog, Category, SubCategory, ChildSubCategory
# Register your models here.


@admin.register(AuthLogin)
class AuthLoginadmin(admin.ModelAdmin):
    
    list_display = ['id', 'username' , 'email', 'password', 'first_name', 'last_name']



@admin.register(Category)
class Categoryadmin(admin.ModelAdmin):
    
    list_display = ['id', 'category_name', 'slug', 'short_description', 'long_description', 'meta_title', 'meta_description', 'feature_category', 'status']


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_name', 'user_type', 'action', 'ip_address', 'timestamp')
    search_fields = ('user__username', 'action', 'ip_address')
    list_filter = ('action', 'timestamp')


    def user_name(self, obj):
        return obj.user.username if obj.user else "Anonymous"
    
    def user_type(self, obj):
        return obj.user.user_type if obj.user else "N/A"

    user_name.short_description = "User Name"
    user_type.short_description = "User Type"



admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(SubCategory)
admin.site.register(ChildSubCategory)



class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_login_approved', 'is_profile_approved')
    actions = ['approve_login', 'approve_profile', 'reject_profile']

    def approve_profile(self, request, queryset):
        queryset.update(is_profile_approved=True)
    approve_profile.short_description = "Approve Vendor Profile"

    def reject_profile(self, request, queryset):
        queryset.update(is_profile_approved=False)
    reject_profile.short_description = "Reject Vendor Profile"


