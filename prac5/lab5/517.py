import re

n = input()
pattern = r"\d{2}/\d{2}/\d{4}"
match = re.findall(pattern, n)
print(len(match))