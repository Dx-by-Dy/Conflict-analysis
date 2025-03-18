import re

def replace_match(match):
    numbers = match.group(1)
    return numbers.replace(",", ";")[1:-1]

pattern1 = r'(\[\d,\d,\d\])'
pattern2 = r'(\[\d,\d\])'

with open("sudoku.lp", "r") as file:
    with open("sudoku_repl.lp", 'w') as nfile:
        while line := file.readline():
            result = re.sub(pattern1, replace_match, line)
            result = re.sub(pattern2, replace_match, result)
            if line == "Bounds\n":
                for i in range(9):
                    for j in range(9):
                        for k in range(9):
                            nfile.write(f"sub{i};{j};{k}: G{i};{j};{k} <= 1\n")
            if line == "Binaries\n":
                nfile.write("General\n")
                for i in range(9):
                    for j in range(9):
                        for k in range(9):
                            nfile.write(f"G{i};{j};{k}\n")
                nfile.write("End")
                break
            nfile.write(result)