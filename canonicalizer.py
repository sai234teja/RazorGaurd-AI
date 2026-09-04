import pandas as pd
from schema_adapter import find_mapping


# Load the incoming dataset
file_path = "datasets/sample2.csv"

df = pd.read_csv(file_path)


# Get the schema mapping
mapping = find_mapping(df.columns)


# Create a new canonical dataset
canonical_df = pd.DataFrame()


# Apply the mapping
for canonical_field, details in mapping.items():

    source_column = details["source_column"]

    canonical_df[canonical_field] = df[source_column]


# Display result
print("=" * 60)
print("       RAZORGUARD AI - CANONICAL DATASET")
print("=" * 60)

print("\nOriginal Columns")
print("-" * 60)

print(list(df.columns))


print("\nCanonical RazorGuard Columns")
print("-" * 60)

print(list(canonical_df.columns))


print("\nCanonical Dataset")
print("-" * 60)

print(canonical_df)


print("\n" + "=" * 60)
print("Canonicalization completed!")
print("=" * 60)