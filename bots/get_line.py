import sys


filename, number = sys.argv[1:]
with open(filename, "r") as file:
    counter: int = 1
    for i, line in enumerate(file.readlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if counter == int(number):
            print(i + 1, line)
            break
        counter += 1
