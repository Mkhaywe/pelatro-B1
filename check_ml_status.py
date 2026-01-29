"""
Check ML Service Status
Run this to see why mock mode might be enabled
"""
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from django.conf import settings
from loyalty.ml.inference import MOCK_ML_ENABLED, TENSORFLOW_AVAILABLE, NUMPY_AVAILABLE

print("="*70)
print("ML SERVICE STATUS CHECK")
print("="*70)
print()

# Check settings
print("1. SETTINGS:")
print(f"   ML_MOCK_MODE (from settings): {getattr(settings, 'ML_MOCK_MODE', 'NOT SET')}")
print(f"   ML_MOCK_MODE (env var): {os.environ.get('ML_MOCK_MODE', 'NOT SET')}")
print(f"   MOCK_ML_ENABLED (runtime): {MOCK_ML_ENABLED}")
print()

# Check libraries
print("2. LIBRARIES:")
print(f"   TensorFlow Available: {TENSORFLOW_AVAILABLE}")
print(f"   NumPy Available: {NUMPY_AVAILABLE}")
print()

if TENSORFLOW_AVAILABLE:
    try:
        import tensorflow as tf
        print(f"   TensorFlow Version: {tf.__version__}")
    except Exception as e:
        print(f"   TensorFlow Import Error: {e}")

if NUMPY_AVAILABLE:
    try:
        import numpy as np
        print(f"   NumPy Version: {np.__version__}")
    except Exception as e:
        print(f"   NumPy Import Error: {e}")
print()

# Check models
print("3. MODEL FILES:")
from pathlib import Path
models_dir = Path('models')
nbo_model = models_dir / 'nbo.tflite'
churn_model = models_dir / 'churn.tflite'

print(f"   NBO Model: {'EXISTS' if nbo_model.exists() else 'MISSING'} ({nbo_model})")
print(f"   Churn Model: {'EXISTS' if churn_model.exists() else 'MISSING'} ({churn_model})")
print()

# Check ML service initialization
print("4. ML SERVICE INITIALIZATION:")
try:
    from loyalty.ml.inference import MLInferenceService
    ml_service = MLInferenceService()
    print(f"   Service initialized: OK")
    print(f"   Models loaded: {list(ml_service.models.keys())}")
    if not ml_service.models:
        print("   WARNING: No models loaded - check model files and TensorFlow availability")
except Exception as e:
    print(f"   Service initialization error: {e}")
    import traceback
    traceback.print_exc()
print()

# Summary
print("="*70)
print("SUMMARY:")
print("="*70)
if MOCK_ML_ENABLED:
    print("*** MOCK MODE IS ENABLED ***")
    print("   Reason: ML_MOCK_MODE is set to True")
    print("   Solution: Set ML_MOCK_MODE=False in settings.py or environment")
    print("   Or unset environment variable: $env:ML_MOCK_MODE='' (PowerShell)")
elif not TENSORFLOW_AVAILABLE or not NUMPY_AVAILABLE:
    print("*** MOCK MODE WILL BE USED (Libraries not available) ***")
    if not TENSORFLOW_AVAILABLE:
        print("   Reason: TensorFlow not available")
    if not NUMPY_AVAILABLE:
        print("   Reason: NumPy not available")
    print("   Solution: Install with: pip install tensorflow numpy")
    print("   NOTE: Make sure Django server is using venv Python, not system Python")
else:
    print("*** REAL ML MODE SHOULD BE ACTIVE ***")
    print("   TensorFlow: OK")
    print("   NumPy: OK")
    print("   Mock Mode: Disabled")
    print("   Models: Check above if loaded")
print("="*70)

