import re

a=input()
b=input()
result = re.findall(b, a)
print(len(result))
