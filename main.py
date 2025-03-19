import highspy
from bnb import BnB

if __name__ == '__main__':
    #path = "../../Downloads/benchmark/enlight_hard.mps"
    #path = "../../Downloads/benchmark/enlight8.mps"
    #path = "../../Downloads/benchmark/glass-sc.mps" # highs not solve
    #path = "../../Downloads/benchmark/iis-glass-cov.mps" # highs not solve
    # path = "../../Downloads/benchmark/h80x6320.mps" # to easy
    # path = "../../Downloads/benchmark/air05.mps" # to hard
    #path = "../../Downloads/benchmark/air04.mps" # to hard
    path = "../../Downloads/benchmark/supportcase16.mps"
    #path = "test.lp"
    B = BnB(path, max_var_value=1)
    B.start()
    print(B.result())

    h = highspy.Highs()
    h.readModel(path)
    h.silent()

    h.run()
    print(h.getSolution().col_value)
    print(h.getInfo().objective_function_value)