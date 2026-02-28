import math

def area(side, length):
    ar = (side * length ** 2) / (4 * math.tan(math.pi / side))
    return ar