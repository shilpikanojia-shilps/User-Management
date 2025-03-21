from django.urls import path
from . import views, views_roles, views_category
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

app_name = 'enroll'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='user_login'), 
    path('dashboard/', views.dashboard, name='dashboard'),
    path('userlist/', views.userlist, name='userlist'),
    path('adduser/', views.add_user, name='add_user'),
    path('edit/<int:id>/', views.edit_user, name='edit_user'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('deleteuser/<int:user_id>/', views.delete_user, name='delete_user'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('get-states/', views.get_states, name='get_states'),
    path('get-cities/', views.get_cities, name='get_cities'),
    path('get-all-states/', views.get_all_states, name='get_all_states'),
    path('get-cities-by-state/', views.get_cities_by_state, name='get_cities_by_state'),
    path('update-profile-pic/', views.update_profile_pic, name='update_profile_pic'),
    path('profilepic/', views.update_profile, name = 'update_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.profile_change_password, name='profile_change_password'),
    path('assign-permissions/', views_roles.assign_permissions_to_role, name='assign_permissions'),
    path('', lambda request: redirect('enroll:user_login'), name='home'),
    path('vendor_list/', views.vendor_list, name='vendor_list'),
    path('approve_vendor_login/<int:vendor_id>/', views.approve_vendor_login, name='approve_vendor_login'),
    path('reject-vendor/<int:vendor_id>/', views.reject_vendor, name='reject_vendor'),
    path("vendor_business_detail/<int:vendor_id>/", views.vendor_business_detail, name="vendor_business_detail"),
    path("approve-vendor-profile/<int:vendor_id>/", views.approve_vendor_profile, name="approve_vendor_profile"),
    path("vendors/detail/<int:vendor_id>/", views.vendor_business_detail, name="vendor_business_detail"),
    path('reject-vendor/<int:vendor_id>/', views.reject_vendor_profile, name='reject_vendor_profile'),
    path('vendor-login-approval/', views.vendor_login_approval, name='vendor_login_approval'),
    path('vendor-profile-approval/', views.vendor_profile_approval, name='vendor_profile_approval'),
    path('approve-vendor/<int:vendor_id>/', views.approve_vendor_profile, name='approve_vendor_profile'),
    path('reject-vendor/<int:vendor_id>/', views.reject_vendor_profile, name='reject_vendor_profile'),




    #banner management

    path('banners/', views.banner_list, name='banner_list'),
    path('banners/add/', views.add_banner, name='add_banner'),
    path('banners/', views.banner_list, name='banner_list'),
    path('banners/<int:banner_id>/', views.view_banner, name='view_banner'),
    path('delete-banner/<int:banner_id>/', views.delete_banner, name='delete_banner'),
    path("edit-banner/<int:banner_id>/", views.edit_banner, name="edit_banner"),
    path("delete-banner-image/", views.delete_banner_image, name="delete_banner_image"),
    
    # Role Management URLs
    path('roles/', views_roles.manage_roles, name='manage_roles'),
    path('roles/add/', views_roles.add_role, name='add_role'),
    path('roles/<int:role_id>/edit/', views_roles.edit_role, name='edit_role'),
    path('roles/<int:role_id>/delete/', views_roles.delete_role, name='delete_role'),

    
    # Sub-Admin Management URLs
    path('sub-admins/', views_roles.manage_sub_admins, name='manage_sub_admins'),
    path('sub-admin/add/', views_roles.add_sub_admin, name='add_sub_admin'),
    path('edit-sub-admin/<int:admin_id>/', views_roles.edit_sub_admin, name='edit_sub_admin'),
    path('delete-sub-admin/<int:admin_id>/', views_roles.delete_sub_admin, name='delete_sub_admin'),


    # CMS URLs
    path('cms/', views.cms_list, name='cms_list'),
    path('cms/create/', views.cms_create, name='cms_create'),
    path('cms/edit/<int:id>/', views.cms_edit, name='cms_edit'),
    path('cms/delete/<int:id>/', views.cms_delete, name='cms_delete'),
    path('cms/delete-image/<int:image_id>/', views.delete_cms_image, name='delete_cms_image'),


    # Category URLs
    path("manage-categories/", views_category.manage_categories, name="manage_categories"),
    path('add-category/', views_category.add_category, name='add_category'),
    path("edit-category/<int:category_id>/", views_category.edit_category, name="edit_category"),
    path('delete-category/<int:category_id>/', views_category.delete_category, name='delete_category'),
    path("manage-subcategories/", views_category.manage_subcategories, name="manage_subcategories"),
    path('add-subcategory/', views_category.add_subcategory, name='add_subcategory'),
    path("edit-subcategory/<int:subcategory_id>/", views_category.edit_subcategory, name="edit_subcategory"),
    path('delete-subcategory/<int:subcategory_id>/', views_category.delete_subcategory, name='delete_subcategory'),
    path("manage-child-subcategories/", views_category.manage_child_subcategories, name="manage_child_subcategories"),
    path("add-child-subcategory/", views_category.add_child_subcategory, name="add_child_subcategory"),
    path("edit-child-subcategory/<int:child_id>/", views_category.edit_child_subcategory, name="edit_child_subcategory"),
    path("delete-child-subcategory/<int:child_id>/", views_category.delete_child_subcategory, name="delete_child_subcategory"),
    path('get-subcategories/<int:category_id>/', views_category.get_subcategories, name='get_subcategories'),
    path("get_subcategories/", views_category.get_subcategories, name="get_subcategories"),
    path('get_subcategories/', views_category.get_subcategories, name='get_subcategories'),
    path('category/<int:category_id>/', views_category.view_category, name='view_category'),
    path('view-subcategory/<int:subcategory_id>/', views_category.view_subcategory, name='view_subcategory'),
    path('child-subcategory/<int:id>/', views_category.view_child_subcategory, name='view_child_subcategory'),
    path("get-child-subcategories/<int:subcategory_id>/", views_category.get_child_subcategories, name="get_child_subcategories"),

#=============================#
#Product
#=============================#
    
    
    path('vendor_product_approval/', views.vendor_product_approval, name='vendor_product_approval'),
    path('approve-product/<int:product_id>/', views.approve_product, name='approve_product'),
    path('reject-product/<int:product_id>/', views.reject_product, name='reject_product'),
    path('product/<int:product_id>/detail/', views.view_product_detail, name='view_product_detail'),


    path('brands/', views_category.brands, name='brands'),
    path('add-brand/', views_category.add_brand, name='add_brand'),
    path('edit-brand/<int:brand_id>/', views_category.edit_brand, name='edit_brand'),
    path('delete-brand/<int:brand_id>/', views_category.delete_brand, name='delete_brand'),
    path('brand/<int:brand_id>/', views_category.view_brand, name='view_brand'),
    path('add_tags/', views_category.add_tags, name='add_tags'),
    path('edit_tags/<int:tag_id>/', views_category.edit_tags, name='edit_tags'),
    path('delete-tag/<int:id>/', views_category.delete_tag, name='delete_tags'),

    path('tags/', views_category.tags, name='tags'),
    # path('delete_tags/<int:tag_id>/', views_category.delete_tags, name='delete_tags'),
    # path('get-brands-tags/', views_category.get_brands_tags, name='get_brands_tags'),



]

