import re

text = input()
result = re.findall("[A-Z]", text)
print(len(result))