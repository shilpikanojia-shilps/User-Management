from django.db import models
from django.conf import settings
from django.utils import timezone
import os
import time
from django.db.models.signals import post_save, pre_delete
# from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.text import slugify
import uuid



def user_image_path(instance, filename):
    # Generate a unique filename using timestamp
    ext = filename.split('.')[-1]
    filename = f"{instance.fullname}_{int(time.time())}.{ext}"
    return f'user_images/{filename}'



class Permission(models.Model):
    codename = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, null = True) 
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_permissions')


    def __str__(self):
        return self.name
    


class Role(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=255, null=True)
    permissions = models.ManyToManyField(Permission, related_name='roles')

    def __str__(self):
        return self.name
    

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, blank=True)

    class Meta:
        unique_together = ('role', 'permission')


class AuthLogin(models.Model):
    username = models.CharField(max_length=100, null=False)
    fullname = models.CharField(max_length=70, blank=True, default="Anonymous")
    email = models.EmailField(max_length=100, null=False, blank=False, default="anonymous@example.com")
    password = models.CharField(max_length=255, null=False, blank=False)
    first_name = models.CharField(max_length=50, blank=True, null= True)
    last_name = models.CharField(max_length=50, blank=True, null= True)
    last_login = models.DateTimeField(auto_now=True)
    contact = models.CharField(max_length=15, blank=True, null=True)
    age = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    profile_pic = models.ImageField(upload_to=user_image_path, blank=True, null=True)
    user_type = models.CharField(max_length=50, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    def profile_pic_url(self):
        if self.profile_pic and hasattr(self.profile_pic, 'url'):
            return self.profile_pic.url
        else:
            return settings.STATIC_URL + 'enroll/assets/images/users/avatar-1.jpg'

    def has_permission(self, permission_codename):
        if self.role:
            return self.role.permissions.filter(codename=permission_codename).exists()
        return False


class State(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'State'
        verbose_name_plural = 'States'


class City(models.Model):
    state = models.ForeignKey(State, related_name='cities', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}, {self.state.name}"

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Cities'


class CMSPage(models.Model):
    page_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    content = models.TextField(blank=True)  # For rich text content
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.page_name

    class Meta:
        ordering = ['page_name']
        verbose_name = 'CMS Page'
        verbose_name_plural = 'CMS Pages'


class CMSImage(models.Model):
    cms_page = models.ForeignKey(CMSPage, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='cms_images/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'CMS Image'
        verbose_name_plural = 'CMS Images'

    def __str__(self):
        return f"Image for {self.cms_page.page_name}"


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    user = models.OneToOneField(AuthLogin, on_delete=models.CASCADE, related_name='profile')

    contact = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    about = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def profile_pic_url(self):
        if self.profile_pic and hasattr(self.profile_pic, 'url'):
            return self.profile_pic.url
        else:
            return settings.STATIC_URL + 'enroll/assets/images/users/avatar-1.jpg'
        


class UserActivityLog(models.Model):
    user = models.ForeignKey(AuthLogin, on_delete=models.SET_NULL, null=True, blank = True)
    user_name = models.CharField(max_length=255, default='Unknown', null=False, blank = False)  # ✅ Default added
    user_type = models.CharField(max_length=100, default='Unknown', null=False, blank = False) 
    action = models.CharField(max_length=255)  # e.g., 'login', 'logout', 'password_change'
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    details = models.JSONField(null=True, blank=True)  # Additional details if needed
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.action} - {self.timestamp}"


def log_user_activity(user, action, ip_address=None, user_agent=None, details=None):
    """Helper function to create logs easily."""
    UserActivityLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )

@receiver(post_save, sender=AuthLogin)
def user_created_or_updated(sender, instance, created, **kwargs):
    """Log when a user is created or updated."""
    action = "User Created" if created else "User Updated"
    log_user_activity(user=instance, action=action)

@receiver(pre_delete, sender=AuthLogin)
def user_deleted(sender, instance, **kwargs):
    """Log when a user is deleted."""
    log_user_activity(user=instance, action="User Deleted")



class Attribute(models.Model):
    ATTRIBUTE_TYPES = [
        ('Textbox', 'Textbox'),
        ('Upload', 'Upload img/pdf'),
        ('Dropdown', 'Dropdown'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    default_value = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=50, choices=ATTRIBUTE_TYPES, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category_id = models.IntegerField(blank=True, null=True) 
    subcategory_id = models.IntegerField(blank=True, null=True)
    childsubcategory_id = models.IntegerField(blank=True, null=True)
    # dropdown_options = models.ManyToManyField('DropdownOption', blank=True)



    def __str__(self):
        return self.name



class DropdownOption(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7, blank=True, null=True)  
   

    def __str__(self):
        return f"{self.attribute.name} - {self.value}"
    
    class Meta:
        db_table = 'enroll_dropdown_option'




class Category(models.Model):
    CATEGORY_STATUS = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ]

    FEATURE_CATEGORY_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No')
    ]

    category_name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    feature_category = models.CharField(max_length=3, choices=FEATURE_CATEGORY_CHOICES, default='No')
    status = models.CharField(max_length=8, choices=CATEGORY_STATUS, default='Active')
    short_description = models.TextField(blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AuthLogin, on_delete=models.CASCADE, null=True, blank=True)

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')



    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.category_name

 




class Specification(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="specifications")
    name = models.CharField(max_length=255)  # e.g., RAM, Size, Color
    input_type = models.CharField(max_length=50, choices=[('text', 'Text'), ('number', 'Number'), ('select', 'Dropdown')])

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class SpecificationChoice(models.Model):
    specification = models.ForeignKey(Specification, on_delete=models.CASCADE, related_name="choices")
    value = models.CharField(max_length=255)  # e.g., 8GB, 16GB, Red, Blue

    def __str__(self):
        return self.value
    


class SubCategory(models.Model):

    FEATURE_CATEGORY_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No')
    ]

    # related_name unique rakha
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="all_subcategories")
    name = models.CharField(max_length=255)
    sub_slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    feature_category = models.BooleanField(max_length=3, choices=FEATURE_CATEGORY_CHOICES, default='No')
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True)



    def save(self, *args, **kwargs):
        if not self.sub_slug:
           
            base_slug = slugify(f"{self.category.category_name}-{self.name}") 
            unique_sub_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}" 
            
            # Ensure unique slug
            counter = 1
            while SubCategory.objects.filter(sub_slug=unique_sub_slug).exists():
                unique_sub_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}-{counter}"
                counter += 1
            
            self.sub_slug = unique_sub_slug
        
        super(SubCategory, self).save(*args, **kwargs)
    def __str__(self):
        return self.name




