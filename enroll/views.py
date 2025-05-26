from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages
from django.http import JsonResponse
from .models import CMSPage, CMSImage, UserProfile, UserActivityLog, Banner, BannerImage
from django.contrib.auth import logout,login
from .models import AuthLogin, State, City, CMSPage
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
import random
import string
from django.core.mail import send_mail
from .forms import ResetPasswordForm, AuthLoginForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify
import re
import os
from django.contrib.auth.decorators import login_required
import json
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from itertools import zip_longest
from vendor.models import VendorProfile
from django.contrib import messages
from django.conf import settings
from vendor.models import VendorProfile, VendorBusinessProfile, Product






def clean_html_content(content):
    if not content:
        return content
    # Remove <p> tags but keep the content
    content = re.sub(r'<p[^>]*>', '', content)
    content = content.replace('</p>', '\n')
    # Remove extra newlines
    content = re.sub(r'\n+', '\n', content).strip()
    return content


def generate_otp():
    return str(random.randint(100000, 999999))


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        print(f"Email entered: {email}")

        if email and '@' in email:  
            if AuthLogin.objects.filter(email=email).exists(): 
                otp = str(generate_otp())
                print(f"Generated OTP: {otp}")

                try:
                    send_mail(
                        'Password Reset OTP',
                        f'Your OTP for password reset is: {otp}',
                        'no-reply@thesparxitsolutions.com', 
                        [email],
                        fail_silently=False,
                    )
                    print("Email sent successfully.")
                except Exception as e:
                    print(f"Exception while sending email: {e}")
                    messages.error(request, "Failed to send OTP. Please try again.")
                    return redirect('enroll:forgot_password')

                
                request.session['otp'] = otp
                request.session['email'] = email

                messages.success(request, "OTP has been sent to your email.")
                return redirect('enroll:verify_otp')
            else:
                messages.error(request, "Email not found. Please try again.")
        else:
            messages.error(request, "Invalid email format. Please enter a valid email.")

        return redirect('enroll:forgot_password')

    return render(request, 'enroll/forgot_password.html')



def log_otp_verification(request, email, status, error_message=None):
    """User OTP verification attempt ka log maintain karne ke liye function"""
    UserActivityLog.objects.create(
        user=AuthLogin.objects.filter(email=email).first(),  # User exist kare to fetch karega
        action="otp_verification",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "email_attempted": email,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )

def verify_otp(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        stored_email = request.session.get('email')
        
        if otp_input == stored_otp:
            log_otp_verification(request, stored_email, "successful")  # Successful verification log
            return redirect('enroll:reset_password')
        else:
            log_otp_verification(request, stored_email, "failed", "Invalid OTP entered")  # Failed attempt log
            messages.error(request, "Invalid OTP.")
            return redirect('enroll:verify_otp')
    
    return render(request, 'enroll/verify_otp.html')



def log_password_reset(request, email, status, error_message=None):
    """User password reset attempt ka log maintain karne ke liye function"""
    UserActivityLog.objects.create(
        user=AuthLogin.objects.filter(email=email).first(),  # User exist kare to fetch karega
        action="password_reset",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "email_attempted": email,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )


def reset_password(request):
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            confirm_password = form.cleaned_data['confirm_password']
            
            if new_password == confirm_password:
                email = request.session.get('email')
                user = AuthLogin.objects.get(email=email)
                user.password = make_password(new_password)
                user.save()
                log_password_reset(request, email, "successful")  # Successful reset log
                messages.success(request, "Your password has been reset successfully.")
                return redirect('enroll:user_login')  
            else:
                log_password_reset(request, request.session.get('email'), "failed", "Passwords do not match")
                messages.error(request, "Passwords do not match.")
                return redirect('enroll:reset_password') 
    else:
        form = ResetPasswordForm()
    
    return render(request, 'enroll/reset_password.html', {'form': form})



def log_user_signup(request, username, email, status, error_message=None):
    """User signup attempt ka log maintain karne ke liye function"""
    UserActivityLog.objects.create(
        user=None,  # Kyunki user signup kar raha hai, isliye abhi user instance nahi hoga
        action="signup",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "status": status,
            "username_attempted": username,
            "email_attempted": email,
            "error": error_message if error_message else None,
            "timestamp": timezone.now().isoformat()
        }
    )


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user_type = request.POST.get('role.name')  # Default to Employee if not specified
        fullname = first_name + ' ' + last_name

        # Password validation
        if pass1 != pass2:
            log_user_signup(request, username, email, "failed", "Passwords do not match")
            messages.error(request, "Passwords do not match")
            return render(request, 'enroll/signup.html')

        # Username and Email validation
        if AuthLogin.objects.filter(username=username).exists():
            log_user_signup(request, username, email, "failed", "Username already exists")
            messages.error(request, "Username already exists!")
            return render(request, 'enroll/signup.html')

        if AuthLogin.objects.filter(email=email).exists():
            log_user_signup(request, username, email, "failed", "Email already exists")
            messages.error(request, "Email already exists!")
            return render(request, 'enroll/signup.html')

        # User creation
        user = AuthLogin.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            fullname=fullname,
            password=make_password(pass1),
            user_type=user_type
        )
        user.save()

        log_user_signup(request, username, email, "successful")  # Successful signup log
               
        messages.success(request, "Your account has been successfully created.")
        return redirect('enroll:user_login')
    return render(request, 'enroll/signup.html')



