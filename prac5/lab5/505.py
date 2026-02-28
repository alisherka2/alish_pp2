import re

a=input()
result = re.match("^[a-zA-Z]*[0-9]$", a)
if result:
    print("Yes")
else:   print("No")