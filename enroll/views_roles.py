from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Role, Permission, AuthLogin, UserProfile, UserActivityLog
from django.http import JsonResponse
import json
from django.urls import reverse
# from .permissions import ROLE_PERMISSIONS
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from enroll.models import Role, Permission
from django.utils import timezone
from .views import check_auth



@check_auth
def manage_roles(request):
    print(request.user)
    
    roles = Role.objects.all()
    permissions = Permission.objects.all()
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = [] 

    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    
    context = {
        'roles': roles,
        'permissions': permissions,
        'fullname': full_name,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'email': auth_user.email,
        'user': auth_user,
        'sidebar_items': sidebar_items,
        'user_type': user_type,
    }
    return render(request, 'enroll/manage_roles.html', context)


def get_permissions(request):
    """ Get all permissions with sub-permissions """
    permissions = Permission.objects.filter(parent__isnull=True).values("id", "name")
    data = []

    for permission in permissions:
        sub_permissions = Permission.objects.filter(parent_id=permission["id"]).values("id", "name")
        data.append({
            "id": permission["id"],
            "name": permission["name"],
            "sub_permissions": list(sub_permissions)
        })

    return JsonResponse({"permissions": data})


def assign_permission(request):
    """ Assign selected permissions to role """
    if request.method == "POST":
        role_id = request.POST.get("role_id")
        permission_ids = request.POST.getlist("permissions[]")

        role = Role.objects.get(id=role_id)
        role.permissions.set(permission_ids)

        return JsonResponse({"status": "success", "message": "Permissions assigned successfully!"})


def log_role_creation(request, role, status, error_message=None):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    """Role creation ka log maintain karne ke liye function"""
    UserActivityLog.objects.create(
        user=AuthLogin.objects.filter(id=request.session.get('user_id')).first(),
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="add_role",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "role_id": role.id if role else None,
            "role_name": role.name if role else None,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )

@check_auth
def add_role(request):
    permissions = Permission.objects.all()
    
    if request.method == 'POST':
        print(request.POST)
        role_name = request.POST.get('role_name')
        description = request.POST.get('description')
        print(f"role name :", role_name)
        print(f"description :", description)

        if not role_name:
            return render(request, 'enroll/add_role.html', {'error': 'Role name is required', 'permissions': Permission.objects.all()})

        selected_permissions = request.POST.getlist('permissions.name')
        print(selected_permissions)
        role, created = Role.objects.get_or_create(name=role_name, defaults={'description': description})

        # Clear existing permissions and add selected onesr
        if role:
            role_id = role

        else:
            role_id = created
        role.permissions.clear()
        for perm_codename in selected_permissions:
            permission = Permission.objects.filter(name=perm_codename).first()
            if permission:
                role.permissions.add(permission)
            
        role.save()
        log_role_creation(request, role, "successful")  # Successful log
        messages.success(request, f'Role "{role_name}" added successfully')
        return redirect('enroll:manage_roles') 
    else:
        permissions = Permission.objects.all()
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = [] 

    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    
    context = {       
        'user': auth_user,
        'email': auth_user.email,
        'fullname': full_name, 
        'permissions': permissions,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'sidebar_items': sidebar_items,
        'user_type': user_type,            
    }

    return render(request, 'enroll/add_role.html', context)



def log_role_edit(request, role, status, error_message=None):
    """Role edit attempt ka log maintain karne ke liye function"""
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    UserActivityLog.objects.create(
        user=AuthLogin.objects.filter(id=request.session.get('user_id')).first(),
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="edit_role",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "role_id": role.id if role else None,
            "role_name": role.name if role else None,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )


