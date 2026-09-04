import csv
import json
from pathlib import Path


OUTPUT_FILE = Path("catalog/products_universal.csv")


products = []


def add_product(
    product_id,
    name,
    category,
    subcategory,
    brand,
    price,
    description,
    rating,
    stock,
    attributes,
    use_cases
):
    products.append({
        "product_id": product_id,
        "name": name,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "price": price,
        "currency": "INR",
        "description": description,
        "rating": rating,
        "stock": stock,
        "attributes": json.dumps(attributes, separators=(",", ":")),
        "use_cases": json.dumps(use_cases, separators=(",", ":"))
    })


# ============================================================
# ELECTRONICS
# ============================================================

headphones = [
    ("SoundMax Air Pro", 2499, 4.5, 25, 40, True, "excellent"),
    ("QuietRide ANC", 2999, 4.7, 12, 35, True, "excellent"),
    ("BeatFlow Lite", 1799, 4.2, 40, 30, False, "good"),
    ("TravelPods Max", 2699, 4.5, 20, 45, True, "good"),
    ("ClearTalk Air", 1999, 4.3, 35, 29, False, "excellent"),
]

for i, item in enumerate(headphones, 1):
    name, price, rating, stock, battery, anc, mic = item

    add_product(
        f"HP{i:03d}",
        name,
        "Electronics",
        "Headphones",
        "AudioTech",
        price,
        f"Wireless headphones designed for everyday listening and communication.",
        rating,
        stock,
        {
            "battery_hours": battery,
            "noise_cancellation": anc,
            "microphone_quality": mic,
            "wireless": True
        },
        ["music", "travel", "online classes"]
    )


smartphones = [
    ("Nova X5", 18999, 4.4, 30, 5000, 50, 8, 128),
    ("PixelWave Pro", 22999, 4.6, 18, 5200, 48, 12, 256),
    ("CorePhone Lite", 14999, 4.2, 45, 5000, 42, 6, 128),
    ("VisionMax 5G", 27999, 4.7, 15, 5100, 50, 12, 256),
    ("SmartOne S", 19999, 4.3, 28, 5000, 108, 8, 128),
]

for i, item in enumerate(smartphones, 1):

    name, price, rating, stock, battery_mah, camera, ram, storage = item

    add_product(
        f"PH{i:03d}",
        name,
        "Electronics",
        "Smartphones",
        "TechNova",
        price,
        "5G smartphone with modern performance, camera and long battery life.",
        rating,
        stock,
        {
            "battery_mah": battery_mah,
            "camera_mp": camera,
            "ram_gb": ram,
            "storage_gb": storage,
            "5g": True
        },
        ["photography", "gaming", "daily use", "social media"]
    )


laptops = [
    ("CodeBook 14", 54999, 4.5, 12, 16, 512, "Core i5", 10),
    ("DevPro 15", 64999, 4.7, 8, 16, 512, "Core i7", 12),
    ("StudentBook Air", 42999, 4.3, 20, 8, 512, "Core i5", 11),
    ("GameStation 15", 74999, 4.6, 7, 16, 1024, "Ryzen 7", 8),
    ("UltraWork 14", 59999, 4.4, 14, 16, 512, "Ryzen 5", 13),
]

for i, item in enumerate(laptops, 1):
    name, price, rating, stock, ram, storage, processor, battery = item

    add_product(
        f"LP{i:03d}",
        name,
        "Electronics",
        "Laptops",
        "ComputeX",
        price,
        "Laptop designed for productivity, development and everyday computing.",
        rating,
        stock,
        {
            "ram_gb": ram,
            "storage_gb": storage,
            "processor": processor,
            "battery_hours": battery
        },
        ["coding", "college", "office", "gaming"]
    )


smartwatches = [
    ("FitWatch Pro", 4999, 4.5, 20, 10),
    ("ActiveWatch S", 3499, 4.3, 30, 7),
    ("HealthTrack X", 5999, 4.6, 15, 12),
    ("SportWatch Lite", 2999, 4.2, 35, 8),
    ("UrbanWatch", 4499, 4.4, 22, 9),
]

