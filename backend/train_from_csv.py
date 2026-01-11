#!/usr/bin/env python
"""Test CSV dataset training"""
from random_forest_fraud import load_voting_fraud_dataset, initialize_rf_service

print("Loading dataset...")
records = load_voting_fraud_dataset()
print(f"✓ Loaded {len(records)} records")

print("\nInitializing RF service...")
rf_service = initialize_rf_service()

print("\nTraining model...")
metrics = rf_service.train_and_save(records)

print(f"\n✓ Model trained!")
print(f"  ROC AUC: {metrics['roc_auc']:.4f}")
print(f"  PR AUC: {metrics['pr_auc']:.4f}")
print(f"  Training samples: {metrics['n_train']}")
print(f"  Test samples: {metrics['n_test']}")
