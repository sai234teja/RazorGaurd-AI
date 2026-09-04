import sys

lines = open("intent_normalizer.py").readlines()
out = []

in_class = True

for line in lines:
    if line.startswith("CATEGORY_MAP = {"):
        # Everything from here needs 4 spaces
        break

# wait, I can just indent everything from CATEGORY_MAP to line 584 by 4 spaces.
# But what about the normalize method? It was deleted!
