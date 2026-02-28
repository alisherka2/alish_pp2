import re

text = input()
pattern = r"Name: (.+), Age: (\d+)"

match = re.search(pattern, text)

if match:
    name = match.group(1)
    age = match.group(2)
    print(f"{name} {age}")