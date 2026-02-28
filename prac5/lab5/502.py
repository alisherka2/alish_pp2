import re

a=input()
b=input()
if re.search(b, a):
    print("Yes")
else:   print("No")