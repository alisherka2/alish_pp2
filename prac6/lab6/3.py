n = int(input())
words = input().split()
output = [f"{i}:{word}" for i, word in enumerate(words)]
print(" ".join(output))