"""
Script to create a Django superuser non-interactively
Run: python create_user.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from django.contrib.auth.models import User

# User credentials
USERNAME = 'admin'
EMAIL = 'admin@khaywe.com'
PASSWORD = 'admin123'  # Change this in production!

# Check if user already exists
if User.objects.filter(username=USERNAME).exists():
    print(f"User '{USERNAME}' already exists. Updating password...")
    user = User.objects.get(username=USERNAME)
    user.set_password(PASSWORD)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"[OK] User '{USERNAME}' password updated!")
else:
    # Create new superuser
    user = User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD
    )
    print(f"[OK] Superuser '{USERNAME}' created successfully!")

print(f"\nLogin credentials:")
print(f"  Username: {USERNAME}")
print(f"  Password: {PASSWORD}")
print(f"\n[WARNING] Remember to change the password in production!")

