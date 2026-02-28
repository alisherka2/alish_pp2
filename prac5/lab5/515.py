import re
def double_digit(match):
    digit = match.group()
    return digit * 2

text = input()
result = re.sub(r"\d", double_digit, text)
print(result)