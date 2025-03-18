import highspy
from bnb import BnB

if __name__ == '__main__':
    path = "sudoku_repl.lp"
    B = BnB(path)
    B.start()
    print(B.result())

    h = highspy.Highs()
    h.readModel(path)
    h.silent()
    h.run()
    print(h.getSolution().col_value)
    print(h.getInfo().objective_function_value)