from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib import messages
from .models import VendorProfile, VendorBusinessProfile, State, City, Product, ProductImage
from django.contrib.auth.hashers import check_password, make_password
import os, json
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Count
from decimal import Decimal, InvalidOperation


from enroll.models import  Category, SubCategory, ChildSubCategory, Brand, Tag, Attribute, Attributeswithcatgory, Specification,SpecificationChoice, DropdownOption

# #  ========================



def safe_decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0.00')
    

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0




def get_states(request):
    try:
        states = State.objects.all().values('id', 'name').order_by('name')
        print("States fetched:", list(states))  # Debug print
        return JsonResponse({'states': list(states)})
    except Exception as e:
        print("Error fetching states:", str(e))  # Debug print
        return JsonResponse({'error': str(e)}, status=400)


def get_cities(request):
    state_name = request.GET.get('state_id')
    print(f"Fetching cities for state ID: {state_name}")
    
    if not state_name:
        return JsonResponse({'cities': []})
        
    try:
        state = State.objects.filter(name=state_name).first()

        if not state:
            print(f"State not found with name: {state_name}")
            return JsonResponse({'error': 'State not found'}, status=404)
                                                                                                                                                                                                                                                                                                                                         
        cities = City.objects.filter(state_id=state.id).order_by('name')
        
        city_list = [{'id': city.id, 'name': city.name} for city in cities]
        print(f"Found {len(city_list)} cities for state {state.name}")
        return JsonResponse({'cities': city_list})
        
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid state ID format'}, status=400)
    except State.DoesNotExist:
        return JsonResponse({'error': 'State not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===========================



# ✅ Vendor Registration
def vendor_register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')
        contact = request.POST.get('contact')
        print(full_name, email, pass1, pass2, contact)
    
        if VendorProfile.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'vendor/register.html')

        if pass1 != pass2:
            messages.error(request, "Passwords do not match")
            return render(request, 'vendor/register.html')
        
        vendor = VendorProfile.objects.create(
            full_name=full_name, 
            email=email, 
            contact=contact, 
            password = make_password(pass1),
            is_approved = False,
        )
        vendor.save()
        messages.success(request, "Registration successful! Wait for admin approval.")
        return redirect('vendor:vendor_login')
    return render(request, 'vendor/register.html')



def vendor_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(password, email)

        if not email or not password:
            messages.error(request, 'Please provide both username and password.')
            return redirect('enroll:vendor_login')

        try:
            vendor = VendorProfile.objects.get(email=email)
        
            if check_password(password, vendor.password):
                print(password, vendor.password)
                print("Password matched")
                request.session['vendor_id'] = vendor.id 

                if not vendor.is_login_approved:
                    messages.error(request, "Your account is pending approval.")
                    return redirect('vendor:vendor_login') 
            
            request.session["vendor_id"] = vendor.id
            request.session["email"] = vendor.email
            messages.success(request, "Login successful!")
            return redirect("vendor:vendor_dashboard")

        except VendorProfile.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
            return redirect("vendor:vendor_login")     

    return render(request, 'vendor/login.html')



def check_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        vendor_id = request.session.get('vendor_id')

        if not vendor_id:
            messages.error(request, "Please log in first.")
            return redirect('vendor:vendor_login')

        vendor = VendorProfile.objects.get(id=vendor_id)

        if not vendor.is_login_approved:
            messages.warning(request, "Your account is under review. You cannot create a profile yet.")
            return render(request, 'vendor/dashboard.html')
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view



@check_auth
def vendor_dashboard(request):
    vendor_id = request.session.get('vendor_id')

    if not vendor_id:
        messages.error(request, "Please log in first.")
        return redirect('vendor:vendor_login')
    
    vendor = VendorProfile.objects.get(id=vendor_id) 
    business_profile = VendorBusinessProfile.objects.filter(vendor=vendor).first()
    
    if vendor.is_profile_rejected:
        messages.error(request, f"Your business profile was rejected: {business_profile.rejection_reason}")
        return redirect("vendor:business_profile")
    
    # if not vendor.is_profile_submitted:
    #     messages.info(request, "Please complete your Business Profile.")   

    elif vendor.is_profile_submitted:
        messages.warning(request, "Profile submitted, please wait for admin approval.")
    
    elif vendor.is_profile_approved:
        messages.warning(request, "Profile approved.")
    
    elif not vendor.is_profile_approved:
        messages.warning(request, "Profile not approved.")        

    return render(request, 'vendor/dashboard.html', {'vendor': vendor,  "business_profile": business_profile, "rejection_reason": business_profile.rejection_reason if business_profile else "",})
    



@check_auth
def business_profile(request):
    vendor = VendorProfile.objects.get(id=request.session.get('vendor_id')) 
    business_profile, created = VendorBusinessProfile.objects.get_or_create(vendor=vendor)


    if request.method == "POST":

        if vendor.is_profile_approved:
            messages.warning(request, "Your profile is already approved. No further changes allowed.")
        else:
            vendor.is_profile_submitted = True  # Mark profile as submitted
            vendor.save()
            
        if not business_profile:
            business_profile = VendorBusinessProfile(vendor=vendor)

        city_id = request.POST.get("city")
        state_id = request.POST.get("state")
        state_instance = State.objects.filter(name=state_id).first()
        city_instance = City.objects.filter(name=city_id, state=state_instance).first()
        print(city_id, "________________")
        # print(state_name, "+++++++++++++++++++")
        print(state_instance, "================")
        print(city_instance, "//////////////////")


        if 'business_logo' in request.FILES:
            business_profile.business_logo = request.FILES['business_logo']  
           


        if 'banner_images' in request.FILES:
            banner_images = request.FILES.getlist('banner_images')

            # Ensure banners field is a valid list
            if business_profile.banners:
                banner_paths = business_profile.banners if business_profile.banners else []
            else:
                banner_paths = []

            for banner in banner_images:
                banner_path = f"banners/{banner.name}"
                with open(f"media/{banner_path}", "wb+") as destination:
                    for chunk in banner.chunks():
                        destination.write(chunk)
                banner_paths.append(banner_path)

            business_profile.banners = banner_paths
           

        business_profile.company_name = request.POST.get("company_name")
        business_profile.business_logo = request.FILES.get("business_logo") if "business_logo" in request.FILES else business_profile.business_logo
        business_profile.services = request.POST.get("services")
        business_profile.contact = request.POST.get("contact")
        business_profile.email = request.POST.get("email")
        business_profile.about = request.POST.get("about")
        business_profile.business_registration_number = request.POST.get("business_registration_number")

        business_profile.city = city_instance
        business_profile.state = state_instance
        business_profile.address = request.POST.get("address")
        business_profile.pincode = request.POST.get("pincode")
        business_profile.country = request.POST.get("country")
        business_profile.website = request.POST.get("website")
        business_profile.instagram = request.POST.get("instagram")
        business_profile.facebook = request.POST.get("facebook")
        business_profile.linkedin = request.POST.get("linkedin")
        
        if "gst_certificate" in request.FILES:
            business_profile.gst_certificate = request.FILES["gst_certificate"]

        if "aadhaar_pan" in request.FILES:
            business_profile.aadhaar_pan = request.FILES["aadhaar_pan"]

        business_profile.save()

        vendor.is_profile_completed = True
        vendor.is_profile_submitted = True
        vendor.is_profile_approved = False
        vendor.is_profile_rejected = False

        vendor.save()
        return redirect("vendor:business_profile")
    
    states = State.objects.all()
    cities = City.objects.all()  

    selected_state = business_profile.state.name if business_profile.state else ""
    selected_city = business_profile.city.name if business_profile.city else ""
    is_editable = vendor.is_profile_rejected and vendor.is_editable
    banner_list = business_profile.banners if isinstance(business_profile.banners, list) else []
    print(banner_list)
  
    context = {
    'vendor': vendor,
    'business_profile': business_profile,
    'states': states,
    'cities': cities,
    'selected_state': selected_state, 
    'selected_city': selected_city,  
    'is_editable': is_editable, 
    'banner_list': banner_list,
    'is_submitted': vendor.is_profile_submitted,
    'is_approved': vendor.is_profile_approved,
    'is_rejected': vendor.is_profile_rejected,
    
    }

    if vendor.is_profile_rejected:
        context['is_rejected'] = True
        messages.error(request, f"Your business profile was rejected: {business_profile.rejection_reason}")

    return render(request, "vendor/business_profile.html", context)



@csrf_exempt
def delete_banner(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        banner_path = data.get("banner_path")

        if not banner_path:
            return JsonResponse({"error": "No banner path provided"}, status=400)

        try:
            # Vendor ka business profile find karo
            vendor_id = request.session.get('vendor_id')  # Vendor ID session se lo
            business_profile = VendorBusinessProfile.objects.get(vendor_id=vendor_id)

            # Image ko list se hatao
            if banner_path in business_profile.banners:
                business_profile.banners.remove(banner_path)
                business_profile.save()

                # Image ko media folder se delete karo
                full_path = os.path.join(settings.MEDIA_ROOT, banner_path)
                if os.path.exists(full_path):
                    os.remove(full_path)

                return JsonResponse({"message": "Banner deleted successfully"}, status=200)

            return JsonResponse({"error": "Banner not found in profile"}, status=404)

        except VendorBusinessProfile.DoesNotExist:
            return JsonResponse({"error": "Vendor profile not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)



@check_auth
def vendor_profile(request):
    vendor = VendorProfile.objects.get(id=request.session.get('vendor_id')) 
    states= State.objects.all()
    cities = City.objects.all()

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        state_name= request.POST.get("state")
        about = request.POST.get("about")
        city_name = request.POST.get("city")

        if 'profile_pic' in request.FILES:
            vendor.profile_pic = request.FILES['profile_pic']
            print(vendor.profile_pic)  
            vendor.save() 

        
        state = State.objects.filter(name=state_name).first()
        city = City.objects.filter(name=city_name, state=state).first()

        if not state or not city:
            return redirect("vendor:vendor_profile")                                                                                                         

        vendor.full_name = full_name
        vendor.email = email
        vendor.contact = contact
        vendor.state = state
        vendor.city= city
        vendor.about=about
        vendor.state_name = state.name  
        vendor.city_name = city.name
        vendor.save()
        messages.success(request, "Profile Updated")
        return redirect("vendor:vendor_dashboard")

    context = {
        'vendor': vendor,
        'full_name': vendor.full_name,
        'email': vendor.email,
        'contact': vendor.contact,
        'states': states,
        'cities': cities,      
        'profile_pic': vendor.profile_pic.url if vendor.profile_pic else None, 
        
    } 
     
    return render(request, 'vendor/profile.html', context)



@check_auth
def vendor_logout(request):
    request.session.flush()  
    messages.success(request, "Logged out successfully.")
    return redirect("vendor:vendor_login")




#=====================================#
#Product
#========================================#


@check_auth
def product_list(request):
    vendor = VendorProfile.objects.get(id=request.session.get('vendor_id'))  
    products = Product.objects.select_related('category', 'subcategory').filter(vendor=vendor).order_by('-created_at')
    search_query = request.GET.get('search', '')
    
    if search_query:
        products = Product.objects.filter(
            Q(product_name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__category_name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        )

    # Pagination Logic
    paginator = Paginator(products, 10)  # 10 products per page
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)
    context = {
        'vendor': vendor,
        'full_name': vendor.full_name,
        'email': vendor.email,
        'contact': vendor.contact,
        'products': products, 
        'search_query': search_query,
        'profile_pic': vendor.profile_pic.url if vendor.profile_pic else None,
    }

    return render(request, 'products/product_list.html', context)



@check_auth
def add_product(request):
    vendor_id = request.session.get('vendor_id')
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    categories = Category.objects.all()
    selected_category = request.GET.get('category', '')
    subcategories = SubCategory.objects.all()
    childsubcategories = ChildSubCategory.objects.all()
    tags_list = Tag.objects.all()  

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        child_subcategory_id = request.POST.get("child_subcategory")
        sku = request.POST.get("sku")
        price = request.POST.get("price")
        discount_price = request.POST.get("Discount")
        description = request.POST.get("description")
        brand_id = request.POST.get("brand")
        warranty = request.POST.get("warranty")
        return_policy = request.POST.get("return_policy")
        tag_ids = request.POST.getlist("tags")
        specifications = {key: value for key, value in request.POST.items() if key.startswith("specifications")}

        brand = Brand.objects.get(id=brand_id)
        # brand_name = brand_instance.brand_name

        category = Category.objects.get(id=category_id)
        
        subcategory_id = request.POST.get('subcategory')
        subcategory = None
        if subcategory_id and subcategory_id.isdigit():
            try:
                subcategory = SubCategory.objects.get(id=int(subcategory_id))
            except SubCategory.DoesNotExist:
                pass

        child_subcategory_id = request.POST.get('child_subcategory')
        child_subcategory = None
        if child_subcategory_id and child_subcategory_id.isdigit():
            try:
                child_subcategory = ChildSubCategory.objects.get(id=int(child_subcategory_id))
            except ChildSubCategory.DoesNotExist:
                pass


        specifications = {}
        for key, value in request.POST.items():
            if key.startswith('specifications'):
                attr_id = key.split('[')[1].split(']')[0]
                specifications[attr_id] = value 

        for key, value in request.FILES.items():
            if key.startswith('specifications'):
                attr_id = key.split('[')[1].split(']')[0]
                file = request.FILES.get(key)
                if file:
                    specifications[attr_id] = file 

        print("Specifications:", specifications)
        price_speification = specifications.get('62')  
        descountprice_speification = specifications.get('63') 
        print(f"Price Specification: {price_speification}")
        print(f"Discount Price Specification: {descountprice_speification}")
            
        product = Product.objects.create(
            vendor=vendor,
            product_name=product_name,
            sku=sku,
            price=price_speification,
            description=description,
            brand=brand,
            discount_price=descountprice_speification,
            warranty=warranty,
            return_policy=return_policy,
            category=category,
            subcategory=subcategory,
            child_subcategory=child_subcategory,
            status="pending",
            is_approved=False,
            specifications=specifications,
        )

        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(product=product, image=img)
        product.set_specifications(specifications)
        product.save()
        messages.success(request, "Product submitted for approval.")
        return redirect("vendor:product_list")   

    context = {
        'vendor': vendor,
        'full_name': vendor.full_name,
        'email': vendor.email,
        'contact': vendor.contact,
        'profile_pic': vendor.profile_pic.url if vendor.profile_pic else None,
        'categories': categories,
        'subcategories': subcategories,
        'childsubcategories': childsubcategories,
        'selected_category': selected_category,
    }

    return render(request, 'products/add_product.html', context)



from django.db.models import Q

def get_dynamic_attributes(request):
    category_id = request.GET.get("category_id")
    subcategory_id = request.GET.get('subcategory_id')
    childsubcategory_id = request.GET.get('childsubcategory_id')

    print(f"Category ID: {category_id}, SubCategory ID: {subcategory_id}, ChildSubCategory ID: {childsubcategory_id}")

    filters = Q()
    
    if category_id:
        filters |= Q(attributeswithcatgory__category_id=category_id)
    if subcategory_id:
        filters |= Q(attributeswithcatgory__subcategory_id=subcategory_id)
    if childsubcategory_id:
        filters |= Q(attributeswithcatgory__child_subcategory_id=childsubcategory_id)

    attributes = Attribute.objects.filter(filters).distinct()

    attribute_data = []

    for attr in attributes:
        attr_data = {
            "id": attr.id,
            "name": attr.display_name,
            "type": attr.type.lower() if attr.type else "textbox"
        }
        if attr.type == "Dropdown":
            options = DropdownOption.objects.filter(attribute=attr).distinct('name')
            color_cde = []
            for opt in options:
                color_cde.append({
                    'name':opt.name,
                    'value':opt.value}

                )
            attr_data["options"] = color_cde
        attribute_data.append(attr_data)

    return JsonResponse({"attributes": attribute_data})




@check_auth
def edit_product(request, product_id):
    vendor_id = request.session.get('vendor_id')
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    product = get_object_or_404(Product, id=product_id, vendor=vendor)

    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    tags_list = Tag.objects.all()  
    brands = Brand.objects.all()

    if request.method == "POST":
        product.product_name = request.POST.get("product_name")
        product.sku = request.POST.get("sku")
        product.category_id = request.POST.get("category")
        product.subcategory_id = request.POST.get("subcategory")
        product.child_subcategory_id = request.POST.get("child_subcategory")
        print(product.category_id, product.subcategory_id, product.child_subcategory_id )
        product.model_number = request.POST.get("model_number")
        product.description = request.POST.get("description")
        product.price = safe_decimal(request.POST.get("price"))
        product.discount_price = safe_decimal(request.POST.get("discount_price"))
        product.weight = safe_decimal(request.POST.get("weight"))
        product.stock_quantity = safe_int(request.POST.get("stock_quantity"))
        product.dimensions = request.POST.get("dimensions")
        product.shipping_details = request.POST.get("shipping_details")
        product.warranty = request.POST.get("warranty")
        product.return_policy = request.POST.get("return_policy")
        product.tags = request.POST.get("tags", "")  
        brand_id = request.POST.get("brand")

        try:
            brand_instance = Brand.objects.get(id=brand_id)
            product.brand = brand_instance.brand_name
        except Brand.DoesNotExist:
            product.brand = None 


        image_files = request.FILES.getlist("images") 
        if image_files:           
            product.images.all().delete()
            for img in image_files:
                ProductImage.objects.create(product=product, image=img)

        if product.status in ['approved', 'rejected']:                                                                                                                                                                                                                                           
            product.status = 'pending'
            product.is_approved = False


        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect("vendor:product_list")
        
    context = {
    'vendor': vendor,
    'full_name': vendor.full_name,
    'email': vendor.email,
    'contact': vendor.contact,
    'profile_pic': vendor.profile_pic.url if vendor.profile_pic else None,
    "product": product,
    "categories": categories,
    "subcategories": subcategories,
    "brands": brands, 
    "tags_list": tags_list,
  
   
      
    }
    return render(request, "products/edit_product.html", context)


@check_auth
def product_delete(request, product_id):
    """ Allow seller to delete product """
    vendor_id = request.session.get('vendor_id')
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('vendor:product_list')


def get_subcategories(request):
    category_id = request.GET.get('category_id')  
    try:
        if category_id:
            subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
            return JsonResponse(list(subcategories), safe=False)
    except Exception as e:
        print(e, "error")
    return JsonResponse({'error': 'No category_id provided'}, status=400)


def get_child_subcategories(request):
    subcategory_id = request.GET.get('subcategory_id')
    category_id = request.GET.get('category_id')

    child_subcategories = ChildSubCategory.objects.filter(
        subcategory_id=subcategory_id,
        category_id=category_id
    ).values('id', 'name')

    return JsonResponse({'child_subcategories': list(child_subcategories)})


@check_auth
def view_product(request, pk):
    vendor_id = request.session.get('vendor_id')
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    product = get_object_or_404(Product, pk=pk)
    specifications = product.get_specifications() 

    print(specifications, "++++++++")

    context = {
        'product': product,
        'specifications': specifications,
        'vendor': vendor,
        'full_name': vendor.full_name,
        'email': vendor.email,
        'contact': vendor.contact,
        'profile_pic': vendor.profile_pic.url if vendor.profile_pic else None,

    }
    return render(request, 'products/view_product.html', context)



def get_brands_tags(request):
    try:
        brands = Brand.objects.all().values('id', 'brand_name')
        tags = Tag.objects.all().values('id', 'tag_name')

        print("BRANDS:", list(brands))  
        print("TAGS:", list(tags))     

        return JsonResponse({
            'brands': list(brands),
            'tags': list(tags)
        })

    except Exception as e:
        print("ERROR in get_brands_tags:", e)
        return JsonResponse({'error': str(e)}, status=500)
    



#===================API==============#

#====================================#




    