def log_user_login(user, request, status="successful", **kwargs):
    """User login attempt ka log karta hai."""

    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')

    print(f"🟢 Session Data: {user_id}, {username}, {user_type}")  # ✅ Debugging line

    # 🔍 Check agar user object hai to waha bhi verify karo
    if user:
        print(f"🔵 User Object: {user.username}, {user.user_type}")

    # 📝 Save Log
    log_entry = UserActivityLog.objects.create(
        user=user,        
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="login",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={"status": status, "timestamp": timezone.now().isoformat()},
    )

    print(f"✅ Log Saved: {log_entry.user_name} - {log_entry.user_type}")  # ✅ Final Check


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return redirect('enroll:user_login')

        try:
            auth_login_user = AuthLogin.objects.get(username=username)
            if check_password(password, auth_login_user.password):
                # Create session for the user
                request.session['user_id'] = auth_login_user.id
                request.session['username'] = auth_login_user.username
                request.session['user_type'] = auth_login_user.user_type
                request.session.modified = True 
                print(request.session.get('user_id'))
                print(request.session.get('username'))
                print(request.session.get('user_type'))
                print(f"DEBUG: Login Successful - {auth_login_user.username}, {auth_login_user.user_type}")
                # ✅ Corrected function call
                log_user_login(request=request, user=auth_login_user, status="successful")
                return redirect('enroll:dashboard')  

            else:
                # Wrong password, log failed attempt
                log_user_login(request=request, user=auth_login_user, status="failed - incorrect password")
                messages.error(request, 'Invalid username or password.')
                return redirect('enroll:user_login')

        except AuthLogin.DoesNotExist:
            # Log failed login attempt for non-existent user
            UserActivityLog.objects.create(
                user=None,  # Kyunki user exist nahi karta
                action="login",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"status": "failed - user does not exist", "username_attempted": username}
            )
            messages.error(request, 'Invalid username or password.')
            return redirect('enroll:user_login')

    return render(request, 'enroll/login.html')


def logout_view(request):  
    if 'user_id' in request.session:

        try:
            user = AuthLogin.objects.get(id=request.session['user_id'])
            user_type = user.user_type
            user_id = request.session.get('user_id')
            username = request.session.get('username')
            user_type = request.session.get('user_type')

            UserActivityLog.objects.create(
                user=user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={
                    'logout_status': 'success',
                    'user_type': user_type,  # ✅ Logout karne wale ka role bhi track ho raha hai
                    'timestamp': timezone.now().isoformat()  # ✅ Logout ka exact time store ho raha hai
                }
            )
        except AuthLogin.DoesNotExist:
            pass
    
    # Clear the session
    request.session.flush()
    logout(request)
    return redirect('enroll:user_login')



# Custom middleware to handle authentication
def check_auth(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'Please login first')
            return redirect('enroll:user_login')
        try:
            auth_user = AuthLogin.objects.get(id=request.session.get('user_id'))
            request.user = auth_user  # Set auth_user as request.user for compatibility
            return view_func(request, *args, **kwargs)
        except AuthLogin.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('enroll:user_login')
    return wrapper



@check_auth
def dashboard(request):

    if not request.session.get('user_id'):
        return redirect('enroll:user_login')
    
    
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type

    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')

     # ✅ Log Dashboard Visit
    UserActivityLog.objects.create(
        user=auth_user,
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="dashboard_visit",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={
            "user_type": user_type,
            "dashboard_access": "successful"
        }
    )


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
        'fullname': full_name,
        'profile_pic': user_profile.profile_pic_url() if hasattr(user_profile, 'profile_pic_url') else None,
        'email': auth_user.email,
        'user': auth_user,  # Pass the auth_user instead of request.user
        'sidebar_items': sidebar_items,
        'user_type': user_type,
    }
    return render(request, 'enroll/index-2.html', context)


