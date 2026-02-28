import re

text = input()
result = re.findall("[0-9]+[0-9]", text)
print(" ".join(result))