import re

text = input()
result = re.findall(r"\w+", text)
print(len(result))