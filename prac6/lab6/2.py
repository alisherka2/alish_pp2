n = int(input())
numbers = list(map(int, input().split()))
evennumbers = list(filter(lambda x: x % 2 == 0, numbers))
print(len(evennumbers))