@check_auth
def edit_role(request, role_id):
    try:
        role = Role.objects.get(id=role_id)
        user = AuthLogin.objects.filter(role=role).first()
        
    except Role.DoesNotExist:
        log_role_edit(request, None, "failed", "Role not found")
        messages.error(request, 'Role not found')
        return redirect('enroll:manage_roles')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        permissions = request.POST.getlist('permissions[]')  # Array format ke liye

        print(name, description, permissions)

        role.name = name
        role.description = description
        role.save()
        

        # Clear existing permissions and add new ones

        role.permissions.clear()
        try:
            new_permissions = Permission.objects.filter(codename__in=permissions)
            role.permissions.set(new_permissions)
        except Exception as e:
            print(f"Error while updating permissions: {e}")
        for codename in permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': codename.replace('_', ' ').title(),
                    'description': ''
                }
            )
            
            role.permissions.add(permission)
        log_role_edit(request, role, "successful")  # Successful role edit log
        # permissions = Permission.objects.all()
        messages.success(request, 'Role updated successfully')
        return redirect('enroll:manage_roles')
    
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = [] 

    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    permissions = Permission.objects.all()

    context = {
        'role': role,
        'fullname': full_name,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'email': auth_user.email,
        'user': auth_user,
        'permissions': permissions,
        'sidebar_items': sidebar_items,
        'user_type': user_type,
    }
    return render(request, 'enroll/edit_role.html', context)



def log_role_deletion(request, role, status, error_message=None):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    """Role delete attempt ka log maintain karne ke liye function"""
    UserActivityLog.objects.create(
        user=AuthLogin.objects.filter(id=request.session.get('user_id')).first(),
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="delete_role",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "role_id": role.id if role else None,
            "role_name": role.name if role else None,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )


@check_auth
def delete_role(request, role_id):
    if request.method == 'POST':
        try:
            role = get_object_or_404(Role, id=role_id)
            role.delete()
            log_role_deletion(request, role, "successful")  # Successful role delete log
            messages.success(request, 'Role deleted successfully')
        except Exception as e:
            log_role_deletion(request, None, "failed", str(e))  # Failed delete log
            messages.error(request, 'Error deleting role')
    return redirect('enroll:manage_roles')



@check_auth
def manage_sub_admins(request):
    sub_admins = AuthLogin.objects.all()
    roles = Role.objects.all()  # Get all saved roles

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = [] 

    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    context = {
        'sub_admins': sub_admins,
        'roles': roles,  # Pass roles to template
        'fullname': full_name,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'email': auth_user.email,
        'user': auth_user,
        'sidebar_items': sidebar_items,
        'user_type': user_type,
    }
    return render(request, 'enroll/manage_sub_admins.html', context)




def log_sub_admin_creation(request, user, status, error_message=None):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    """Sub-Admin creation ka log maintain karne ke liye function"""
    UserActivityLog.objects.create(
        user=AuthLogin.objects.filter(id=request.session.get('user_id')).first(),
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="sub_admin_created",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "sub_admin_id": user.id if user else None,
            "sub_admin_username": user.username if user else None,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )


@check_auth
def add_sub_admin(request):
    if request.method == 'POST':
        print(request.POST, request.FILES)
        username = request.POST.get('username')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('new-password')
        role_type = request.POST.get('role')
        profile_pic = request.FILES.get('profile_pic')
        print(username, email, contact, password, role_type, profile_pic)

        try:
            # Create role with default permissions first
            role = Role.objects.filter(id=role_type).first()
            print(role.name)

            # Create the user with role
            from django.contrib.auth.hashers import make_password
            user = AuthLogin.objects.create(
                username=username,
                fullname=username,  # Using username as fullname
                email=email,
                contact=contact,
                user_type = role.name,
                role=role,  # Assign role immediately
                password=make_password(password),  # Hash password using Django's hasher
                is_staff=True
            )
            
            print(user, "++++++++++++++++++++++")
            # Save profile picture if uploaded
            if profile_pic:
                user.profile_pic = profile_pic
                user.save()
            log_sub_admin_creation(request, user, "successful")
            
            messages.success(request, 'Sub-Admin created successfully')
            return redirect('enroll:manage_sub_admins')
            
        except Exception as e:
            print(e)
            log_sub_admin_creation(request, None, "failed", str(e))
            messages.error(request, f'Error creating sub-admin: {str(e)}')
        
        return redirect('enroll:manage_sub_admins')
        
    return redirect('enroll:manage_sub_admins')



