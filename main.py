import highspy
from highspy import Highs

from bnb import BnB

if __name__ == '__main__':
    #path = "../../Downloads/benchmark/supportcase16.mps"
    path = "test.lp"
    #B = BnB(path, max_var_value=1)
    #B.start()
    #print(B.result())

    h = Highs()
    h.readModel(path)
    h.silent()

    h.presolve()
    #h.solve()
    #h.run()
    print(h.getSolution().col_value)
    #print(h.getInfo().objective_function_value)
    print(h.getPresolvedLp().col_lower_)
    print(h.getPresolvedLp().col_upper_)
    print(list(map(lambda x: h.getColByName(x)[1], h.getPresolvedLp().col_names_)))
    #print(help(h))
    #print(help(h.getPresolvedLp()))