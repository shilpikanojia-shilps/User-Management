# SIDEBAR_PERMISSIONS = {
#     "Manage Role": ["add_manage_role", "edit_manage_role", "delete_manage_role"],
#     "Manage Sub-Admins": ["add_manage_sub_admins", "edit_manage_sub_admins", "delete_manage_sub_admins"],
#     "User Management": ["add_user_management", "edit_user_management", "delete_user_management"],
#     "CMS Pages": ["add_cms_pages", "edit_cms_pages", "delete_cms_pages"],
# }


from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from enroll.models import Role  # Make sure to import your Role model

# Manually Defining Permissions
SIDEBAR_PERMISSIONS = [
    ("add_user", "Can add user"),
    ("edit_user", "Can edit user"),
    ("delete_user", "Can delete user"),
    ("view_user", "Can view user"),
    ("add_cms", "Can add CMS"),
    ("edit_cms", "Can edit CMS"),
    ("delete_cms", "Can delete CMS"),
    ("view_cms", "Can view CMS"),
    ("add_role", "Can add role"),
    ("edit_role", "Can edit role"),
    ("delete_role", "Can delete role"),
    ("view_role", "Can view role"),
]

# Assigning Permissions
for codename, name in SIDEBAR_PERMISSIONS:
    perm, created = Permission.objects.get_or_create(
        codename=codename,
        name=name,
        content_type=ContentType.objects.get(model="role")  # Adjust according to your app
    )
    print(f"Permission Created: {name}")

print("All Permissions Created!")
