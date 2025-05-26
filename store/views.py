
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
from collections import defaultdict





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




@login_required
def products_view(request):
    return render(request, 'store/products.html')

products_view.login_required = True  # <-- Just this line






@login_required
def product_listing(request):
    categories = Category.objects.all()
    brands = Brand.objects.all()
    products = Product.objects.filter(is_approved=True)
    
    active_attribute_keys = set()
    for product in products:
        specs = product.specifications or {}
        for key in specs.keys():
            active_attribute_keys.add(key.strip())

    all_attributes = Attribute.objects.filter(name__in=active_attribute_keys).prefetch_related('options')

    attribute_filters = {}  
    attribute_counts = defaultdict(Counter)  
    selected_categories = request.GET.getlist('categories[]')
    selected_brands = request.GET.getlist('brands[]')

    selected_attribute_values = {}
    for key in request.GET:
        if key.startswith('attribute_') and key.endswith('[]'):
            attr_slug = key[len('attribute_'):-2]  # strip 'attribute_' and '[]'
            attr_obj = all_attributes.filter(name__iexact=attr_slug.replace('-', ' ')).first()
            if attr_obj:
                selected_attribute_values[attr_obj.name] = request.GET.getlist(key)
                print("Selected attributes:", selected_attribute_values)



    filtered_products = products

    if selected_categories:
        filtered_products = filtered_products.filter(category__id__in=selected_categories)
        print(filtered_products, 'ccccccc')

    if selected_brands:
        brand_names = Brand.objects.filter(id__in=selected_brands).values_list('brand_name', flat=True)
        filtered_products = filtered_products.filter(brand__id__in=selected_brands)

    for attr in all_attributes:
        attr_key = attr.name.strip()
        selected_values = selected_attribute_values.get(attr_key, [])
        if selected_values:
            filters = [Q(**{f'specifications__{attr_key}__iexact': val}) for val in selected_values]
            filtered_products = filtered_products.filter(reduce(operator.or_, filters))
            print(filtered_products, 'ggggggggg')

    # Pagination
    paginator = Paginator(filtered_products, 80)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Count filter options based on current filtered products
    for product in filtered_products.distinct():
        specs = product.specifications or {}
        for key, value in specs.items():
            if key and value:
                attribute_counts[key.strip()][value.strip()] += 1


    # Build filter options with counts
    for attribute in all_attributes:
        dropdown_options = DropdownOption.objects.filter(attribute=attribute)
        attr_name = attribute.name.strip()

        options_with_count = [
            (option, attribute_counts[attr_name].get(option.name.strip(), 0))
            for option in dropdown_options
            if attribute_counts[attr_name].get(option.name.strip(), 0) > 0
        ]
        attribute_filters[attr_name] = options_with_count

    # Count brand/category usage
    brand_counter = Counter()
    category_counter = Counter()
    for product in filtered_products:
        if product.brand:
            brand_counter[product.brand] += 1
        if product.category:
            category_counter[product.category] += 1

    brands_with_count = [(brand, brand_counter.get(brand, 0)) for brand in brands if brand_counter.get(brand, 0) > 0]

    categories_with_count = [(cat, category_counter.get(cat, 0)) for cat in categories if category_counter.get(cat, 0) > 0]


    # AJAX response
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
                'brand': product.brand.brand_name if product.brand.brand_name else "",
                'category': product.category.category_name if product.category else "",
                'image': image_url,
                'rating': product.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
            })

        filters_json = {
            'categories': [(c.id, c.category_name, category_counter.get(c, 0)) for c in categories if category_counter.get(c, 0)],
            'brands': [(b.id, b.brand_name, brand_counter.get(b, 0)) for b in brands if brand_counter.get(b, 0)],
            'attributes': {
                attr.name: [
                    (opt.id, opt.name, attribute_counts[attr.name].get(opt.name.strip(), 0))
                    for opt in attr.options.all()
                    if attribute_counts[attr.name].get(opt.name.strip(), 0)
                ]
                for attr in all_attributes
            }
        }

        

        return JsonResponse({
            'products': product_data,
            'has_next': page_obj.has_next(),
            **filters_json
        })

    # Normal render
    context = {
        'products': page_obj,
        'categories': categories_with_count,
        'brands': brands_with_count,
        'attribute_filters': attribute_filters,
        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'selected_attribute_values': selected_attribute_values
    }

    return render(request, 'store/product_listing.html', context)






@login_required
def get_filtered_options(request):
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return redirect('store:user_login')

    selected_categories = request.GET.getlist('categories[]')
    selected_brands = request.GET.getlist('brands[]')

    products = Product.objects.filter(is_approved=True)

    if selected_categories:
        products = products.filter(category__id__in=selected_categories)

    if selected_brands:
        products = products.filter(brand__id__in=selected_brands)

    print(products, "kpkpkp products")
    selected_attributes = {}
    for key, values in request.GET.lists():
        if key.startswith('attribute_'):
            attr_slug = key.replace('attribute_', '').replace('[]', '')
            selected_attributes[attr_slug] = values

    for attr_slug, values in selected_attributes.items():
        attr = Attribute.objects.filter(
            name__iexact=attr_slug.replace('-', ' ')
        ).first()
        
        if attr:
            filters = Q()
            for val in values:
                filters |= Q(
                    specifications__has_key=attr.name,
                    specifications__contains={attr.name: val}
                )
            products = products.filter(filters)
            print(products)

    categories = Category.objects.annotate(
        products_count=Count('products', filter=Q(products__in=products))
    ).filter(products_count__gt=0).values('id', 'category_name', 'products_count')

    brands = Brand.objects.annotate(
        products_count=Count('products', filter=Q(products__in=products))
    ).filter(products_count__gt=0).values('id', 'brand_name', 'products_count')

    attributes = []
    for attr in Attribute.objects.all():
        options = []
        for opt in attr.options.all():
            count = products.filter(
                specifications__has_key=attr.name,
                specifications__contains={attr.name: opt.name}
            ).count()
            if count > 0:
                options.append({
                    'id': opt.id,
                    'name': opt.name,
                    'value': opt.value,
                    'color_code': opt.color_code,
                    'product_count': count
                })
        if options:
            attributes.append({
                'id': attr.id,
                'name': attr.name,
                'options': options
            })

    return JsonResponse({
        'categories': list(categories),
        'brands': list(brands),
        'attributes': attributes
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








