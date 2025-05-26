from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import AuthLogin, UserActivityLog, UserProfile, Category, SubCategory, ChildSubCategory, Brand,Tag, Attribute
from django.utils.timezone import now
from .views import check_auth
from django.utils.text import slugify
from django.db.models import Count
from django.http import JsonResponse
from django.db import models
from django.core.exceptions import ObjectDoesNotExist



def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)


def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'subcategories': list(subcategories)})


def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = SubCategory.objects.filter(category_id=category_id).values("id", "name")
        return JsonResponse(list(subcategories), safe=False)
    return JsonResponse([], safe=False)

def get_child_subcategories(request, subcategory_id):
    # SubCategory ke andar jitne ChildSubCategory hain unko fetch karna
    child_subcategories = ChildSubCategory.objects.filter(subcategory_id=subcategory_id).values("id", "name")
    return JsonResponse(list(child_subcategories), safe=False)

@check_auth
def view_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    user_type = auth_user.user_type
    
    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        'category': category,
    }
    return render(request, "enroll/category/view_category.html", context)




@check_auth
def manage_categories(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    categories = Category.objects.all().annotate(subcategory_count=Count('all_subcategories')).values(
        'id', 'category_name', 'subcategory_count', 'feature_category', 'status'
    ) 
    category_id = request.GET.get('category_id')  
    if category_id:
        subcategories = subcategories.order_by(
            models.Case(
                models.When(category_id=category_id, then=0),
                default=1,
                output_field=models.IntegerField(),
            ),
            "category__category_name"
        )
   
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(category_name__icontains=search_query)

    paginator = Paginator(categories, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        "categories": categories,
        'page_obj': page_obj,
        'selected_category': category_id  
    }
  
    return render(request, "enroll/category/manage_categories.html", context)


@check_auth
def add_category(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    username = auth_user.username

    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        short_description = request.POST.get('short_description', '').strip()
        long_description = request.POST.get('long_description', '').strip()
        meta_title = request.POST.get('meta_title', '').strip()
        meta_description = request.POST.get('meta_description', '').strip()
        status = request.POST.get('status', 'Inactive')  
        feature_category = request.POST.get('feature_category', 'No')
        image = request.FILES.get('image', None)  
        
        if Category.objects.filter(category_name__iexact=category_name).exists():
            messages.warning(request, "Category already exists.")
            return redirect('enroll:add_category')

        if category_name and short_description:
            category = Category.objects.create(
                category_name=category_name,
                slug=slugify(category_name),  
                short_description=short_description,
                long_description=long_description,
                meta_title=meta_title,
                meta_description=meta_description,
                status=status,
                feature_category=feature_category,
                image=image,  # Save Image
                created_by=auth_user,
                created_at=now()
            )

            messages.success(request, "Category added successfully!")
            return redirect('enroll:manage_categories')

        else:
            messages.error(request, "Category name and short description cannot be empty!")

    return render(request, 'enroll/category/add_category.html', {
        'user_type': user_type,
        'username': username
    })


@check_auth
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)  
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    username = auth_user.username
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    if request.method == "POST":
        category.category_name = request.POST.get("category_name", "").strip()
        category.slug = request.POST.get("slug", "").strip()
        category.short_description = request.POST.get("short_description", "").strip()
        category.long_description = request.POST.get("long_description", "").strip()
        category.meta_title = request.POST.get("meta_title", "").strip()
        category.meta_description = request.POST.get("meta_description", "").strip()
        category.feature_category = request.POST.get("feature_category", "").strip()
        category.status = request.POST.get("status", "Inactive").strip()

        if "image" in request.FILES:
            category.image = request.FILES["image"]

        category.save() 
        messages.success(request, "Category updated successfully!")
        return redirect("enroll:manage_categories")  

    context = {
        "category": category,
        'user_type': user_type,
        'username': username,
        'fullname': full_name,
        'email': auth_user.email,
    }
    return render(request, "enroll/category/edit_category.html", context)



@check_auth
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, "Category deleted successfully!")
    return redirect('enroll:manage_categories') 




@check_auth
def view_subcategory(request, subcategory_id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    username = auth_user.username,
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)

    context = {
        'user_type': user_type,
        'username': username,
        'fullname': full_name,
        'email': auth_user.email,
        'subcategory': subcategory,
    }
    return render(request, "enroll/category/view_subcategory.html", context)



