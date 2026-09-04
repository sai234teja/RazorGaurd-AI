import pandas as pd

# Load the dataset
file_path = "datasets/sample.csv"

df = pd.read_csv(file_path)

print("=" * 50)
print("        RAZORGUARD AI - DATASET PROFILER")
print("=" * 50)

# Basic information
print("\nDataset Information")
print("-" * 50)
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

# Column information
print("\nColumn Analysis")
print("-" * 50)

for column in df.columns:
    print(f"\nColumn: {column}")
    print("Data Type:", df[column].dtype)
    print("Missing Values:", df[column].isnull().sum())
    print("Unique Values:", df[column].nunique())

# Display first 5 rows
print("\nFirst 5 Transactions")
print("-" * 50)
print(df.head())

print("\n" + "=" * 50)
print("Dataset profiling completed!")
print("=" * 50)