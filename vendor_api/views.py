from django.shortcuts import render
from vendor.models import Product
from django.http import JsonResponse
from django.utils.html import strip_tags
import re
from django.db.models import Count
from enroll.models import Category, SubCategory, ChildSubCategory, Brand,DropdownOption,Attribute
from vendor.models import Product
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import json



def product_detail_api(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
       
        def clean_text(field):
            text = strip_tags(field or "")
            return re.sub(r'\s+', ' ', text).strip()
        
        data = {
            "id": product.id,
            "name": product.product_name,
            "category": product.category.category_name if product.category else None,
            "subcategory": product.subcategory.name if product.subcategory else None,
            "child_subcategory": product.child_subcategory.name if product.child_subcategory else None,
            "brand": product.brand,
            "status": product.status,
            "description":clean_text(product.description),
            "warranty": clean_text(product.warranty), 
            "return_policy" : clean_text(product.return_policy),
            "specifications": product.get_specifications(),
            "images": [img.image.url for img in product.images.all()],
            "vendor": {
                "name": product.vendor.full_name,
                "email": product.vendor.email,
                "contact": product.vendor.contact,
                "city": product.vendor.city.name if product.vendor.city else None,
                "state": product.vendor.state.name if product.vendor.state else None,
            }
        }
        return JsonResponse(data, safe=False)
    
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    




def all_products_api(request):
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 10))

    def clean_text(field):
        text = strip_tags(field or "")
        return re.sub(r'\s+', ' ', text).strip()

    # Initialize queryset
    all_products = Product.objects.prefetch_related('images').select_related(
        'category', 'subcategory', 'child_subcategory', 'vendor__city', 'vendor__state', 'vendor'
    ).order_by('vendor__full_name')

    # Parse filter parameter if exists
    filter_param = request.GET.get('filter')
    filter_dict = {}
    applied_filters = {}

    if filter_param:
        try:
            filter_items = re.split(r',\s*', filter_param.strip('{}'))
            for item in filter_items:
                if '=' in item:
                    key, value = map(str.strip, item.split('=', 1))
                    filter_dict[key] = value
        except Exception as e:
            print(f"Error parsing filter parameter: {e}")

    # Get filter parameters from both direct params and filter dict
    brand_id = request.GET.get('brand_id') or filter_dict.get('brand_id')
    color_id = request.GET.get('color_id') or filter_dict.get('colour_id') or filter_dict.get('color_id')
    size_id = request.GET.get('size_id') or filter_dict.get('size_id')
    category_id = request.GET.get('category_id') or filter_dict.get('category_id')

    # Apply filters and collect filter info
    if brand_id:
        try:
            brand_obj = Brand.objects.get(id=brand_id)
            all_products = all_products.filter(brand__iexact=brand_obj.brand_name)
            applied_filters['brand'] = {
                'id': brand_id,
                'name': brand_obj.brand_name
            }
        except Brand.DoesNotExist:
            applied_filters['brand'] = {
                'id': brand_id,
                'name': None,
                'error': 'Brand not found'
            }

    if color_id:
        color = DropdownOption.objects.filter(id=color_id).first()
        if color:
            all_products = all_products.filter(specifications__Colours__iexact=color.name)
            applied_filters['color'] = {
                'id': color_id,
                'name': color.name
            }
        else:
            applied_filters['color'] = {
                'id': color_id,
                'name': None,
                'error': 'Color not found'
            }

    if size_id:
        size = DropdownOption.objects.filter(id=size_id).first()
        if size:
            all_products = all_products.filter(specifications__Size__iexact=size.name)
            applied_filters['size'] = {
                'id': size_id,
                'name': size.name
            }
        else:
            applied_filters['size'] = {
                'id': size_id,
                'name': None,
                'error': 'Size not found'
            }

    if category_id:
        category = Category.objects.filter(id=category_id).first()
        if category:
            all_products = all_products.filter(category_id=category_id)
            applied_filters['category'] = {
                'id': category_id,
                'name': category.category_name
            }
        else:
            applied_filters['category'] = {
                'id': category_id,
                'name': None,
                'error': 'Category not found'
            }

    # Pagination
    paginator = Paginator(all_products, page_size)

    try:
        paginated_products = paginator.page(page)
        current_page = paginated_products.number
        total_pages = paginator.num_pages
        use_all = False
    except (PageNotAnInteger, EmptyPage):
        paginated_products = all_products
        current_page = "all"
        total_pages = 1
        use_all = True

    # Prepare response data
    data = []
    product_list = paginated_products if not use_all else all_products

    for product in product_list:
        brand_obj = Brand.objects.filter(brand_name=product.brand).first()       
        specs = json.loads(product.specifications) if isinstance(product.specifications, str) else product.specifications
        
        # Get color info
        color_value = specs.get("Colours") or specs.get("Colours", "")
        color_obj = DropdownOption.objects.filter(name__iexact=color_value).first() if color_value else None
        
        # Get size info
        size_value = specs.get("Size", "")
        size_obj = DropdownOption.objects.filter(name__iexact=size_value).first() if size_value else None

        item = {
            "id": product.id,
            "name": product.product_name,
            "category": {
                "name": product.category.category_name if product.category else None,
                "id": product.category.id if product.category else None,
            },
            "brand": {
                "name": product.brand,  
                "id": brand_obj.id if brand_obj else None,
            },
            "color": {
                "name": color_obj.name if color_obj else None,
                "id": color_obj.id if color_obj else None,
            },
            "size": {
                "name": size_obj.name if size_obj else None,
                "id": size_obj.id if size_obj else None,
            },
            "status": product.status,
            "description": clean_text(product.description),
            "warranty": clean_text(product.warranty),
            "return_policy": clean_text(product.return_policy),
            "specifications": specs,
            "images": [img.image.url for img in product.images.all()],
            "vendor": {
                "name": product.vendor.full_name,
                "email": product.vendor.email,
                "contact": product.vendor.contact,
                "city": product.vendor.city.name if product.vendor.city else None,
                "state": product.vendor.state.name if product.vendor.state else None,
            },
            "applied_filters": applied_filters  # Add applied filters to each product
        }
        data.append(item)

    print(f"Filters applied: {applied_filters}")
    print(f"Query: {all_products.query}")


    result = {
        "current_page": current_page,
        "total_pages": total_pages,
        "total_products": all_products.count(),
        "page_size": len(data),
        "filters": applied_filters,  # Structured filter information
        "products": data
    }

    return JsonResponse(result, safe=False)