@check_auth
def userlist(request):

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')


    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = []
    
    search_query = request.GET.get('search', '')
    
    if search_query:
        users = AuthLogin.objects.filter(
            Q(fullname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(contact__icontains=search_query)
        )
        
        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="user_search_attempt",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"status": "successful" if users.exists() else "failed", "query": search_query}
        )

        if not users.exists():
            messages.warning(request, 'User not available')
            return redirect('enroll:userlist')
    else:
        users = AuthLogin.objects.all().order_by('fullname') 

        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="user_list_viewed",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"status": "successful"}
        )

    
    paginator = Paginator(users, 10)  
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number) 
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    return render(request, 'enroll/userlist.html', {'page_obj': page_obj, 'user': request.user, 'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None ,'fullname': full_name, 'email': auth_user.email, 'sidebar_items': sidebar_items, 'user_type': user_type,})



@check_auth
def add_user(request):
    states = State.objects.all().order_by('name')  

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')

    if request.method == 'POST':
        print(request.POST, "-------------")
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        age = request.POST.get('age')
        city = request.POST.get('city')
        state = request.POST.get('state')

        # Log the received data
        print("Full Name:", fullname)
        print("Email:", email)
        print("Contact:", contact)
        print("Age:", age)
        print("City:", city)
        print("State:", state)


        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="user_add_attempt",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"fullname": fullname, "email": email}
        )

        # Validation for required fields
        if not (fullname and email and contact and age and city and state):
            messages.error(request, "All fields are required.")

            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="user_add_failed",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"reason": "missing_fields", "fullname": fullname, "email": email}
            )

            return render(request, 'enroll/adduser.html', {'states': states, 'data': request.POST})
        
        # Check if email already exists
        if AuthLogin.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")


            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="user_add_failed",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"reason": "email_exists", "email": email}
            )
            return render(request, 'enroll/adduser.html', {'states': states, 'data': request.POST})

        
        # Create the new user
        AuthLogin.objects.create(
            fullname=fullname,
            email=email,
            contact=contact,
            age=age,
            city=city,
            state=state,
        )

        messages.success(request, "User added successfully")


        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="user_added_successfully",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"fullname": fullname, "email": email}
        )

        return redirect('enroll:userlist')
   

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = []

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)            
    return render(request, 'enroll/adduser.html', {'states': states, 'user': request.user, 'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None, 'email':request.user.email, 'fullname':request.user.fullname, 'sidebar_items': sidebar_items, 'user_type': user_type,})



@check_auth
def edit_user(request, id):
    try:
        user = AuthLogin.objects.get(pk=id)
        all_states = State.objects.all().order_by('name')
        auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
        user_type = auth_user.user_type
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_id = request.session.get('user_id')
        username = request.session.get('username')
        user_type = request.session.get('user_type')

                
        if request.method == 'POST':
            user.fullname = request.POST.get('fullname')
            user.email = request.POST.get('email')
            user.contact = request.POST.get('contact')
            user.age = request.POST.get('age')
            state_id = request.POST.get('state')
            city_id = request.POST.get('city')


              # 🔹 Log edit attempt
            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="user_edit_attempt",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"edited_user": user.id, "fullname": user.fullname, "email": user.email}
            )
            


            if not (user.fullname and user.email and user.contact and user.age and state_id and city_id):
                messages.error(request, "All fields are required.")

                # 🔹 Log validation failure
                UserActivityLog.objects.create(
                    user=auth_user,
                    user_name=username if username else "Session Missing",
                    user_type=user_type if user_type else "Session Missing",
                    action="user_edit_failed",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    details={"reason": "missing_fields", "edited_user": user.id}
                )
                
                return redirect('enroll:edit_user', id=id)

            # Validate state and city IDs
            if not state_id or not city_id:
                messages.error(request, "Please select both state and city")
                return redirect('enroll:edit_user', id=id)
            
            try:
                state = State.objects.get(id=state_id)
                city = City.objects.get(id=city_id)
                # Verify city belongs to selected state
                if city.state_id != int(state_id):
                    messages.error(request, "Selected city does not belong to the selected state")

                    # 🔹 Log invalid state/city selection

                    UserActivityLog.objects.create(
                        user=auth_user,
                        user_name=username if username else "Session Missing",
                        user_type=user_type if user_type else "Session Missing",
                        action="user_edit_failed",
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        details={"reason": "invalid_city_state", "edited_user": user.id}
                    )

                    return redirect('enroll:edit_user', id=id)
                
                user.state = state.name
                user.city = city.name
            except (State.DoesNotExist, City.DoesNotExist, ValueError):
                messages.error(request, "Invalid state or city selected")
                return redirect('enroll:edit_user', id=id)
            
            if 'profile_pic' in request.FILES:
                user.profile_pic = request.FILES['profile_pic']
            
            user.save()
            # 🔹 Log successful update
            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="user_edited_successfully",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"edited_user": user.id, "fullname": user.fullname, "email": user.email}
            )

            messages.success(request, "User updated successfully!")
            return redirect('enroll:userlist')
        
        # Get current state and city objects
        current_state = None
        current_cities = []
        try:
            if user.state:
                current_state = State.objects.get(name=user.state)
                current_cities = City.objects.filter(state=current_state).order_by('name')
        except State.DoesNotExist:
            pass
       

        if user_type == 'Employee':
            sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
        elif user_type == 'Admin':
            sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
        elif user_type == 'HR':
            sidebar_items = ['dashboard', 'user_list'] 
        else:
            sidebar_items = []
        
        context = {
            'user': user,
            'states': all_states,
            'cities': current_cities,
            'current_state': current_state,
            'current_city': user.city,
            'email':request.user.email,
            'fullname':request.user.fullname,
            'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
            'sidebar_items': sidebar_items,
            'user_type': user_type,
            
        }
        return render(request, 'enroll/edituser.html', context)
        
    except AuthLogin.DoesNotExist:
        messages.error(request, "User not found!")

        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="user_edit_failed",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"reason": "user_not_found", "edited_user_id": id}
        )

        return redirect('enroll:userlist')




def delete_user(request, user_id):
    if request.method == "GET":
        user = get_object_or_404(AuthLogin, id=user_id)
        user.delete()
        return redirect('enroll:userlist')
    return HttpResponse("Invalid request method", status=405) 




@check_auth
def profile_view(request):
    # Get the authenticated user's ID from the session
    auth_user_id = request.session.get('user_id')
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')
    if not auth_user_id:
        return redirect('enroll:login')

    # Fetch the user and user profile
    auth_user = AuthLogin.objects.filter(id=auth_user_id).last()
    if not auth_user:
        return redirect('enroll:login')  # Redirect if user not found

    user_profile = UserProfile.objects.filter(user=auth_user).last()
    if not user_profile:
        user_profile = UserProfile.objects.create(user=auth_user)

    if request.method == 'POST':

        old_data = {
            "first_name": auth_user.first_name,
            "last_name": auth_user.last_name,
            "email": auth_user.email,
            "contact": user_profile.contact,
            "about": user_profile.about,
        }
        # Update UserProfile fields
        user_profile.contact = request.POST.get('contact')
        user_profile.about = request.POST.get('about')
        user_profile.save()

        # Update auth_user fields
        auth_user.first_name = request.POST.get('first_name')
        auth_user.last_name = request.POST.get('last_name')
        auth_user.email = request.POST.get('email')
        auth_user.save()

        new_data = {
            "first_name": auth_user.first_name,
            "last_name": auth_user.last_name,
            "email": auth_user.email,
            "contact": user_profile.contact,
            "about": user_profile.about,
        }

        # ✅ Log the Profile Update
        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="Profile Updated",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"old_data": old_data, "new_data": new_data}
        )

        return redirect('enroll:profile')  # Redirect after saving changes

    # ✅ Log the Profile View
    UserActivityLog.objects.create(
        user=auth_user,
        user_name=username if username else "Session Missing",
        user_type=user_type if user_type else "Session Missing",
        action="Profile Viewed",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        details={"status": "viewed"}
    )
    # Calculate full name
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type

    if user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list']
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms'] 
    else:
        sidebar_items = [] 


    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    # Prepare context to pass to the template
    context = {
        'fullname': full_name,
        'email': auth_user.email,
        'first_name': auth_user.first_name,
        'last_name': auth_user.last_name,
        'contact': auth_user.contact,
        'about': user_profile.about,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,

        'sidebar_items': sidebar_items,
        'user_type': user_type,
    }

    return render(request, 'enroll/profile.html', context)    



