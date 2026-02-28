import re

text = input()
pattern = re.compile(r"\b\w+\b")
words = pattern.findall(text)
count = len(words)
print(count)