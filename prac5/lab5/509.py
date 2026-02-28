import re
#output words that exactly have 3 letters
text = input()
result = re.findall(r"\b\w{3}\b", text)
print(len(result))