@check_auth
def manage_subcategories(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    categories = Category.objects.all()
    category_id = request.GET.get("category_id")
    if category_id:
        subcategories = subcategories.order_by(
            models.Case(
                models.When(category_id=category_id, then=0),
                default=1,
                output_field=models.IntegerField(),
            ),
            "category__category_name"
        )

    search_query = request.GET.get('search', '')   
    if search_query:
        subcategories = subcategories.filter(name__icontains=search_query)

    paginator = Paginator(subcategories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        "categories": categories,
        "subcategories": subcategories, 
        'page_obj': page_obj,
        }
    return render(request, "enroll/category/manage_subcategories.html", context)



@check_auth
def add_subcategory(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    
    categories = Category.objects.all()  
    parent_subcategories = SubCategory.objects.all()

    if request.method == 'POST':
        category_id = request.POST.get('category')
        subcategories = request.POST.getlist('subcategories[]')
        short_descriptions = request.POST.getlist('short_descriptions')
        long_descriptions = request.POST.getlist('long_descriptions')
        meta_titles = request.POST.getlist('meta_titles')
        meta_descriptions = request.POST.getlist('meta_descriptions')
        statuses = request.POST.getlist('status')
        feature_categories = request.POST.getlist('feature_category')
        images = request.FILES.getlist('images')
        print(category_id, subcategories, short_descriptions, long_descriptions, meta_titles, meta_descriptions, statuses, feature_categories, images)
      

        if not category_id or not subcategories:
            messages.error(request, "All fields are required!")
            return redirect('enroll:add_subcategory')

        category = get_object_or_404(Category, id=category_id)
        for index, subcategory_name in enumerate(subcategories):
            if subcategory_name.strip():  
                base_slug = slugify(subcategory_name.strip()) 
                unique_slug = base_slug
                counter = 1
                while SubCategory.objects.filter(sub_slug=unique_slug).exists():
                    unique_slug = f"{base_slug}-{counter}"
                    counter += 1

                status_value = statuses[index].lower() == "active" if index < len(statuses) else True
                feature_category_value = feature_categories[index] == "Yes" if index < len(feature_categories) else False

                subcategory = SubCategory.objects.create(
                    category=category,
                    name=subcategory_name.strip(),
                    sub_slug=unique_slug,  
                    short_description=short_descriptions[index] if index < len(short_descriptions) else "",
                    long_description=long_descriptions[index] if index < len(long_descriptions) else "",
                    meta_title=meta_titles[index] if index < len(meta_titles) else "",
                    meta_description=meta_descriptions[index] if index < len(meta_descriptions) else "",
                    status=status_value,
                    feature_category=feature_category_value,
                    image=images[index] if index < len(images) else None
                )
                subcategory.save()   

        messages.success(request, "SubCategories added successfully!")
        return redirect('enroll:manage_subcategories')

    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        "categories": categories,
        "parent_subcategories": parent_subcategories,
    }

    return render(request, 'enroll/category/add_subcategory.html', context)




@check_auth
def edit_subcategory(request, subcategory_id):

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    categories = Category.objects.all() 

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        feature_category = request.POST.get("feature_category")
        status = request.POST.get("status")
        meta_title = request.POST.get("meta_title")
        meta_description = request.POST.get("meta_description")
        long_description = request.POST.get("long_description")
        short_description = request.POST.get("short_description")
        image = request.FILES.get("image")

        if not name or not category_id:
            messages.error(request, "All fields are required.")
        else:
            category = get_object_or_404(Category, id=category_id)
            subcategory.name = name
            subcategory.category = category
            subcategory.feature_category = feature_category == "Yes"
            subcategory.status = status == "Active"
            subcategory.long_description = long_description if long_description else ""
            subcategory.short_description = short_description if short_description else ""
            subcategory.meta_title = meta_title if meta_title else ""
            subcategory.meta_description = meta_description if meta_description else ""
            subcategory.image = image if image else None
            
            subcategory.save()
            messages.success(request, "Subcategory updated successfully!")
            return redirect("enroll:manage_subcategories") 
    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        "categories": categories,
        "subcategory": subcategory,
    }
        

    return render(request, "enroll/category/edit_subcategory.html", context)



@check_auth
def delete_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    subcategory.delete()
    messages.success(request, "SubCategory deleted successfully!")
    return redirect('enroll:manage_subcategories')


@check_auth
def view_child_subcategory(request, id):
    childsubcategory = get_object_or_404(ChildSubCategory, id=id)  
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'childsubcategory': childsubcategory
    }
    return render(request, 'enroll/category/view_child_subcategory.html', context)



