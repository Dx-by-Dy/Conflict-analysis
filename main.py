from highspy import Highs
from bnb import BnB

if __name__ == '__main__':
    path = "../../Downloads/benchmark/supportcase16.mps"
    #path = "test.lp"
    B = BnB(path, max_var_value=1)
    B.start()
    print(B.result())

    h = Highs()
    h.readModel(path)
    h.silent()

    h.run()
    print(h.getSolution().col_value)
    print(h.getInfo().objective_function_value)