def log_sub_admin_update(request, sub_admin, status, error_message=None):
    """Sub-Admin update ka log maintain karne ke liye function"""
    
    # 🔍 Check session me user_id hai ya nahi
    
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    print(f"User ID from session: {user_id}")

    # 🔍 Check database me user exist karta hai ya nahi
    current_user = AuthLogin.objects.filter(id=user_id).first()

    print(f"DEBUG: Username - {current_user.username if current_user else 'None'}")
    print(f"DEBUG: User Type - {current_user.user_type if current_user else 'None'}")


    if current_user:
        print(f"User Found: {current_user.username} - {current_user.user_type}")
    else:
        print("⚠ No user found in the database!")

    # 📝 Log activity
    UserActivityLog.objects.create(
        user=current_user,
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="sub_admin_updated",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "sub_admin_id": sub_admin.id if sub_admin else None,
            "sub_admin_username": sub_admin.username if sub_admin else None,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )
    



@check_auth
def edit_sub_admin(request, admin_id):
    if request.method == 'POST':
        print("edit called",request.POST)
    
        try:
            user = AuthLogin.objects.get(id=request.POST.get('user_id'))
            # user = AuthLogin.objects.get(id=admin_id)
            username = request.POST.get('username')
            email = request.POST.get('email')
            contact = request.POST.get('contact')
            role_type = request.POST.get('role')
            profile_pic = request.FILES.get('profile_pic')
            new_password = request.POST.get('new-password')
            print(role_type)

            # Update password if provided
            if new_password:
                from django.contrib.auth.hashers import make_password
                user.password = make_password(new_password)
            role = Role.objects.filter(id=role_type).first()

            # Update profile picture if uploaded
            if profile_pic:
                user.profile_pic = profile_pic

            user.username = username
            user.fullname = username
            user.email = email
            user.contact = contact
            user.role = role
            user.user_type = role.name
            user.save()
            messages.success(request, 'Sub-Admin updated successfully')
        except AuthLogin.DoesNotExist:
            log_sub_admin_update(request, None, "failed", "Sub-Admin not found")
            messages.error(request, 'Sub-Admin not found')
        except Exception as e:
            log_sub_admin_update(request, None, "failed", str(e))
            messages.error(request, f'Error updating sub-admin: {str(e)}')
            
    return redirect('enroll:manage_sub_admins')



def log_sub_admin_deletion(request, sub_admin, status, error_message=None):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    """Sub-Admin deletion ka log maintain karne ke liye function"""
    
    # DEBUGGING: Print karo ki session me user_id kya aa raha hai
    
    print(f"User ID from session: {user_id}")

    # Fetch the user from the database
    current_user = AuthLogin.objects.filter(id=user_id).first()

    # DEBUGGING: Check user mil raha hai ya nahi
    if current_user:
        print(f"User Found: {current_user.username} - {current_user.user_type}")
    else:
        print("No user found!")

    # Log activity
    UserActivityLog.objects.create(
        user=current_user,
        uuser_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="sub_admin_deleted",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "sub_admin_id": sub_admin.id if sub_admin else None,
            "sub_admin_username": sub_admin.username if sub_admin else None,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )



@check_auth
def delete_sub_admin(request, admin_id):
    if request.method == 'POST':
        print("delete called")
        try:
            sub_admin = AuthLogin.objects.get(id=admin_id)
            sub_admin.delete()
            log_sub_admin_deletion(request, sub_admin, "successful")
            return JsonResponse({'success': True})
            
        except AuthLogin.DoesNotExist:
            log_sub_admin_deletion(request, None, "failed", "Sub-admin not found")
            return JsonResponse({'success': False, 'error': 'Sub-admin not found'})
        except Exception as e:
            print(e)
            log_sub_admin_deletion(request, None, "failed", str(e))
            return JsonResponse({'success': False, 'error': str(e)})
        
    return JsonResponse({'success': False, 'error': 'Invalid request method'})






@csrf_exempt
def assign_permissions_to_role(request):
    if request.method == "POST":
        data = json.loads(request.body)
        role_name = data.get("role")
        permissions = data.get("permissions", [])

        role, created = Role.objects.get_or_create(name=role_name)

        # Pehle existing permissions delete kar dete hain
        RolePermission.objects.filter(role=role).delete()

        # Naye permissions assign karte hain
        for permission_codename in permissions:
            permission = Permission.objects.filter(codename=permission_codename).first()
            if permission:
                RolePermission.objects.create(role=role, permission=permission)

        return JsonResponse({"message": "Permissions assigned successfully"}, status=200)

    return JsonResponse({"error": "Invalid request"}, status=400)