@check_auth
def update_profile_pic(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        profile_pic = request.FILES['profile_pic']
        print(profile_pic)
        
        try:
            auth_user_id = request.session.get('user_id')  # This is the authenticated user
            auth_user = AuthLogin.objects.get(id= auth_user_id)
            # Get or create the UserProfile for the logged-in user
            user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
            user_id = request.session.get('user_id')
            username = request.session.get('username')
            user_type = request.session.get('user_type')

            

            # 🛑 Delete old profile picture safely
            if user_profile.profile_pic:
                old_path = user_profile.profile_pic.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            print(f"✅ Profile picture saved at: {user_profile.profile_pic.url if user_profile.profile_pic else None}")
            # Save new profile picture
            auth_user.profile_pic = profile_pic
            auth_user.save()

            # ✅ Log the Profile Picture Update
            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="Profile Picture Updated",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"profile_pic":  user_profile.profile_pic.url if user_profile.profile_pic else None},
            )

            messages.success(request, "Profile picture updated successfully!")
        except AuthLogin.DoesNotExist:
            messages.error(request, "User profile not found.")
        
        return redirect('enroll:profile')
    
    messages.error(request, "Failed to update profile picture. Please try again.")
    return redirect('enroll:profile')





@check_auth
def update_profile(request):
    if request.method == 'POST':
        print(request.POST)
        try:
            # Use the logged-in user directly
            auth_user_id = request.session.get('user_id')  # This is the authenticated user
            auth_user = AuthLogin.objects.get(id= auth_user_id)
            user_id = request.session.get('user_id')
            username = request.session.get('username')
            user_type = request.session.get('user_type')
            print(auth_user, "+++++++++")
            # Get or create the UserProfile for the logged-in user
            user_profile, created = UserProfile.objects.get_or_create(user=auth_user)
            print(user_profile)
            
            # Update profile fields
            auth_user.first_name = request.POST.get('first_name')
            auth_user.last_name = request.POST.get('last_name')           
            auth_user.email = request.POST.get('email')
            user_profile.contact = request.POST.get('contact')
            user_profile.about = request.POST.get('about')
            user_profile.save()
            # Update AuthLogin user information (if necessary)
            if request.POST.get('first_name'):
                auth_user.first_name = request.POST.get('first_name')
            if request.POST.get('last_name'):
                auth_user.last_name = request.POST.get('last_name')
            if request.POST.get('email'):
                auth_user.email = request.POST.get('email')
            
            auth_user.save()


            UserActivityLog.objects.create(
                user=auth_user,  # The user performing the action
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action='profile_update',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={'updated_fields': ['profile_pic', 'about', 'etc',]}
            )

        except Exception as e:
            print(e)
            messages.error(request, f" Updated Profile")
            
        return redirect('enroll:profile')
    return redirect('enroll:profile')


@check_auth
def profile_change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user_id = request.session.get('user_id')
        username = request.session.get('username')
        user_type = request.session.get('user_type')

        # Get current user from database
        try:
            auth_user = AuthLogin.objects.get(username=request.user.username)
            
            # Verify current password from database
            if not check_password(current_password, auth_user.password):
                messages.error(request, 'Current password is incorrect')

                # ✅ Log Failed Attempt
                UserActivityLog.objects.create(
                    user=auth_user,
                    user_name=username if username else "Session Missing",
                    user_type=user_type if user_type else "Session Missing",
                    action="password_change_attempt",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    details={"status": "failed", "reason": "incorrect_current_password"}
                )
                return redirect('enroll:profile_change_password')

            # Verify new passwords match
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match')

                UserActivityLog.objects.create(
                    user=auth_user,
                    user_name=username if username else "Session Missing",
                    user_type=user_type if user_type else "Session Missing",
                    action="password_change_attempt",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    details={"status": "failed", "reason": "password_mismatch"}
                )
                return redirect('enroll:profile_change_password')

            # Validate password strength
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long')
                # ✅ Log Failed Attempt
                UserActivityLog.objects.create(
                    user=auth_user,
                    user_name=username if username else "Session Missing",
                    user_type=user_type if user_type else "Session Missing",
                    action="password_change_attempt",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    details={"status": "failed", "reason": "weak_password"}
                )
                return redirect('enroll:profile_change_password')

            # Save new password to database
            auth_user.password = make_password(new_password)
            auth_user.save()

            # ✅ Log Successful Password Change
            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="password_change",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"status": "successful"}
            )
            messages.success(request, 'Password changed successfully! Please login with your new password.')
            return redirect('enroll:profile')
        except AuthLogin.DoesNotExist:
            messages.error(request, 'User not found')

            # ✅ Log User Not Found
            UserActivityLog.objects.create(
                user=None,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="password_change_attempt",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={"status": "failed", "reason": "user_not_found"}
            )
            return redirect('enroll:profile_change_password')


    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    return render(request, 'enroll/profile_change_password.html', {'user': request.user, 'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None ,  'fullname': full_name, 'email': auth_user.email})

        
    

@check_auth
def cms_create(request):
    print("+++++++++++++")
    if request.method == 'POST':
        page_name = request.POST.get('page_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        
    user_id = request.session.get('user_id')
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type 
    username = request.session.get('username')
    user_type = request.session.get('user_type')

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = []  
        
    try:
        # Clean the description HTML
        cleaned_description = clean_html_content(description) if description else ""
        
        # Create CMS Page
        cms_page = CMSPage.objects.create(
            page_name=page_name,
            slug=slug,
            description=cleaned_description,          
        )

        # Handle image uploads
        images = request.FILES.getlist('images') if 'images' in request.FILES else []
        captions = request.POST.getlist('captions[]') if 'captions[]' in request.POST else []
        
        for i, image in enumerate(images):
            caption = captions[i] if i < len(captions) else ''
            CMSImage.objects.create(
                cms_page=cms_page,
                image=image,
                caption=caption,
                order=i
            )
        
        # cms_page.save()
        
        messages.success(request, 'CMS Page created successfully!')
        return redirect('enroll:cms_list')
    
    except Exception as e:
        # ✅ Log Failed Attempt
        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="cms_page_create_attempt",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"status": "failed", "error": str(e)}
        )

        # messages.error(request, f'Error creating CMS Page: {str(e)}')
        

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    return render(request, 'enroll/cms/create.html', {'user': request.user, 'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None , 'fullname': full_name, 'email': auth_user.email, 'user_type': user_type, 'sidebar_items': sidebar_items, })



@check_auth
def cms_list(request): 

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = []

    search_query = request.GET.get('search', '')
    
    # Filter CMS pages based on search
    if search_query:
        cms_pages = CMSPage.objects.filter(
            Q(page_name__icontains=search_query) |
            Q(slug__icontains=search_query)
        )

        # ✅ Log Search Action
        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="cms_page_search",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"search_query": search_query, "result_count": cms_pages.count()}
        )


    else:
        cms_pages = CMSPage.objects.all()
         # ✅ Log Page Listing Access
        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="cms_page_list_view",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={"status": "viewed all pages", "total_pages": cms_pages.count()}
        )

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    context = {
        'cms_pages': cms_pages,
        'search_query': search_query,
        'user': request.user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None, 
        'fullname': full_name,
        'email': auth_user.email,
        'user_type': user_type,
        'sidebar_items': sidebar_items,
    }
    return render(request, 'enroll/cms/list.html', context)




