import zipfile
import os

zip_path = r"C:\Users\ramug\OneDrive\Desktop\RazorPay AI Commerce Agent (2).zip"
target_file = "RazorPay AI Commerce Agent/intent_normalizer.py"

with zipfile.ZipFile(zip_path, "r") as z:
    with open("intent_normalizer.py", "wb") as f:
        f.write(z.read(target_file))
print("Restored!")