@check_auth
def manage_child_subcategories(request):

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    subcategory_id = request.GET.get('subcategory_id')
    child_subcategories = ChildSubCategory.objects.all().order_by('subcategory__category__category_name')

    if subcategory_id:
        try:
            subcategory_id = int(subcategory_id)  
        except ValueError:
            subcategory_id = None  

        if subcategory_id:
            child_subcategories = child_subcategories.order_by(
                models.Case(
                    models.When(subcategory_id=models.Value(subcategory_id), then=models.Value(0)),
                    default=models.Value(1),
                    output_field=models.IntegerField(),
                ),
                'subcategory__category__category_name'
            )

    search_query = request.GET.get('search', '')
    if search_query:
        child_subcategories = child_subcategories.filter(name__icontains=search_query)

    paginator = Paginator(child_subcategories, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.all()

    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        "categories": categories,
        'subcategories': subcategories,
        'child_subcategories': child_subcategories,
        'page_obj': page_obj,
        'selected_subcategory': subcategory_id
        }   

    return render(request, 'enroll/category/manage_child_subcategories.html', context)



@check_auth
def add_child_subcategory(request):
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    if request.method == "POST":
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        short_descriptions = request.POST.getlist("short_descriptions[]")
        long_descriptions = request.POST.getlist("long_descriptions[]")
        meta_titles = request.POST.getlist('meta_titles[]')
        meta_descriptions = request.POST.getlist('meta_descriptions[]')
        statuses = request.POST.getlist('statuses[]')
        feature_categories = request.POST.getlist('feature_categories')
        images = request.FILES.getlist('images[]')
        childsubcategories = request.POST.getlist('childsubcategories[]')
        print(feature_categories, statuses)

        category = get_object_or_404(Category, id=category_id)
        subcategory = get_object_or_404(SubCategory, id=subcategory_id)

        for index, childsubcategory_name in enumerate(childsubcategories):
            print(index, childsubcategory_name)
            if childsubcategory_name.strip():  
                base_slug = slugify(childsubcategory_name.strip())

                unique_slug = base_slug
                counter = 1
                status_value = statuses[index].lower() == "active" if index < len(statuses) else True
                feature_category_value = feature_categories[index] == "yes" if index < len(feature_categories) else False
                image_value = images[index] if index < len(images) else None

                childsubcategory = ChildSubCategory.objects.create(
                    category=category,
                    subcategory=subcategory,
                    name=childsubcategory_name.strip(),
                    child_slug=unique_slug,
                    short_description=short_descriptions[index] if index < len(short_descriptions) else "",
                    long_description=long_descriptions[index] if index < len(long_descriptions) else "",
                    meta_title=meta_titles[index] if index < len(meta_titles) else "",
                    meta_description=meta_descriptions[index] if index < len(meta_descriptions) else "",
                    status=status_value,
                    feature_category=feature_category_value,
                    image=image_value
                )
                childsubcategory.save()

        messages.success(request, "Child Subcategory added successfully!")
        return redirect("enroll:manage_child_subcategories")
    
    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        'categories': categories,
        'subcategories': subcategories,
    }

    return render(request, "enroll/category/add_child_subcategory.html", context)