@check_auth
def cms_edit(request, id):
    cms_page = get_object_or_404(CMSPage, id=id)
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_type = request.session.get('user_type')

    if user_type == 'Employee':
        sidebar_items = ['dashboard', 'cms']  # only dashboard and cms pages
    elif user_type == 'Admin':
        sidebar_items = ['dashboard', 'role_management', 'user_list', 'cms' ] 
    elif user_type == 'HR':
        sidebar_items = ['dashboard', 'user_list'] 
    else:
        sidebar_items = []  
        
    if request.method == 'POST':
        try:

            # ✅ Save old values for logging
            old_page_name = cms_page.page_name
            old_description = cms_page.description


            # Update CMS Page with cleaned description
            cms_page.page_name = request.POST.get('page_name')
            cms_page.description = clean_html_content(request.POST.get('description'))
            cms_page.save()


            # ✅ Log CMS Page Update
            UserActivityLog.objects.create(
                user=auth_user,
                user_name=username if username else "Session Missing",
                user_type=user_type if user_type else "Session Missing",
                action="cms_page_edit",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                details={
                    "cms_id": cms_page.id,
                    "old_page_name": old_page_name,
                    "new_page_name": cms_page.page_name,
                    "old_description": old_description[:100],  # Limit description length for logs
                    "new_description": cms_page.description[:100],
                }
            )
            
            # Handle existing image captions
            existing_captions = request.POST.dict()
            for key, value in existing_captions.items():
                if key.startswith('existing_captions[') and key.endswith(']'):
                    image_id = int(key[18:-1])  # Extract image ID from the field name
                    try:
                        image = CMSImage.objects.get(id=image_id, cms_page=cms_page)
                        old_caption = image.caption
                        image.caption = value
                        image.save()

                        # ✅ Log Image Caption Update
                        UserActivityLog.objects.create(
                            user=auth_user,
                            user_name=username if username else "Session Missing",
                            user_type=user_type if user_type else "Session Missing",
                            action="cms_image_caption_edit",
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT'),
                            details={
                                "image_id": image.id,
                                "old_caption": old_caption,
                                "new_caption": image.caption,
                            }
                        )

                    except CMSImage.DoesNotExist:
                        pass
            
            # Handle new image uploads
            images = request.FILES.getlist('images')
            captions = request.POST.getlist('captions[]')
            current_order = cms_page.images.count()
            
            for i, image in enumerate(images):
                caption = captions[i] if i < len(captions) else ''
                new_image = CMSImage.objects.create(
                    cms_page=cms_page,
                    image=image,
                    caption=caption,
                    order=current_order + i
                )

                # ✅ Log New Image Upload
                UserActivityLog.objects.create(
                    user=auth_user,
                    user_name=username if username else "Session Missing",
                    user_type=user_type if user_type else "Session Missing",
                    action="cms_image_upload",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    details={
                        "image_id": new_image.id,
                        "caption": caption,
                        "cms_id": cms_page.id
                    }
                )

            
            messages.success(request, 'CMS Page updated successfully!')
            return redirect('enroll:cms_list')
        except Exception as e:
            messages.error(request, f'Error updating CMS Page: {str(e)}')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    return render(request, 'enroll/cms/edit.html', {'cms_page': cms_page, 'user': request.user, 'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None , 'fullname': full_name, 'user_type': user_type, 'sidebar_items': sidebar_items, })


@check_auth
@require_http_methods(["POST"])
def cms_delete(request, id):
    try:
        print(f"Received request to delete CMS with ID: {id}")  # Debugging log
        auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
        user_id = request.session.get('user_id')
        username = request.session.get('username')
        user_type = request.session.get('user_type')
        
        cms_page = get_object_or_404(CMSPage, id=id)
        print(f"Found CMS page: {cms_page.page_name}")  # Debugging log
        page_name = cms_page.page_name
        cms_page.delete()
        print(id)
        # CMSPage.objects.get(pk=id).delete()
        print(f"CMS page deleted successfully.")  # Debugging log

        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="cms_page_delete",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={
                "cms_id": id,
                "deleted_page_name": page_name
            }
        )
        return JsonResponse({
            'success': True,
            'message': f'CMS page "{"page_name"}" has been deleted successfully.'
        })
    except CMSPage.DoesNotExist:
        print(f"CMS page with ID {id} does not exist.")  # Debugging log
        return JsonResponse({
            'success': False,
            'message': 'CMS page not found.'
        }, status=404)
    except Exception as e:
        print(f"Error deleting CMS page: {str(e)}")  # Debugging log
        return JsonResponse({
            'success': False,
            'message': f'Error deleting CMS page: {str(e)}'
        }, status=500)


@check_auth
@require_http_methods(["POST"])
def delete_cms_image(request, image_id):
    try:
        auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))  # Get the logged-in user
        user_id = request.session.get('user_id')
        username = request.session.get('username')
        user_type = request.session.get('user_type')
        image = CMSImage.objects.get(id=image_id)
        cms_page = image.cms_page 
        image.delete()

        # ✅ Log Image Deletion
        UserActivityLog.objects.create(
            user=auth_user,
            user_name=username if username else "Session Missing",
            user_type=user_type if user_type else "Session Missing",
            action="cms_image_delete",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            details={
                "image_id": image_id,
                "cms_id": cms_page.id,
                "cms_page_name": cms_page.page_name
            }
        )
        return JsonResponse({'success': True})
    except CMSImage.DoesNotExist:
        user_id = request.session.get('user_id')
        username = request.session.get('username')
        user_type = request.session.get('user_type')
        return JsonResponse({'success': False, 'error': 'Image not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# @check_auth
def change_password(request):
    if request.method == 'POST':
        try:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate current password
            if not request.user.check_password(old_password):
                return JsonResponse({
                    'success': False,
                    'error': 'Current password is incorrect'
                })
            
            # Validate new passwords match
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'error': 'New passwords do not match'
                })
            
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            
            # Update session to prevent logout
            update_session_auth_hash(request, request.user)
            
            return JsonResponse({
                'success': True,
                'message': 'Password changed successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    return render(request, 'enroll/change_password.html', { 'user': request.user, 'profile_pic': user_profile.profile_pic.url, 'fullname': full_name})



def get_states(request):
    try:
        states = State.objects.all().values('id', 'name').order_by('name')
        print("States fetched:", list(states))  # Debug print
        return JsonResponse({'states': list(states)})
    except Exception as e:
        print("Error fetching states:", str(e))  # Debug print
        return JsonResponse({'error': str(e)}, status=400)

def get_cities(request):
    state_id = request.GET.get('state_id')
    print(f"Fetching cities for state ID: {state_id}")
    
    if not state_id:
        return JsonResponse({'cities': []})
        
    try:
        # Convert state_id to integer
        state_id = int(state_id)
        state = State.objects.get(id=state_id)
        cities = City.objects.filter(state=state).order_by('name')
        
        city_list = []
        for city in cities:
            city_list.append({
                'id': city.id,
                'name': city.name
            })
        
        print(f"Found {len(city_list)} cities for state {state.name}")
        return JsonResponse({'cities': city_list})
        
    except (ValueError, TypeError):
        print(f"Invalid state ID format: {state_id}")
        return JsonResponse({'error': 'Invalid state ID format'}, status=400)
    except State.DoesNotExist:
        print(f"State not found with ID: {state_id}")
        return JsonResponse({'error': 'State not found'}, status=404)
    except Exception as e:
        print(f"Error fetching cities: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)

def get_cities_by_state(request, state_id):
    try:
        # Get state by name (state_id is actually the state name)
        state = State.objects.get(name=state_id)
        cities = City.objects.filter(state=state).values('name').order_by('name')
        return JsonResponse({'cities': list(cities)})
    except State.DoesNotExist:
        return JsonResponse({'error': f'State not found: {state_id}'}, status=404)
    except Exception as e:
        print(f"Error fetching cities: {str(e)}")  # Debug print
        return JsonResponse({'error': str(e)}, status=400)

def get_all_states(request):
    try:
        states = State.objects.all().values('id', 'name').order_by('name')
        return JsonResponse({'states': list(states)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_cities_by_state(request):
    state_id = request.GET.get('state_id')
    if not state_id:
        return JsonResponse({'cities': []})
    
    try:
        cities = City.objects.filter(state_id=state_id).values('id', 'name').order_by('name')
        return JsonResponse({'cities': list(cities)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


# <-- ============================================================== -->
#  Banner management
# <-- ============================================================== -->


@check_auth
def banner_list(request):
    banners = Banner.objects.prefetch_related('images').all()
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_type = request.session.get('user_type')

    search_query = request.GET.get('search', '')
    
    if search_query:
        users = Banner.objects.filter(
            Q(fullname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(contact__icontains=search_query)
        )

        if not users.exists():
            messages.warning(request, 'User not available')
            return redirect('enroll:banner_list')
    else:
        users = Banner.objects.all().order_by('title') 
        
    paginator = Paginator(users, 10)  
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number) 
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    
    context= {
        'banners': banners,
        'page_obj': page_obj, 
        'user': request.user, 
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None ,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': user_type,

    }
    return render(request, 'enroll/banner/banner_list.html', context)


@check_auth
def view_banner(request, banner_id):
    banner = get_object_or_404(Banner, id=banner_id)
    images = BannerImage.objects.filter(banner=banner)
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    
    context= {
        'banner': banner,
        'user': request.user, 
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None ,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': user_type,
        'images': images

    }
    return render(request, 'enroll/banner/view_banner.html', context)



@check_auth
def add_banner(request):

    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = auth_user.user_type
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    

    if request.method == 'POST':
        title = request.POST.get('title')
        images = request.FILES.getlist('images')
        content = request.POST.get('content')
        captions = request.POST.getlist('captions[]')
        links = request.POST.getlist('links[]')
        print(title, images, content, links)

        # Save banner
        banner = Banner.objects.create(title=title, content=content)

        for img, cap, link in zip_longest(images, captions, links, fillvalue=""):  
            BannerImage.objects.create(banner=banner, images=img, caption=cap, link=link)


        messages.success(request, "banner added successfully")
        return redirect('enroll:banner_list')
    
    context= {
        
        'user': request.user, 
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None ,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': user_type,
        
    }
    
    return render(request, 'enroll/banner/add_banner.html', context)



@check_auth

def edit_banner(request, banner_id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    banner = get_object_or_404(Banner, id=banner_id)
    images = BannerImage.objects.filter(banner=banner)  # Fetch existing images

    if request.method == "POST":                        
        # Handle image deletion
        delete_image_ids = request.POST.getlist('delete_images[]')
        delete_image_ids = [int(i) for i in delete_image_ids if i.strip().isdigit()]

        if delete_image_ids:  
            BannerImage.objects.filter(id__in=delete_image_ids).delete()

        existing_images = request.POST.getlist("existing_images[]")
        captions = request.POST.getlist("captions[]")
        links = request.POST.getlist("links[]")

        for img_id, cap, img_link in zip_longest(existing_images, captions, links, fillvalue=""):
            if img_id:
                image = BannerImage.objects.filter(id=img_id).first()
                if image:
                    image.caption = cap
                    image.link = img_link
                    image.save()

        title = request.POST.get("title")
        content = request.POST.get("content")
        link = request.POST.get("link")
        new_images = request.FILES.getlist("images")

        # Update Banner details
        banner.title = title
        banner.content = content
        banner.link = link
        banner.save()

        # Update or add images
        for img, cap, img_link in zip_longest(new_images, captions[len(existing_images):], links[len(existing_images):], fillvalue=""):
            if img:  
                BannerImage.objects.create(banner=banner, images=img, caption=cap, link=img_link)

            else:
                existing_images = [img_id for img_id in request.POST.getlist("existing_images[]") if img_id.strip().isdigit()]

                if existing_images:
                    existing_images.caption = cap
                    existing_images.link = img_link
                    existing_images.save()

        messages.success(request, "Banner updated successfully!")
        return redirect("enroll:banner_list")

    context = {
        'user': request.user, 
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': user_type,
        "banner": banner,
        "images": images
    }

    return render(request, "enroll/banner/edit_banner.html", context)

@check_auth
def delete_banner_image(request):
    if request.method == "POST":
        image_id = request.POST.get("image_id")
        try:
            image = get_object_or_404(BannerImage, id=image_id)
            image.delete()
            return JsonResponse({"status": "success"})
        except:
            return JsonResponse({"status": "error"})
    return JsonResponse({"status": "invalid request"})



from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def delete_banner(request, banner_id):
    if request.method == "DELETE":
        banner = get_object_or_404(Banner, id=banner_id)
        banner.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

def get_banner_images(request, banner_id):
    banner_images = BannerImage.objects.filter(banner_id=banner_id)
    images_data = [
        {
            "id": img.id,
            "image_url": img.images.url,  # Image field ka correct naam use karein
            "caption": img.caption,
            "link": img.link
        }
        for img in banner_images
    ]
    return JsonResponse({"images": images_data})




@check_auth
def vendor_list(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('enroll:user_login')  
    
    try:
        auth_user = AuthLogin.objects.get(id=user_id)
    except AuthLogin.DoesNotExist:
        return redirect('enroll:user_login') 

    # All vendors (Approved + Pending)
    all_vendors = VendorProfile.objects.all()

    # Vendors waiting for approval
    pending_vendors = VendorProfile.objects.filter(is_approved=False)

    # Vendors whose personal profile is approved but business profile is pending
    pending_profiles = VendorProfile.objects.filter(is_approved=True, is_profile_approved=False)

    # User Profile
    user_profile, created = UserProfile.objects.get_or_create(user=auth_user)  
    full_name = auth_user.fullname.strip() if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"

    search_query = request.GET.get('search', '')
    
    if search_query:
        products = Product.objects.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(category__icontains=search_query) 
          
        )

    # Pagination Logic
    paginator = Paginator(products, 10)  # 10 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    
    context = {
        'vendors': all_vendors,  # Show all vendors
        'user': auth_user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': auth_user.user_type,
        'pending_vendors': pending_vendors,
        'pending_profiles': pending_profiles,
        'serch_query': search_query,
        'page_obj': page_obj,
    }
    
    return render(request, 'enroll/vendor/vendor_list.html', context)


@check_auth
def approve_vendor_login(request, vendor_id):
    vendor = VendorProfile.objects.get(id=vendor_id)
    vendor.is_login_approved = True
    vendor.status = "approved"
    vendor.save()
    
    try:
        send_mail(
            'Your Vendor Account is Approved',
            f'Congratulations {vendor.full_name}, your vendor account has been approved! You can now log in.',
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )
    except Exception as e:
        print('Error:', e)

    messages.success(request, f'Vendor "{vendor.full_name}" login has been approved.')
    return redirect('enroll:vendor_login_approval')


@check_auth
def approve_vendor_profile(request, vendor_id):
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    business_profile = VendorBusinessProfile.objects.filter(vendor=vendor).first()

    if not business_profile:
        messages.error(request, "Vendor's business profile does not exist.")
        return redirect("enroll:vendor_list")
   
    if vendor.is_profile_submitted:  # Check if vendor has submitted their profile
        vendor.is_profile_approved = True
        vendor.is_profile_rejected = False  
        vendor.is_profile_submitted = False  # Reset submitted status
        vendor.status = "approved"
        vendor.save()

        send_mail(
            'Your Vendor Profile is Approved',
            f'Hello {vendor.full_name}, your business profile has been approved! You can now access your dashboard.',
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=False,
        )

        messages.success(request, f"Vendor {vendor.full_name}'s business profile has been approved!")
    else:
        messages.warning(request, "Vendor has not submitted their profile yet.")
    
    return redirect('enroll:vendor_profile_approval')



@check_auth
def reject_vendor(request, vendor_id):
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    if request.method == "POST":
        rejection_reason = request.POST.get("rejection_reason", "")

    
    vendor.is_profile_rejected = True
    vendor.is_profile_approved = False
    vendor.status = "Rejected"

    business_profile = VendorBusinessProfile.objects.filter(vendor=vendor).first()
    if business_profile:
        business_profile.rejection_reason = rejection_reason
        business_profile.save()
   
    vendor.save()

    messages.success(request, f"Vendor {vendor.full_name} has been rejected.")
    return redirect('enroll:vendor_login_approval')



@check_auth
def reject_vendor_profile(request, vendor_id):
    vendor = get_object_or_404(VendorProfile, id=vendor_id)

    if request.method == "POST":
        rejection_reason = request.POST.get("rejection_reason", "")
        vendor.rejection_reason = rejection_reason

    
    vendor.is_profile_approved = False
    vendor.is_profile_rejected = True
    vendor.is_profile_submitted = False
    vendor.status = "rejected"
    vendor.save()


    send_mail(
        'Your Vendor Profile is Rejected',
        f'Sorry {vendor.full_name}, your business profile has been rejected.  Reason: {rejection_reason}. ',
        settings.DEFAULT_FROM_EMAIL,
        [vendor.email],
        fail_silently=False,
    )

    messages.warning(request, f"Your profile was rejected. Reason: {rejection_reason}")
    return redirect('enroll:vendor_profile_approval')




@check_auth
def vendor_business_detail(request, vendor_id):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    business_profile = get_object_or_404(VendorBusinessProfile, vendor=vendor)

    is_profile_complete = vendor.is_profile_completed

    context = {
        'vendor': vendor,  # Show all vendors
        'user': auth_user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': auth_user.user_type,
        "business_profile": business_profile, 
        "is_profile_complete": is_profile_complete,
        "MEDIA_URL": settings.MEDIA_URL
        }

  
    return render(request, "enroll/vendor_business_detail.html", context)


    
@check_auth
def vendor_login_approval(request):
    vendors = VendorProfile.objects.filter(is_login_approved=False)
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"


    context = {
        'vendors': vendors,  # Show all vendors
        'user': auth_user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': auth_user.user_type,
    }
    return render(request, "enroll/vendor/vendor_login_approval.html", context)

    

@check_auth
def vendor_profile_approval(request):
    business_profiles = VendorBusinessProfile.objects.filter(vendor__is_profile_completed=True, vendor__is_profile_submitted=True, vendor__is_profile_approved=False)
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    

    context = {
        "business_profiles": business_profiles,
        'user': auth_user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': auth_user.user_type,
    }
    return render(request, "enroll/vendor/vendor_profile_approval.html", context)


#===========================#
#Products
#============#

@check_auth
def vendor_product_approval(request):
    auth_user = get_object_or_404(AuthLogin, id=request.session.get('user_id'))
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    products = Product.objects.select_related('vendor').all().order_by("-id")

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        product = Product.objects.get(id=product_id)
        if action == 'approve':
            product.status = 'approved'
            product.is_approved = True
        elif action == 'reject':
            product.status = 'rejected'
            product.is_approved = False
        product.save()
        messages.success(request, f"Product '{product.name}' has been {action}d.")

    search_query = request.GET.get('search', '')
    
    if search_query:
        products = Product.objects.filter(
            Q(product_name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__category_name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        )

    paginator = Paginator(products, 10)  
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
       
        'user': auth_user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': auth_user.user_type,
        # 'products': products,
        'search_query': search_query,
        'page_obj': page_obj, 
        'products': page_obj.object_list,
        
    }

    return render(request, 'enroll/vendor/vendor_product_approval.html', context)



@check_auth
def approve_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.status = 'approved'
    product.admin_message = request.POST.get('reason') or 'Product approved.'
    product.is_approved = True
    product.save()
    messages.success(request, f"Product '{product.product_name}' has been approved.")
    return redirect("enroll:vendor_product_approval")

@check_auth
def reject_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.status = 'rejected'
    product.is_approved = False
    product.save()
    messages.warning(request, f"Product '{product.product_name}'  has been rejected.")
    return redirect("enroll:vendor_product_approval")




@check_auth
def view_product_detail(request, product_id):
    
    user_type = request.session.get('user_type')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user) 
    auth_user = get_object_or_404(AuthLogin, username=request.user.username)
    full_name = auth_user.fullname if auth_user.fullname.strip() else f"{auth_user.first_name} {auth_user.last_name}"
    vendor_id = request.session.get('vendor_id')
    product = get_object_or_404(Product, id=product_id)
    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    specifications = product.get_specifications() 

    print(specifications, "++++++++")
    
    context = {
        'user': auth_user,
        'profile_pic': user_profile.profile_pic.url if user_profile.profile_pic else None,
        'fullname': full_name, 
        'email': auth_user.email,
        'user_type': auth_user.user_type,
        'product': product,
        'specifications': specifications,
        'vendor': vendor,
       
    }
    return render(request, 'enroll/vendor/view_product_detail.html', context)
