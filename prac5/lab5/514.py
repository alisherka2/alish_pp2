import re

text = input()
pattern=re.compile(r"^\d+$")
if pattern.match(text):
    print("Match")
else:   print("No match")
