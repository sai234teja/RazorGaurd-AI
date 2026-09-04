import pandas as pd
import re

# Our fixed RazorGuard schema
CANONICAL_FIELDS = {
    "transaction_id": [
        "transaction_id", "transactionid", "txn_id", "txn", "id"
    ],
    "timestamp": [
        "timestamp", "time", "datetime", "date", "created_at", "transaction_time"
    ],
    "amount": [
        "amount", "transaction_amount", "transaction_amt",
        "total_amount", "total_value", "value"
    ],
    "customer_id": [
        "customer_id", "customer", "user", "user_id",
        "customer_code", "user_code"
    ],
    "merchant_id": [
        "merchant_id", "merchant", "merchant_code", "shop_id"
    ],
    "payment_method": [
        "payment_method", "payment_type", "payment_mode", "method"
    ],
    "device_id": [
        "device_id", "device", "device_code"
    ],
    "location": [
        "location", "city", "country", "region"
    ],
    "status": [
        "status", "result", "transaction_status"
    ],
    "fraud_label": [
        "fraud_label", "fraud", "is_fraud", "isfraud",
        "fraud_flag", "class"
    ]
}


def normalize_name(name):
    """Make column names easier to compare."""
    name = str(name).lower().strip()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def find_mapping(columns):
    """Find the best simple mapping from dataset columns to RazorGuard fields."""

    mapping = {}

    normalized_columns = {
        normalize_name(column): column
        for column in columns
    }

    for canonical_field, possible_names in CANONICAL_FIELDS.items():

        for possible_name in possible_names:

            normalized_possible = normalize_name(possible_name)

            if normalized_possible in normalized_columns:
                original_column = normalized_columns[normalized_possible]

                mapping[canonical_field] = {
                    "source_column": original_column,
                    "confidence": 1.0
                }

                break

    return mapping


# --------------------------------------------------
# Test with sample2.csv
# --------------------------------------------------

file_path = "datasets/sample2.csv"

df = pd.read_csv(file_path)

mapping = find_mapping(df.columns)

print("=" * 60)
print("          RAZORGUARD AI - SCHEMA ADAPTER")
print("=" * 60)

print("\nIncoming Dataset Columns")
print("-" * 60)

for column in df.columns:
    print(column)

print("\nRazorGuard Schema Mapping")
print("-" * 60)

for canonical_field in CANONICAL_FIELDS:

    if canonical_field in mapping:

        source = mapping[canonical_field]["source_column"]
        confidence = mapping[canonical_field]["confidence"]

        print(
            f"{source:<20} -> "
            f"{canonical_field:<20} "
            f"Confidence: {confidence:.0%}"
        )

    else:
        print(
            f"{'NOT FOUND':<20} -> "
            f"{canonical_field:<20} "
            f"Confidence: 0%"
        )

print("\n" + "=" * 60)
print("Schema mapping completed!")
print("=" * 60)