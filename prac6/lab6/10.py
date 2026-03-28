n = int(input())
numbers = list(map(int, input().split()))
counttruth = sum(map(bool, numbers))
print(counttruth)