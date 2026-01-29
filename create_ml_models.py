"""
Create placeholder ML models for development/testing.
These are simple models that work but need to be replaced with trained models for production.

Requirements:
- tensorflow >= 2.10.0
- numpy

Install: pip install tensorflow numpy
"""
import os
import sys
from pathlib import Path

# Check if tensorflow is available
try:
    import tensorflow as tf
    import numpy as np
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow not installed.")
    print("Install with: pip install tensorflow numpy")
    print("\nFor now, ML will use mock mode.")
    sys.exit(1)

# Create models directory
models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

print("Creating placeholder ML models...")

# ============================================================================
# NBO Model (Next Best Offer)
# ============================================================================
print("\n1. Creating NBO model...")

# Simple neural network for NBO prediction
# Input: 10 features, Output: 8 offer probabilities
nbo_model = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(10,)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(8, activation='softmax')  # 8 offers
])

nbo_model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Train with dummy data that creates patterns (so model learns to differentiate)
# Create patterns: high revenue -> offer 3, medium -> offer 0, low -> offer 7
dummy_X = np.random.rand(1000, 10).astype(np.float32)
dummy_y = np.zeros((1000, 8), dtype=np.float32)

# Create patterns based on features to make model learn differentiation
for i in range(1000):
    revenue = dummy_X[i][0]  # First feature as revenue proxy
    if revenue > 0.7:  # High revenue
        dummy_y[i][3] = 0.4  # Offer 3
        dummy_y[i][4] = 0.3
        dummy_y[i][2] = 0.2
        dummy_y[i][0] = 0.1
    elif revenue > 0.4:  # Medium revenue
        dummy_y[i][0] = 0.35  # Offer 0
        dummy_y[i][1] = 0.25
        dummy_y[i][2] = 0.2
        dummy_y[i][5] = 0.2
    else:  # Low revenue
        dummy_y[i][7] = 0.4  # Offer 7
        dummy_y[i][6] = 0.3
        dummy_y[i][5] = 0.2
        dummy_y[i][4] = 0.1
    
    # Normalize
    dummy_y[i] = dummy_y[i] / dummy_y[i].sum()

nbo_model.fit(dummy_X, dummy_y, epochs=50, verbose=0, batch_size=32)

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(nbo_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
nbo_tflite = converter.convert()

# Save
with open(models_dir / 'nbo.tflite', 'wb') as f:
    f.write(nbo_tflite)

print(f"✅ NBO model saved to {models_dir / 'nbo.tflite'}")

# ============================================================================
# Churn Model
# ============================================================================
print("\n2. Creating Churn model...")

# Simple neural network for churn prediction
# Input: 10 features, Output: churn probability (0-1)
churn_model = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(10,)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')  # Binary classification
])

churn_model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Train with dummy data that creates patterns
# Pattern: low revenue + high days_since_last -> high churn
dummy_X = np.random.rand(1000, 10).astype(np.float32)
dummy_y = np.zeros((1000, 1), dtype=np.float32)

# Create patterns: customers with low revenue and high inactivity -> churn
for i in range(1000):
    revenue = dummy_X[i][0]  # First feature as revenue proxy
    inactivity = dummy_X[i][2] if dummy_X.shape[1] > 2 else dummy_X[i][1]  # Third feature as inactivity proxy
    
    # Higher churn for low revenue + high inactivity
    churn_prob = (1.0 - revenue) * 0.6 + inactivity * 0.4
    churn_prob = np.clip(churn_prob, 0.0, 1.0)
    dummy_y[i][0] = churn_prob

churn_model.fit(dummy_X, dummy_y, epochs=50, verbose=0, batch_size=32)

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(churn_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
churn_tflite = converter.convert()

# Save
with open(models_dir / 'churn.tflite', 'wb') as f:
    f.write(churn_tflite)

print(f"✅ Churn model saved to {models_dir / 'churn.tflite'}")

print("\n" + "="*60)
print("✅ ML Models Created Successfully!")
print("="*60)
print("\n⚠️  IMPORTANT:")
print("These are placeholder models trained on dummy data.")
print("For production accuracy, train on your real DWH data:")
print()
print("📚 TRAINING GUIDE:")
print("   1. See ML_TRAINING_STEP_BY_STEP.md for complete guide")
print("   2. Run: python train_models_from_dwh.py")
print("   3. Script will:")
print("      - Connect to your DWH")
print("      - Extract historical customer data")
print("      - Train models on your real data")
print("      - Save trained models to models/ directory")
print()
print("🔧 PREREQUISITES:")
print("   - DWH connection configured in settings.py")
print("   - Historical data in DWH (features + labels)")
print("   - ML_FEATURE_MAPPING configured")
print()
print("For now, these placeholder models will work but predictions")
print("may not be accurate. Train on your data for best results!")
print("="*60)

