#!/usr/bin/env python
"""Test offset-based pagination"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client
import requests

client = get_xiva_client()
headers = client._get_headers()
url = f"{client.base_url}/customerManagement/v4/customer/"

# Test offset
print("Testing offset parameter...")
params = {'ordering': '-creationDate', 'offset': '50'}
response = requests.get(url, headers=headers, params=params, timeout=client.timeout)
data = response.json()

if isinstance(data, list):
    print(f"Offset 50: Got {len(data)} results")
    if len(data) > 0:
        print(f"First result: {data[0].get('name', 'N/A')}")

