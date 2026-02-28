import re

text = input()
pattern = input()
replace = input()
result = re.sub(pattern, replace, text)
print(result)