class ChildSubCategory(models.Model):

    FEATURE_CATEGORY_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No')
    ]
    # related_name unique rakha taaki conflict na ho
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="child_subcategory_categories")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="all_child_subcategories")
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='childsubcategory_images/', blank=True, null=True)
    child_slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    feature_category = models.BooleanField(default=True)
    


    def save(self, *args, **kwargs):
        if isinstance(self.feature_category, str):  
            self.feature_category = True if self.feature_category.lower() == "yes" else False
        if not self.child_slug:
            self.child_slug = slugify(self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name




class Banner(models.Model):
    title = models.CharField(max_length=255)     
    content = models.TextField(blank=True, null=True)
    

class BannerImage(models.Model):
    banner = models.ForeignKey(Banner, on_delete=models.CASCADE, related_name="images")
    images = models.ImageField(upload_to="banner_images/")
    caption = models.CharField(max_length=500, blank=True, null=True)
    link = models.URLField(blank=True, null=True)


class Brand(models.Model):
    brand_name = models.CharField(max_length=255    )
    short_description= models.CharField(max_length=255, null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    meta_title= models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='brand_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(AuthLogin, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, blank=True, null=True)
    child_subcategory = models.ForeignKey(ChildSubCategory, on_delete=models.CASCADE, blank=True, null=True)



    def __str__(self):
        return self.brand_name


class Tag(models.Model):
    tag_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, blank=True, null=True)
    child_subcategory = models.ForeignKey(ChildSubCategory, on_delete=models.CASCADE, blank=True, null=True)



    def __str__(self):
        return self.tag_name




class Attributeswithcatgory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, blank=True, null=True)
    child_subcategory = models.ForeignKey(ChildSubCategory, on_delete=models.CASCADE, blank=True, null=True)
    attribute = models.ForeignKey(Attribute,on_delete=models.CASCADE, blank=True, null=True)