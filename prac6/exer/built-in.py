from functools import reduce

numbers = [1, 2, 3, 4, 5, 6]

#Use map() and filter()
squared = list(map(lambda x: x**2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))

print("Squared numbers:", squared)
print("Even numbers:", evens)
print()

#Aggregate with reduce()
sum_all = reduce(lambda x, y: x + y, numbers)
print("Sum using reduce:", sum_all)
print()

#Use enumerate() and zip()
names = ["Alice", "Bob", "Charlie"]
scores = [85, 90, 78]

print("Using enumerate:")
for index, name in enumerate(names):
    print(index, name)

print("\nUsing zip:")
for name, score in zip(names, scores):
    print(name, score)
print()

#Demonstrate type checking and conversions
value = "123"

print("Type checking:")
print(isinstance(value, str))

converted_int = int(value)
converted_float = float(value)

print("Converted to int:", converted_int)
print("Converted to float:", converted_float)