def vendor_product_count_api(request):
    page = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 5))

    def clean_text(field):
        text = strip_tags(field or "")
        return re.sub(r'\s+', ' ', text).strip()

    all_products = Product.objects.prefetch_related('images').select_related(
        'category', 'subcategory', 'child_subcategory', 'vendor__city', 'vendor__state', 'vendor'
    ).order_by('vendor__full_name')

    paginator = Paginator(all_products, page_size)

    try:
        paginated_products = paginator.page(page)
        current_page = paginated_products.number
        total_pages = paginator.num_pages
    except (PageNotAnInteger, EmptyPage):
        paginated_products = all_products
        current_page = "all"
        total_pages = 1

    vendor_map = {}
    for product in paginated_products:
        vendor_id = product.vendor.id
        if vendor_id not in vendor_map:
            vendor_map[vendor_id] = {
                "vendor_id": vendor_id,
                "vendor_name": product.vendor.full_name,
                "product_count": Product.objects.filter(vendor__id=vendor_id).count(),
                "products": []
            }

        vendor_map[vendor_id]["products"].append({
            "id": product.id,
            "name": product.product_name,
            "category": product.category.category_name if product.category else None,
            "subcategory": product.subcategory.name if product.subcategory else None,
            "child_subcategory": product.child_subcategory.name if product.child_subcategory else None,
            "brand": product.brand,
            "status": product.status,
            "description": clean_text(product.description),
            "warranty": clean_text(product.warranty),
            "return_policy": clean_text(product.return_policy),
            "specifications": product.get_specifications() if hasattr(product, 'get_specifications') else {},
            "images": [img.image.url for img in product.images.all()],
            "vendor": {
                "name": product.vendor.full_name,
                "email": product.vendor.email,
                "contact": product.vendor.contact,
                "city": product.vendor.city.name if product.vendor.city else None,
                "state": product.vendor.state.name if product.vendor.state else None,
            }
        })

    result = {
        "current_page": current_page,
        "total_pages": paginator.num_pages,
        "total_products": paginator.count,
        "page_size": paginator.per_page,
        "vendors": list(vendor_map.values())
    }

    return JsonResponse(result, safe=False)





def product_count_by_category(request, category_id):
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 5))

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)

    category_products = Product.objects.filter(category_id=category.id)
    total_category_products = category_products.count()

    if per_page >= total_category_products or page > (total_category_products // per_page + 1):
        category_product_data = list(category_products.values())
        cat_page_number = "all"
        cat_total_pages = 1
    else:
        cat_paginator = Paginator(category_products, per_page)
        cat_page = cat_paginator.get_page(page)
        category_product_data = list(cat_page.object_list.values())
        cat_page_number = cat_page.number
        cat_total_pages = cat_paginator.num_pages

    subcategories = SubCategory.objects.filter(category_id=category.id)
    subcategory_data = []

    for subcat in subcategories:
        subcat_products = Product.objects.filter(subcategory_id=subcat.id)
        subcat_total = subcat_products.count()

        if per_page >= subcat_total or page > (subcat_total // per_page + 1):
            subcat_product_data = list(subcat_products.values())
            subcat_page_number = "all"
            subcat_total_pages = 1
        else:
            subcat_paginator = Paginator(subcat_products, per_page)
            subcat_page = subcat_paginator.get_page(page)
            subcat_product_data = list(subcat_page.object_list.values())
            subcat_page_number = subcat_page.number
            subcat_total_pages = subcat_paginator.num_pages

        child_subcategories = ChildSubCategory.objects.filter(subcategory_id=subcat.id)
        child_data = []

        for child in child_subcategories:
            child_products = Product.objects.filter(child_subcategory_id=child.id)
            child_total = child_products.count()

            if per_page >= child_total or page > (child_total // per_page + 1):
                child_product_data = list(child_products.values())
                child_page_number = "all"
                child_total_pages = 1
            else:
                child_paginator = Paginator(child_products, per_page)
                child_page = child_paginator.get_page(page)
                child_product_data = list(child_page.object_list.values())
                child_page_number = child_page.number
                child_total_pages = child_paginator.num_pages

            child_data.append({
                'child_subcategory_id': child.id,
                'child_subcategory_name': child.name,
                'products': child_product_data,
                'total_products': child_total,
                'current_page': child_page_number,
                'total_pages': child_total_pages
            })

        subcategory_data.append({
            'subcategory_id': subcat.id,
            'subcategory_name': subcat.name,
            'products': subcat_product_data,
            'total_products': subcat_total,
            'current_page': subcat_page_number,
            'total_pages': subcat_total_pages,
            'child_subcategories': child_data
        })

    result = {
        'current_page': cat_page_number,
        'total_pages': cat_total_pages,
        'total_products': total_category_products,
        'category_id': category.id,
        'category_name': category.category_name,
        'products': category_product_data, 
        'subcategories': subcategory_data
    }

    return JsonResponse(result, safe=False)





