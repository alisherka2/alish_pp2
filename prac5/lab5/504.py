import re

a=input()
result = re.findall("[0-9]", a)
for r in result:
    print(r, end=' ')