s = input()
vowels = "aeiouAEIOU"
if any(c in vowels for c in s):
    print("Yes")
else:
    print("No")