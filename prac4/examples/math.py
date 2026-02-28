# 1
import math

a=int(input("Enter a: "))
print(math.radians(a))

# 2
import trap

h = int(input("Enter h: "))
b1 = int(input("Enter b1: "))
b2 = int(input("Enter b2: "))
print(trap.area(b1, b2, h))

# 3
import polygon

side = int(input("Input number of sides: "))
length = float(input("Input the length of a side: "))
print(polygon.area(side, length))

# 4
import parallel

base_para = float(input("Length of base: "))
height_para = float(input("Height of parallelogram: "))
print(parallel.paral(base_para, height_para))

