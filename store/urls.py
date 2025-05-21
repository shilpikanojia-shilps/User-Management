from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'store'

urlpatterns = [
    path('user_register/', views.user_register, name = "user_register"),
    path('user_login/', views.user_login, name= "user_login"),
    # path('dashboard/', views.dashboard, name = 'dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.product_listing, name='product_listing'),
    path('get_filtered_options/', views.get_filtered_options, name='get_filtered_options'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),




] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)