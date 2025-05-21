
from django.shortcuts import render, get_object_or_404,redirect
from enroll.models import Category, Brand, DropdownOption, Attribute
from vendor.models import Product, ProductImage, Review
from django.db.models import Q,Count
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
from functools import reduce
import operator
from django.core.paginator import Paginator
from collections import Counter
from functools import reduce
import operator
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.views.decorators.cache import never_cache
from django.db.models import Avg




def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request. POST['email']
        pass1 = request.POST['password']
        pass2 = request.POST['confirm_password']

        print(username, email, pass1, pass2)

        if pass1!=pass2:
            messages.error(request, "Password doesn't match ")
            return redirect('store:user_register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exist')


        user = User.objects.create_user(username=username, email=email, password=pass1)
        messages.success(request, 'Account created. Please log in')
        return redirect('store:user_login')
    return render(request, 'store/register.html')


@never_cache
def user_login(request):

    if request.user.is_authenticated:
        print('User is already authenticated')
        return redirect('store:product_listing')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username, password)

        user = authenticate(request, username=username, password=password)
        print(user, 'llllllllllllll')

        if user:
            login(request, user)        
            request.session['user_email'] = user.email
            return redirect('store:product_listing')
        else:
            messages.error(request, 'Invalid Credentals')
            return redirect('store:user_login')
        
    return render(request, 'store/user_login.html')




def logout_view(request):
    logout(request)
    request.session.flush()  
    return redirect('store:user_login')


# def dashboard(request):
#     email = request.session.get('user_email', 'No email found')
 
#     if not request.user.is_authenticated:
#         return redirect('store:user_login')

#     return render(request, 'store/dashboard.html', {'user_email': email})




@login_required

def products_view(request):
    return render(request, 'store/products.html')

products_view.login_required = True  # <-- Just this line






