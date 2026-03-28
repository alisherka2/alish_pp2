n = int(input())
words = input().split()
longestword = max(words, key=len)
print(longestword)