for i, item in enumerate(smartwatches, 1):
    name, price, rating, stock, battery = item

    add_product(
        f"SW{i:03d}",
        name,
        "Electronics",
        "Smartwatches",
        "WearTech",
        price,
        "Smartwatch with fitness tracking, notifications and activity monitoring.",
        rating,
        stock,
        {
            "battery_days": battery,
            "water_resistant": True,
            "heart_rate": True,
            "gps": True
        },
        ["fitness", "running", "health", "daily use"]
    )


# ============================================================
# FASHION
# ============================================================

shoes = [
    ("RunFlex Pro", 3499, 4.6, 25, "mesh", "high"),
    ("ComfortRun X", 2999, 4.5, 35, "knit", "high"),
    ("StreetStep", 2499, 4.2, 40, "synthetic", "medium"),
    ("TrailMaster", 4299, 4.7, 15, "mesh", "high"),
    ("DailyWalk Pro", 1999, 4.3, 50, "mesh", "high"),
]

for i, item in enumerate(shoes, 1):
    name, price, rating, stock, material, comfort = item

    add_product(
        f"SH{i:03d}",
        name,
        "Fashion",
        "Running Shoes",
        "StrideFit",
        price,
        "Comfortable footwear suitable for active lifestyles and daily use.",
        rating,
        stock,
        {
            "material": material,
            "comfort": comfort,
            "water_resistant": False,
            "lightweight": True
        },
        ["running", "walking", "fitness", "college"]
    )


backpacks = [
    ("CampusPack 25L", 1499, 4.4, 40, 25, "water resistant"),
    ("TravelPack Pro", 2499, 4.6, 22, 35, "water resistant"),
    ("UrbanCarry", 1899, 4.3, 30, 22, "standard"),
    ("LaptopPack X", 2999, 4.7, 18, 30, "water resistant"),
    ("DailyPack Lite", 999, 4.1, 60, 20, "standard"),
]

for i, item in enumerate(backpacks, 1):
    name, price, rating, stock, capacity, material = item

    add_product(
        f"BG{i:03d}",
        name,
        "Fashion",
        "Backpacks",
        "CarryPro",
        price,
        "Practical backpack for college, work and everyday travel.",
        rating,
        stock,
        {
            "capacity_liters": capacity,
            "material": material,
            "laptop_compartment": True
        },
        ["college", "office", "travel", "daily use"]
    )


watches = [
    ("Classic Steel", 3999, 4.4, 20, "stainless steel"),
    ("Urban Chrono", 5999, 4.6, 12, "stainless steel"),
    ("Minimal Time", 2499, 4.2, 35, "leather"),
    ("Executive Pro", 7999, 4.7, 8, "stainless steel"),
    ("Daily Classic", 1999, 4.1, 45, "leather"),
]

for i, item in enumerate(watches, 1):
    name, price, rating, stock, material = item

    add_product(
        f"WT{i:03d}",
        name,
        "Fashion",
        "Watches",
        "TimeCraft",
        price,
        "Classic watch designed for everyday and formal occasions.",
        rating,
        stock,
        {
            "material": material,
            "water_resistant": True,
            "style": "classic"
        },
        ["office", "formal", "daily use", "gifting"]
    )


# ============================================================
# T-SHIRTS
# ============================================================

tshirts = [
    ("Urban Tee Classic", 699, 4.3, 50, "cotton", "regular"),
    ("ComfortFit T-Shirt", 799, 4.5, 40, "cotton", "regular"),
    ("StreetStyle Tee", 899, 4.4, 35, "cotton", "slim"),
    ("DailyWear T-Shirt", 599, 4.2, 60, "cotton", "regular"),
    ("Premium Soft Tee", 999, 4.7, 25, "cotton", "slim"),
]

for i, item in enumerate(tshirts, 1):
    name, price, rating, stock, material, fit = item

    add_product(
        f"TS{i:03d}",
        name,
        "Fashion",
        "T-Shirts",
        "UrbanWear",
        price,
        "Comfortable T-shirt suitable for casual everyday wear.",
        rating,
        stock,
        {
            "material": material,
            "fit": fit,
            "casual": True,
            "lightweight": True
        },
        ["casual", "college", "daily use", "travel"]
    )
# ============================================================
# SHIRTS
# ============================================================

