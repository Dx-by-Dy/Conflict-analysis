import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("problem", type=str, help="Path to problem.")
    parser.add_argument("--solver", type=str, default="enable", choices=["enable", "disable"],
                        help="Enable or disable the custom solver. (default = `enable`)")
    parser.add_argument("--highs", type=str, default="disable", choices=["enable", "disable"],
                        help="Enable or disable the Highs solver. (default = `disable`)")
    parser.add_argument("--presolve", type=str, default="enable", choices=["enable", "disable"],
                        help="Enable or disable presolving in the custom solver. (default = `enable`)")
    parser.add_argument("--cutting", type=str, default="standard", choices=["yolo", "standard", "disable"],
                        help="Enable or disable cutting in the custom solver. (default = `standard`)")
    parser.add_argument("--silent", type=str, default="enable", choices=["enable", "disable"],
                        help="Enable or disable writing info from the custom solver. (default = `enable`)")
    args = parser.parse_args()

    if args.solver == "enable":
        from solver import Solver

        cutting_flag = 0

        if args.cutting == "standard":
            cutting_flag = 1
        elif args.cutting == "yolo":
            cutting_flag = 2

        sl = Solver(args.problem,
                    args.presolve == "enable",
                    cutting_flag,
                    args.silent == "enable")
        sl.start()
        print(sl.result())

    if args.highs == "enable":
        from highspy import Highs

        h = Highs()
        h.readModel(args.problem)
        h.silent()
        h.presolve()

        h.run()
        print(h.getSolution().col_value)
        print(h.getInfo().objective_function_value)
