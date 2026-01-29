"""
Temporary script to check what models exist
"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

# Try to import models
try:
    from loyalty.models import *
    print("Models in loyalty.models:")
    import loyalty.models as models_module
    for name in dir(models_module):
        if not name.startswith('_') and hasattr(getattr(models_module, name), '_meta'):
            print(f"  - {name}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