@login_required
def product_listing(request):
    products_view.login_required = True
    categories = Category.objects.all()
    brands = Brand.objects.all()
    products = Product.objects.filter(is_approved=True)

    size_attribute = Attribute.objects.filter(name__iexact='Size').first()
    color_attribute = Attribute.objects.filter(name__iexact='Colours').first()
    occassion_attribute = Attribute.objects.filter(name__iexact='Occasion').first()
    bestfor_attribute = Attribute.objects.filter(name__iexact=' Best For').first()
    usedofor_attribute = Attribute.objects.filter(name__iexact='Used For').first()

    size_options = DropdownOption.objects.filter(attribute=size_attribute).values_list('name', flat=True) if size_attribute else []
    color_options = DropdownOption.objects.filter(attribute=color_attribute).values_list('name', flat=True) if color_attribute else []
    occassion_options = DropdownOption.objects.filter(attribute=occassion_attribute).values_list('name', flat=True) if occassion_attribute else []
    bestfor_options = DropdownOption.objects.filter(attribute=bestfor_attribute).values_list('name', flat=True) if bestfor_attribute else []
    usedfor_options = DropdownOption.objects.filter(attribute=usedofor_attribute).values_list('name', flat=True) if usedofor_attribute else []

    selected_categories = request.GET.getlist('category[]')
    selected_brands = request.GET.getlist('brand[]')
    selected_sizes = request.GET.getlist('size[]')
    selected_colors = request.GET.getlist('color[]')
    selected_occassion = request.GET.getlist('occassion[]')
    selected_bestfor = request.GET.getlist('bestfor[]')
    selected_usedfor = request.GET.getlist('usedfor[]')


    filtered_products = products

    if selected_categories:
        filtered_products = filtered_products.filter(category__id__in=selected_categories)

    if selected_brands:
        print(selected_brands, 'kkkkkkk')
        brand_names = Brand.objects.filter(id__in=selected_brands).values_list('brand_name', flat=True)
        filtered_products = filtered_products.filter(brand__in=brand_names)
        
    
    if selected_sizes:
        size_filters = [Q(**{'specifications__Size__iexact': size}) for size in selected_sizes]
        filtered_products = filtered_products.filter(reduce(operator.or_, size_filters))


    if selected_colors:       
        color_filters = [Q(**{'specifications__Colours__iexact': color}) for color in selected_colors]
        filtered_products = filtered_products.filter(reduce(operator.or_, color_filters))


    if selected_occassion:       
        occassion_filters = [Q(**{'specifications__Occasion__iexact': occassion}) for occassion in selected_occassion]
        filtered_products = filtered_products.filter(reduce(operator.or_, occassion_filters))

    if selected_bestfor:       
        bestfor_filters = [Q(**{'specifications__Best For__iexact': bestfor}) for bestfor in selected_bestfor]
        filtered_products = filtered_products.filter(reduce(operator.or_, bestfor_filters))


    if selected_usedfor:       
        usedfor_filters = [Q(**{'specifications__Used For__iexact': usedfor}) for usedfor in selected_usedfor]
        filtered_products = filtered_products.filter(reduce(operator.or_, usedfor_filters))
    
    
    # Pagination
    paginator = Paginator(filtered_products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    size_counter = Counter()
    color_counter = Counter()
    brand_counter = Counter()
    category_counter = Counter()
    occassion_counter = Counter()
    bestfor_counter = Counter()
    usedfor_counter = Counter()

    for product in filtered_products.distinct():
        specs = product.specifications or {}

        size = specs.get('Size')
        if size:
            size_counter[size] += 1

        color = specs.get('Colours')
        if color:
            color_counter[color] += 1

        occassion = specs.get('Occassion')
        if occassion:
            occassion_counter[occassion] += 1

        bestfor = specs.get('Best For')
        if bestfor:
            bestfor_counter[bestfor] += 1

        usedfor = specs.get('Used For')
        if usedfor:
            usedfor_counter[usedfor] += 1

        if product.brand:
            brand_counter[product.brand] += 1

        if product.category:
            category_counter[product.category] += 1


    size_options = [
        (option, size_counter.get(option.name.strip(), 0))
        for option in DropdownOption.objects.filter(attribute=size_attribute)
    ]

    color_options = [
        (option, color_counter.get(option.name.strip(), 0))
        for option in DropdownOption.objects.filter(attribute=color_attribute)
    ]

    occassion_options = [
        (option, occassion_counter.get(option.name.strip(), 0))
        for option in DropdownOption.objects.filter(attribute=occassion_attribute)
    ]

    bestfor_options = [
        (option, bestfor_counter.get(option.name.strip(), 0))
        for option in DropdownOption.objects.filter(attribute=bestfor_attribute)
    ]

    usedfor_options = [
        (option, usedfor_counter.get(option.name.strip(), 0))
        for option in DropdownOption.objects.filter(attribute=usedofor_attribute)
    ]

    brands_with_count = [
        (brand, brand_counter.get(brand.brand_name, 0))
        for brand in brands
    ]

    categories_with_count = [
        (cat, category_counter.get(cat, 0))
        for cat in categories
    ]


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_data = []
        for product in page_obj:
            image_url = ''
            if product.images.exists():
                image_url = request.build_absolute_uri(product.images.first().image.url)
            else:
                image_url = request.build_absolute_uri(settings.STATIC_URL + 'img/placeholder.png')
        
            product_data.append({
                'id': product.id,                 
                'name': product.product_name,
                'description': product.description[:100] + "...",
                'price': product.price,
                'brand': product.brand if product.brand else "",
                'category': product.category.category_name if product.category else "",
                'image': image_url,
                'rating': product.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
            })
            
        return JsonResponse({
            'products': product_data,
            'has_next': page_obj.has_next(),
            'categories': [(c.id, c.category_name, category_counter.get(c, 0)) for c in categories],
            'brands': [(b.id, b.brand_name, brand_counter.get(b.brand_name, 0)) for b in brands],
            'sizes': [(s.id, s.name, size_counter.get(s.name, 0)) for s in DropdownOption.objects.filter(attribute=size_attribute)],
            'colors': [(c.id, c.name, color_counter.get(c.name, 0)) for c in DropdownOption.objects.filter(attribute=color_attribute)],
            'occassion':[(o.id, o.name, occassion_counter.get(o.name, 0)) for o in DropdownOption.objects.filter(attribute= occassion_attribute)],
            'bestfor': [(bs.id, bs.name, bestfor_counter.get(bs.name, 0)) for bs in DropdownOption.objects.filter(attribute= bestfor_attribute)],
            'usedfor':[(u.id, u.name, usedfor_counter.get(u.name, 0)) for u in DropdownOption.objects.filter(attribute= usedofor_attribute)],
        })
        
    context = {
        'products': page_obj,
        'categories': categories_with_count, 
        'brands': brands_with_count, 
        'size_options': size_options, 
        'color_options': color_options,  
        'occassion_options': occassion_options,
        'bestfor_options': bestfor_options,
        'usedfor_options': usedfor_options,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'selected_sizes': selected_sizes,
        'selected_colors': selected_colors,
        'selected_occassion': selected_occassion,
        'selected_bestfor' : selected_bestfor,
        'selected_uedfor': selected_usedfor,
    }

    return render(request, 'store/product_listing.html', context)




@login_required
def get_filtered_options(request):

    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        else:
            return redirect('store:user_login') 
    
    # Get all filters from GET parameters
    categories = request.GET.getlist('categories[]')
    brands = request.GET.getlist('brands[]')
    sizes = request.GET.getlist('sizes[]')
    colors = request.GET.getlist('colors[]')
    occasions = request.GET.getlist('occasions[]')
    bestfors = request.GET.getlist('bestfors[]')
    usedfors = request.GET.getlist('usedfors[]')

    # Start with all products
    filtered_products = Product.objects.all()

    # Apply filters
    if categories:
        filtered_products = filtered_products.filter(category__id__in=categories)

    if brands:
        brand_names = Brand.objects.filter(id__in=brands).values_list('brand_name', flat=True)
        filtered_products = filtered_products.filter(brand__in=brand_names)

    if sizes:
        filtered_products = filtered_products.filter(specifications__Size__in=sizes)

    if colors:
        filtered_products = filtered_products.filter(specifications__Colours__in=colors)

    if occasions:
        filtered_products = filtered_products.filter(specifications__Occassion__in=occasions)

    if bestfors:
        filtered_products = filtered_products.filter(specifications__BestFor__in=bestfors)

    if usedfors:
        filtered_products = filtered_products.filter(specifications__UsedFor__in=usedfors)

    # Get Attribute dropdown options
    size_attribute = Attribute.objects.filter(name='Size')
    color_attribute = Attribute.objects.filter(name='Colours')
    occassion_attribute = Attribute.objects.filter(name='Occasion')
    bestfor_attribute = Attribute.objects.filter(name='Best For')
    usedfor_attribute = Attribute.objects.filter(name='Used For')

    size_options = DropdownOption.objects.filter(attribute__in=size_attribute)
    color_options = DropdownOption.objects.filter(attribute__in=color_attribute)
    occassion_options = DropdownOption.objects.filter(attribute__in=occassion_attribute)
    bestfor_options = DropdownOption.objects.filter(attribute__in=bestfor_attribute)
    usedfor_options = DropdownOption.objects.filter(attribute__in=usedfor_attribute)



    # Category counts
    category_counts = (
        filtered_products.values('category__id', 'category__category_name')
        .exclude(category__id__isnull=True)
        .exclude(category__category_name__exact='')
        .annotate(product_count=Count('id'))
        .order_by('category__category_name')
    )

    categories_data = [
        {
            'id': cat['category__id'],
            'category_name': cat['category__category_name'],
            'product_count': cat['product_count']
        }
        for cat in category_counts
    ]


    # Brand counts
    brand_counts = (
        filtered_products.values('brand')
        .exclude(brand__isnull=True)
        .exclude(brand__exact='')
        .annotate(product_count=Count('id'))
        .order_by('brand')
    )

    brands_data = [
        {
            'brand_name': brand['brand'],
            'product_count': brand['product_count'],
            'id': Brand.objects.filter(brand_name=brand['brand']).first().id
                if Brand.objects.filter(brand_name=brand['brand']).exists()
                else None
        }
        for brand in brand_counts
    ]

    # Sizes
    size_counts = (
        filtered_products.values('specifications__Size')
        .exclude(specifications__Size__isnull=True)
        .exclude(specifications__Size__exact='')
        .annotate(product_count=Count('id'))
        .order_by('specifications__Size')
    )

    sizes_data = [
        {
            'size_name': size['specifications__Size'],
            'product_count': size['product_count']
        }
        for size in size_counts
    ]

    # Colors
    color_counts = (
        filtered_products.values('specifications__Colours')
        .exclude(specifications__Colours__isnull=True)
        .exclude(specifications__Colours__exact='')
        .annotate(product_count=Count('id'))
        .order_by('specifications__Colours')
    )

    colors_data = [
        {
            'color_name': color['specifications__Colours'],
            'product_count': color['product_count']
        }
        for color in color_counts
    ]

    # Occasions
    
    occassion_counts = (
        filtered_products.values('specifications__Occassion')
        .exclude(specifications__Occassion__isnull=True)
        .exclude(specifications__Occassion__exact='')
        .annotate(product_count=Count('id'))
        .order_by('specifications__Occassion')
    )
    occassion_data = [
        {
            'occassion_name': occassion['specifications__Occassion'],
            'product_count': occassion['product_count']
        }
        for occassion in occassion_counts
    ]

    # Best For
    bestfor_data = [
        {
            'id': bestfor.id,
            'bestfor_name': bestfor.name,
            'product_count': filtered_products.filter(specifications__BestFor=bestfor.name).count()
        }
        for bestfor in bestfor_options
    ]

    # Used For
    usedfor_data = [
        {
            'id': usedfor.id,
            'usedfor_name': usedfor.name,
            'product_count': filtered_products.filter(specifications__UsedFor=usedfor.name).count()
        }
        for usedfor in usedfor_options
    ]

    return JsonResponse({
        'sizes': sizes_data,
        'colors': colors_data,
        'occassion': occassion_data,
        'bestfor': bestfor_data,
        'usedfor': usedfor_data,
        'brands': brands_data,
        'occassion_data': occassion_data,
        'categories': categories_data,
    })





@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()

    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review')
        print(rating, review)
    
        if not rating or not rating.isdigit() or int(rating) < 0 or int(rating) > 5:
            messages.error(request, 'Please select a valid rating between 1 and 5.')
            return redirect('store:product_detail', product_id=product.id)

        rating = int(rating)
        
        if rating == 0:
           
            if user_review:
                user_review.delete()
                messages.success(request, 'Your rating has been removed.')
        else:
            if user_review:
                
                user_review.rating = rating
                user_review.comment = review
                user_review.save()
                messages.success(request, 'Your rating has been updated successfully!')
            else:
               
                Review.objects.create(product=product, user=request.user, rating=rating, comment=review)
                messages.success(request, 'Rating submitted successfully!')

        avg_rating = Review.objects.filter(product=product).aggregate(avg=Avg('rating'))['avg'] or 0
        product.rating = avg_rating
        product.save()
        return redirect('store:product_detail', product_id=product.id)

    full_stars = int(product.rating) if product.rating is not None else 0
    half_star = (product.rating % 1) >= 0.5 if product.rating else False
    next_full_star = full_stars + 1 if half_star else 0
    star_range = [1, 2, 3, 4, 5]

    reviews = Review.objects.filter(product=product).order_by('-created_at')
    rating_count = reviews.count()
    review_count = reviews.exclude(comment__isnull=True).exclude(comment__exact='').count()
    has_user_commented = reviews.filter(user=request.user).exists()
    # Get recommended products (example - you might want a more sophisticated algorithm)
    
    
    price = product.price
    ten_percent = Decimal('0.20')
    min_price = price - (price * ten_percent)
    max_price = price + (price * ten_percent)


    # Recommended products from the same category and price range
    recommendations = Product.objects.filter(
        category=product.category,
        price__gte=min_price,
        price__lte=max_price
    ).exclude(id=product.id)




    context = {
        'product': product,
        'full_stars': full_stars,
        'half_star': half_star,
        'next_full_star': next_full_star,
        'star_range': star_range,
        'rating_count': rating_count,
        'review_count': review_count,
        'user_review': user_review,
        'rating_count': rating_count,
        'has_user_commented': has_user_commented,
        'review_count': review_count,
        'reviews':reviews,
        'recommendations': recommendations,
    }
    
    return render(request, 'store/product_detail.html', context)