shirts = [
    ("Urban Casual Shirt", 899, 4.4, 40, "cotton", "regular"),
    ("Classic Oxford Shirt", 999, 4.6, 30, "cotton", "regular"),
    ("Daily Comfort Shirt", 799, 4.3, 50, "cotton", "regular"),
    ("SlimFit Casual Shirt", 949, 4.5, 25, "cotton", "slim"),
    ("Premium Formal Shirt", 1199, 4.7, 20, "cotton", "slim"),
]

for i, item in enumerate(shirts, 1):
    name, price, rating, stock, material, fit = item

    add_product(
        f"SR{i:03d}",
        name,
        "Fashion",
        "Shirts",
        "UrbanWear",
        price,
        "Stylish shirt suitable for casual, college and office wear.",
        rating,
        stock,
        {
            "material": material,
            "fit": fit,
            "formal": True,
            "comfortable": True
        },
        ["casual", "college", "office", "daily use"]
    )





# ============================================================
# HOME
# ============================================================

air_fryers = [
    ("CrispChef 4L", 4999, 4.5, 18, 4, 1400),
    ("AirCook Pro", 5999, 4.6, 12, 5, 1600),
    ("QuickFry Lite", 3499, 4.2, 30, 3, 1200),
    ("FamilyFry X", 6999, 4.7, 10, 7, 1800),
    ("SmartFry", 7999, 4.6, 8, 6, 1700),
]

for i, item in enumerate(air_fryers, 1):
    name, price, rating, stock, capacity, watts = item

    add_product(
        f"AF{i:03d}",
        name,
        "Home",
        "Air Fryers",
        "HomeChef",
        price,
        "Kitchen air fryer designed for convenient low-oil cooking.",
        rating,
        stock,
        {
            "capacity_liters": capacity,
            "power_watts": watts,
            "digital_controls": True
        },
        ["cooking", "kitchen", "family"]
    )


vacuum_cleaners = [
    ("CleanBot X", 8999, 4.5, 12, 120, 90),
    ("HomeVac Pro", 6999, 4.4, 18, 150, 85),
    ("DustFree Lite", 4999, 4.2, 30, 100, 80),
    ("PowerClean Max", 10999, 4.7, 8, 180, 95),
    ("QuickClean", 3999, 4.1, 35, 90, 75),
]

for i, item in enumerate(vacuum_cleaners, 1):
    name, price, rating, stock, suction, battery = item

    add_product(
        f"VC{i:03d}",
        name,
        "Home",
        "Vacuum Cleaners",
        "CleanHome",
        price,
        "Vacuum cleaner designed for convenient home cleaning.",
        rating,
        stock,
        {
            "suction_power": suction,
            "battery_minutes": battery,
            "cordless": True
        },
        ["home cleaning", "daily use"]
    )


# ============================================================
# SPORTS
# ============================================================

fitness = [
    ("FitMat Pro", 1299, 4.5, 50, "high"),
    ("PowerBand Set", 999, 4.3, 60, "medium"),
    ("GymKit Basic", 2499, 4.4, 30, "medium"),
    ("StrengthPack Pro", 4999, 4.7, 15, "high"),
    ("HomeGym Starter", 3499, 4.5, 20, "high"),
]

for i, item in enumerate(fitness, 1):
    name, price, rating, stock, resistance = item

    add_product(
        f"FT{i:03d}",
        name,
        "Sports",
        "Fitness Equipment",
        "FitZone",
        price,
        "Fitness equipment suitable for home workouts and exercise.",
        rating,
        stock,
        {
            "resistance": resistance,
            "portable": True,
            "home_use": True
        },
        ["fitness", "home workout", "gym", "exercise"]
    )


# ============================================================
# WRITE CSV
# ============================================================

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "product_id",
    "name",
    "category",
    "subcategory",
    "brand",
    "price",
    "currency",
    "description",
    "rating",
    "stock",
    "attributes",
    "use_cases"
]


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(products)


print("=" * 70)
print("       RAZORPAY AI COMMERCE AGENT")
print("          UNIVERSAL CATALOG GENERATOR")
print("=" * 70)

print()
print(f"Catalog created successfully!")
print(f"File: {OUTPUT_FILE}")
print(f"Total products: {len(products)}")

print("\nCategories:")
print("-" * 70)

category_counts = {}

for product in products:

    category = product["category"]

    category_counts[category] = (
        category_counts.get(category, 0) + 1
    )

for category, count in category_counts.items():

    print(f"{category}: {count} products")

print()
print("=" * 70)