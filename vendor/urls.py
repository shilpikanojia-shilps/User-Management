from django.urls import path
from vendor import views
from django.conf import settings
from django.conf.urls.static import static
from .views import delete_banner


app_name = 'vendor' 

urlpatterns = [
    path('register/', views.vendor_register, name='vendor_register'),
    path('login/', views.vendor_login, name='vendor_login'),
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('business_profile/', views.business_profile, name='business_profile'), 
    path('logout/', views.vendor_logout, name='vendor_logout'),
    path('vendor_profile/', views.vendor_profile, name = "vendor_profile"),
    path('delete_banner/', delete_banner, name="delete_banner"),
    path('logout/', views.vendor_logout, name='vendor_logout'),
    path('get-states/', views.get_states, name='get_states'),
    path('get-cities/', views.get_cities, name='get_cities'),

#=============================#
#Product
#=============================#

    path('products/', views.product_list, name='product_list'),
    path('add-product/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.product_delete, name='product_delete'),
    path('product/view/<int:pk>/', views.view_product, name='view_product'),
    path('get_subcategories/', views.get_subcategories, name='get_subcategories'),
    path('get_brands_tags/', views.get_brands_tags, name='get_brands_tags'),
    path('get_child_subcategories/', views.get_child_subcategories, name='get_child_subcategories'),
    path("get-dynamic-attributes/", views.get_dynamic_attributes, name="get_dynamic_attributes"),

#=============================#
#API
#=============================#



]





if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
