from django.urls import path
from vendor_api import views



app_name = 'vendor_api' 

 
urlpatterns = [
       path('product/<int:product_id>/', views.product_detail_api, name='product_detail_api'),   
       path('api/products/', views.all_products_api, name='all_products_api'),
       path('api/vendor-product-count/', views.vendor_product_count_api, name='vendor_product_count_api'),
       path('api/category/<int:category_id>/product-count/', views.product_count_by_category, name='product_count_by_category'),


]