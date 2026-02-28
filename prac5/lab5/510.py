import re

text = input()
if re.search("cat|dog", text):
    print("Yes")
else:   print("No")