from django.contrib import admin
from .models import VendorProfile, VendorBusinessProfile, Product
from django.utils.timezone import now

from .models import Category, SubCategory



class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_login_approved', 'is_profile_approved')
    actions = ['approve_login']

    def approve_login(self, request, queryset):
        queryset.update(is_login_approved=True)
    approve_login.short_description = "Approve Vendor Login"


admin.site.register(VendorProfile, VendorProfileAdmin)

@admin.register(VendorBusinessProfile)
class VendorBusinessProfileAdmin(admin.ModelAdmin):

    list_display = ('company_name', 'vendor', 'email', 'contact', 'address')
    # list_filter = ('is_profile_approved', 'is_profile_rejected')
    search_fields = ('vendor__name', 'rejection_reason')
    readonly_fields = ('vendor',)  # Vendor field editable nahi hoga

    def save_model(self, request, obj, form, change):
        if obj.is_profile_rejected and not obj.rejection_reason:
            obj.rejection_reason = "No reason provided."  # Default reason agar blank ho
#         super().save_model(request, obj, form, change)



# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['id', 'name']


# @admin.register(SubCategory)
# class SubCategoryAdmin(admin.ModelAdmin):
#     list_display = ['id', 'category', 'name']


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['product_name', 'vendor', 'category', 'price', 'stock_quantity', 'status']
#     list_filter = ['status', 'category', 'brand', 'is_approved']
#     search_fields = ['product_name', 'sku', 'brand', 'vendor__full_name']
#     ordering = ('-created_at',)
#     actions = ['approve_products']

#     def approve_products(self, request, queryset):
#         queryset.update(is_approved=True, approved_at=now(), status='approved')
#     approve_products.short_description = "Approve selected products"





    
