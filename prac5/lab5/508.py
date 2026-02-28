import re

a=input()
b=input()
result = re.split(b, a)
print(",".join(result))