@check_auth
def edit_child_subcategory(request, child_id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    child_subcategory = get_object_or_404(ChildSubCategory, id=child_id)
    categories = Category.objects.all()
    subcategories = SubCategory.objects.filter(category=child_subcategory.category.id)

    if request.method == "POST":
        child_subcategory.category = get_object_or_404(Category, id=request.POST.get("category"))
        child_subcategory.subcategory = get_object_or_404(SubCategory, id=request.POST.get("subcategory"))
        child_subcategory.name = request.POST.get("name")
        child_subcategory.short_description = request.POST.get("short_description")
        child_subcategory.long_description = request.POST.get("long_description")
        child_subcategory.meta_title = request.POST.get("meta_title")
        child_subcategory.meta_description = request.POST.get("meta_description")
        child_subcategory.status = True if request.POST.get("status") == "Active" else False
        child_subcategory.feature_category = request.POST.get("feature_category")       

        if 'image' in request.FILES:
            child_subcategory.image = request.FILES.get('image')
      
        child_subcategory.save()
        messages.success(request, "Child Subcategory updated successfully!")
        return redirect("enroll:manage_child_subcategories")
    
    context = {        
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'subcategories': subcategories,
        "categories": categories,
        "child_subcategory": child_subcategory, 
       
    }  

    return render(request, "enroll/category/edit_child_subcategory.html", context)
   



@check_auth
def delete_child_subcategory(request, child_id):
    child_subcategory = get_object_or_404(ChildSubCategory, id=child_id)
    child_subcategory.delete()
    messages.success(request, "Child Subcategory deleted successfully!")
    return redirect("enroll:manage_child_subcategories")



#======================#
#Brands
#======================#

@check_auth
def brands(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    brands = Brand.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        brands = Brand.objects.filter(brand_name__icontains=search_query)
    else:
        brands = Brand.objects.all()
    paginator = Paginator(brands, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'brands': brands,
        'search_query': search_query,

    }  
    
    return render(request, 'enroll/brand/brands.html', context )



@check_auth
def add_brand(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"


    if request.method=='POST':
        brand_name = request.POST.get('brand_name', '').strip()
        short_description = request.POST.get('short_description')
        long_description = request.POST.get('long_description')
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        image = request.FILES.get('image', None)
        

        if Brand.objects.filter(brand_name=brand_name).exists():
            messages.warning(request, "Brand already exists.")
            return redirect('enroll:add_brand')
        
        if brand_name and short_description:
            brand = Brand.objects.create(
                brand_name=brand_name,
                short_description=short_description,
                long_description=long_description,
                meta_title=meta_title,
                meta_description=meta_description,
                image=image,
                

            )

            brand.save()
            messages.success(request, "Brand added successfully!")
            return redirect('enroll:brands') 
        
    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'subcategories': subcategories,
        

    }   
    return render(request, 'enroll/brand/add_brand.html', context)



@check_auth
def edit_brand(request, brand_id):

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    brand = get_object_or_404(Brand, id=brand_id)

    if request.method == 'POST':
        brand.name = request.POST.get('brand_name', '').strip()
        brand.slug = slugify(brand.name)
        brand.short_description = request.POST.get('short_description', '').strip()
        brand.long_description = request.POST.get('long_description', '').strip()
        brand.meta_title = request.POST.get('meta_title', '').strip()
        brand.meta_description = request.POST.get('meta_description', '').strip()
        brand.status = request.POST.get('status', 'Inactive')

        if request.FILES.get('image'):
            brand.image = request.FILES['image']

        brand.save()
        messages.success(request, "Brand updated successfully!")
        return redirect('enroll:brands')
    
    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'brand': brand,

    }   

    return render(request, 'enroll/brand/edit_brand.html', context)


@check_auth
def delete_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.delete()
    messages.success(request, "Brand deleted successfully!")
    return redirect('enroll:brands')


@check_auth
def view_brand(request, brand_id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"   
    brand = get_object_or_404(Brand, id=brand_id)

    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'brand': brand,   

    }  
    return render(request, 'enroll/brand/view_brand.html', context)




@check_auth
def tags(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    tags = Tag.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        tags = Tag.objects.filter(tag_name__icontains=search_query)

    paginator = Paginator(tags, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type,
        'subcategories': subcategories,
        'page_obj': page_obj,
        'tags': tags,
        'search_query': search_query,
    

    }  
    return render(request, 'enroll/tag/tags.html', context)


@check_auth
def add_tags(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    subcategories = SubCategory.objects.all().annotate(child_subcategory_count=Count('all_child_subcategories'))
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    if request.method == 'POST':
        tag_name = request.POST.get('tag_name')
        print(tag_name)

        tags= Tag.objects.create(
            tag_name=tag_name
        )
        tags.save()
        messages.success(request, "Tag added successfully!")
        return redirect('enroll:tags')
    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type, 
    }   

    return render(request, 'enroll/tag/add_tags.html', context)



@check_auth
def edit_tags(request, tag_id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        tag.tag_name = request.POST.get('tag_name')
        print(tag.tag_name)
        tag.save()
        messages.success(request, "Tag updated successfully.")
        return redirect('enroll:tags')
    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type, 
        'tag': tag,
    }   
    return render(request, 'enroll/tag/edit_tags.html', context)



@check_auth
def delete_tag(request, id):
    tag = get_object_or_404(Tag, id=id)
    tag.delete()
    return redirect('enroll:tags')  # Redirect to your list page



# <================================================>

# <======================Attrubute=================>




@check_auth
def manage_attribute(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    attribute = Attribute.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        name = Attribute.objects.filter(name__icontains=search_query)
    else:
        name = Attribute.objects.all()

    paginator = Paginator(name, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type, 
        'attribute': attribute,
        'search_query': search_query,
        'page_obj':page_obj,
    }   
    return render(request,'enroll/category/attribute.html', context)



@check_auth
def add_attribute(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    if request.method =='POST':
        name = request.POST.get('name')
        display = request.POST.get('display')
        default_value = request.POST.get('default_value')
        type = request.POST.get('type') 
        status = request.POST.get('status')
        print(f"Name: {name}, Display: {display}, Default Value: {default_value}, Type: {type}, Status: {status}")

        atr = Attribute.objects.create(
            name=name,
            display_name=display, 
            default_value=default_value, 
            type=type,
            status=status,
        )
        atr.save()
        messages.success(request, 'Attribute added Successfully')
        return redirect('enroll:manage_attribute')

    context = {       
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type, 
        
    }   
    return render(request, 'enroll/category/add_attribut.html', context)


@check_auth
def edit_attribute(request, id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    attribute = get_object_or_404(Attribute, id=id)

    if request.method == 'POST':
        name = request.POST.get('name')
        display = request.POST.get('display')
        default_value = request.POST.get('default_value')
        type_value = request.POST.get('type')
        status = request.POST.get('status')

        if name and display:
            attribute.name = name
            attribute.display_name = display
            attribute.default_value = default_value
            attribute.type = type_value
            attribute.status = status
            attribute.save()
            messages.success(request, 'Attribute updated successfully!')
            return redirect('enroll:manage_attribute')
        else:
            messages.error(request, 'Required fields cannot be empty!')

    context = {
        'attribute': attribute,
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type, 
    }
    return render(request, 'enroll/category/edit_attribute.html', context)



@check_auth
def delete_attribute(request, id):
    attribute = get_object_or_404(Attribute, id=id)
    print(f"Deleting attribute: {attribute}") 
    attribute.delete()
    print("Attribute deleted successfully!") 
    return redirect('enroll:manage_attribute')



import json
@check_auth
def manage_attribute_category(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  
    user_type = auth_user.user_type
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    categories = Category.objects.all()
    attributes = Attribute.objects.all()
    selected_category = None
    assigned_attributes = []

    if request.method == "POST":
       
        try:
            if not request.body:
                return JsonResponse({"status": "error", "message": "Empty request body"}, status=400)
            category_id = request.POST.get("category_hidden")
            selected_attributes = request.POST.getlist("attributes")


            if not category_id:
                return JsonResponse({"status": "error", "message": "Missing Category ID"}, status=400)

            try:
                category_id = int(category_id) 
            except (TypeError, ValueError):
                return JsonResponse({"status": "error", "message": "Invalid Category ID format"}, status=400)

            category = get_object_or_404(Category, id=category_id)
            attribute_objects = Attribute.objects.filter(id__in=selected_attributes)
            category.attributes.set(attribute_objects)  
            
            print("Data saved successfully!")
            messages.success(request, 'Attribute mapped with Categories Suceessfully')
            return redirect("enroll:manage_attribute_category")
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "Category does not exist"}, status=404)

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    context = {
        'full_name': full_name,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'fullname': full_name,
        'email': auth_user.email,
        'user_type' : user_type, 
        'categories': categories, 
        'attributes': attributes,
        "selected_category": selected_category,
        "assigned_attributes": assigned_attributes,       
    }

    return render(request, 'enroll/category/manage_attribute_category.html', context)



def get_attributes(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    assigned_attributes = category.attributes.values_list('id', flat=True) 

    return JsonResponse({"assigned_attributes": list(assigned_attributes)})



def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id).values("id", "name")
    print(subcategories)
    return JsonResponse({"subcategories": list(subcategories)})


def get_child_subcategories(request, subcategory_id):
    """ Given a subcategory, fetch its child subcategories. """
    child_subcategories = ChildSubCategory.objects.filter(subcategory=subcategory_id).values("id", "name")
    print(child_subcategories)
    
    return JsonResponse({"child_subcategories": list(child_subcategories)})
    # else:
    #     return JsonResponse({"error": "No child subcategories found"}, status=404)


def get_attributes(request, category_id):
    """ Given a category/subcategory, fetch its assigned attributes. """
    category = Category.objects.get(id=category_id)
    attributes = category.attributes.values("id", "name")
    return JsonResponse({"attributes": list(attributes)})
