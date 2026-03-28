import os
import shutil

file_path = "sample.txt"
#Create nested directories
nested_dir = "parent/child/grandchild"
os.makedirs(nested_dir, exist_ok=True)
print("Nested directories created.\n")

#List files and folders
print("Listing current directory:")
for item in os.listdir("."):
    print(item)
print()

#Find files by extension
print("Finding .txt files:")
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".txt"):
            print(os.path.join(root, file))
print()

#Move/copy files between directories
dest_path = os.path.join(nested_dir, "sample.txt")
shutil.copy(file_path, dest_path)
print(f"File copied to {dest_path}\n")

moved_path = "moved_sample.txt"
shutil.move(file_path, moved_path)
print(f"File moved to {moved_path}\n")
