from django.db import models
from django.core.validators import URLValidator
from django.utils.html import strip_tags
import os
from enroll.models import Category, SubCategory, ChildSubCategory, Attribute, DropdownOption, Brand
import json
from django.core.exceptions import ObjectDoesNotExist



class State(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")


    def __str__(self):
        return f"{self.name}, {self.state.name}"
    


class VendorProfile(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)

    
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    contact = models.CharField(max_length=15)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    state_name = models.CharField(max_length=100, null=True)  # ✅ Extra field for name
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    city_name = models.CharField(max_length=100, null=True)   # ✅ Extra field for name
    about = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='vendor_profiles/', blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)  # ✅ ForeignKey hona chahiye
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    is_approved = models.BooleanField(default=False)
    is_profile_submitted = models.BooleanField(default=False)
    is_profile_approved = models.BooleanField(default=False)
    is_login_approved = models.BooleanField(default=False)
    is_profile_completed = models.BooleanField(default=False)
    is_profile_rejected = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=False) 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True) 
   
    

    class Meta:
        db_table = "vendorprofile"

    def __str__(self):
        return self.full_name
    
    def is_fully_approved(self):
        return self.is_login_approved and self.is_profile_approved


class VendorBusinessProfile(models.Model):
    

    vendor= models.OneToOneField(VendorProfile, on_delete=models.CASCADE, related_name='business_profile')
    business_logo= models.ImageField(upload_to='business_logos/', blank=True, null=True)
    company_name= models.CharField(max_length=255, null=True, blank=True)
    email=models.EmailField(max_length=100, null=True, blank=True)
    contact = models.CharField(max_length=15, null=True, blank=True)
    services= models.TextField(null=True, blank=True)
    about= models.TextField(null=True, blank=True)
    business_registration_number= models.CharField(max_length=100, unique=True, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE) 
    city = models.ForeignKey(City, on_delete=models.CASCADE) 
    pincode= models.CharField(max_length=10, null=True, blank=True)
    country= models.CharField(max_length=100, null=True, blank=True)
    payment_methods= models.CharField(max_length=50, blank=True, null=True )
    gst_certificate= models.FileField(upload_to='vendor_documents/', blank=True, null=True)
    aadhaar_pan= models.FileField(upload_to='vendor_documents/', blank=True, null=True)
    website= models.URLField(validators=[URLValidator()], blank=True, null=True)
    banners = models.JSONField(default=list, blank=True)  
    instagram= models.URLField(validators=[URLValidator()], blank=True, null=True)
    facebook= models.URLField(validators=[URLValidator()], blank=True, null=True)
    linkedin= models.URLField(validators=[URLValidator()], blank=True, null=True)
    created_at= models.DateTimeField(auto_now_add=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)


    class Meta:
        db_table= "vendorbusinessprofile"

    def save(self, *args, **kwargs):
        self.about = strip_tags(self.about)
        super().save(*args, **kwargs)

    




    
class Product(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    
    # Basic Details
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100,  null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="subcategories")
    child_subcategory = models.ForeignKey(ChildSubCategory, on_delete=models.CASCADE, blank=True, null=True)
    brand = models.ForeignKey(Brand,  on_delete=models.CASCADE, blank=True, null=True, related_name='products')
    model_number = models.CharField(max_length=100, null=True, blank=True)

    # Pricing & Discount
    price = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    discount_price = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Stock & Order
    # stock_quantity = models.PositiveIntegerField()
    min_order_quantity = models.PositiveIntegerField(default=1)
    max_order_quantity = models.PositiveIntegerField(default=10)
    is_available = models.BooleanField(default=True)

    # Specifications & Description
    description = models.TextField()
    # specifications = models.JSONField(default=dict)
    weight = models.CharField(max_length=50, null=True, blank=True)
    dimensions = models.CharField(max_length=50, null=True, blank=True)
    warranty= models.CharField(max_length=50, null=True, blank=True)
    return_policy = models.CharField(max_length=255, null=True, blank=True)
    

    # Shipping & Delivery
    shipping_time = models.CharField(max_length=50, default="5-7 days")
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    shipping_details = models.CharField(max_length=255, null=True, blank=True)

    # Media
    image_urls = models.JSONField(default=list, blank=True)
    video_url = models.URLField(null=True, blank=True)
    tags = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review = models.PositiveIntegerField(default=0)



    # Approval & Reviews
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_approved = models.BooleanField(default=False)
    admin_comments = models.TextField(null=True, blank=True)

    # Timestamps
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_message = models.TextField(blank=True, null=True)  
    jjjjj = models.TextField()

    # #meta
    # meta_title = models.CharField(max_length=255, blank=True, null=True)
    # meta_keywords = models.TextField(blank=True, null=True)
    # meta_description = models.TextField(blank=True, null=True)

    specifications = models.JSONField(default=dict) 



    def set_specifications(self, specs):
        """Specifications ko Attribute name ke saath store karo bina warning ke"""
        updated_specs = {}
        for key, value in specs.items():
            attr_id = key.replace("specifications[", "").replace("]", "")
            try:
                attribute = Attribute.objects.get(id=attr_id)
                updated_specs[attribute.name.strip()] = value.strip()
            except ObjectDoesNotExist:
                updated_specs[attr_id] = value.strip()  

        self.specifications = updated_specs  
        self.save()


    def get_specifications(self):
        """JSONField se specifications fetch karna aur clean karna"""
        if not self.specifications:
            return {}

        if isinstance(self.specifications, str): 
            try:
                return json.loads(self.specifications)
            except json.JSONDecodeError:
                return {}

        return self.specifications  


    def __str__(self):
        return str(self.id)
    

    @property
    def final_price(self):
        if self.discount_price:
            return self.price - (self.price * self.discount_price / 100)
        return self.price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.name}"





from django.contrib.auth.models import User

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')  # 1 user can give 1 review per product

    def __str__(self):
        return f'{self.user.username} - {self.product.name} - {self.rating} stars'