import argparse
from graph import Graph
from solver import Solver
from highspy import Highs

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--problem")
    parser.add_argument("--solver", default="enable")
    parser.add_argument("--highs", default="disable")
    parser.add_argument("--presolve", default="enable")
    parser.add_argument("--cutting", default="enable")
    args = parser.parse_args()

    if args.solver == "enable":
        sl = Solver(args.problem, args.presolve ==
                    "enable", args.cutting == "enable")
        sl.start()
        print(sl.result())

    if args.highs == "enable":
        h = Highs()
        h.readModel(args.problem)
        h.silent()
        h.presolve()

        # _ = list(map(print, dir(h)))

        h.run()
        print(h.getSolution().col_value)
        print(h.getInfo().objective_function_value)
