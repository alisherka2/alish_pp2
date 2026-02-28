import re

n = input()
pattern = input()
match = re.findall(pattern, n)
print(len(match))