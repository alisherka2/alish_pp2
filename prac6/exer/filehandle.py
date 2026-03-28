import os
import shutil
from functools import reduce

#Create
file_path = "sample.txt"
with open(file_path, "w") as f:
    f.write("Hello, this is a sample file.\n")
    f.write("This is the second line.\n")

print("File created and data written.\n")

#Read and print
print("Reading file contents:")
with open(file_path, "r") as f:
    content = f.read()
    print(content)

#Append lines
with open(file_path, "a") as f:
    f.write("This is an appended line.\n")

print("After appending:")
with open(file_path, "r") as f:
    print(f.read())

#Copy and backup
backup_path = "backup_sample.txt"
shutil.copy(file_path, backup_path)
print(f"File copied to {backup_path}\n")

#Delete files
if os.path.exists(backup_path):
    os.remove(backup_path)
    print("Backup file deleted safely.\n")
else:
    print("File does not exist.\n")

# =========================
# BUILT-IN FUNCTIONS PRACTICE
# =========================

numbers = [1, 2, 3, 4, 5, 6]

# 1. Use map() and filter()
squared = list(map(lambda x: x**2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))

print("Squared numbers:", squared)
print("Even numbers:", evens)
print()

# 2. Aggregate with reduce()
sum_all = reduce(lambda x, y: x + y, numbers)
print("Sum using reduce:", sum_all)
print()

# 3. Use enumerate() and zip()
names = ["Alice", "Bob", "Charlie"]
scores = [85, 90, 78]

print("Using enumerate:")
for index, name in enumerate(names):
    print(index, name)

print("\nUsing zip:")
for name, score in zip(names, scores):
    print(name, score)
print()

# 4. Demonstrate type checking and conversions
value = "123"

print("Type checking:")
print(isinstance(value, str))

converted_int = int(value)
converted_float = float(value)

print("Converted to int:", converted_int)
print("Converted to float:", converted_float)