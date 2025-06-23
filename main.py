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
    parser.add_argument("--cutting", type=str, default="fuip", choices=["root", "fuip", "disable"],
                        help="Cutting behaviour in the custom solver. (default = `fuip`)")
    parser.add_argument("--cutting_check", type=str, default="disable", choices=["enable", "disable"],
                        help="Enable or disable cutting check in the custom solver. (default = `disable`)")
    parser.add_argument("--trivial_graph_cut", type=str, default="enable", choices=["enable", "disable"],
                        help="Enable or disable trivial graph cuts in the custom solver. (default = `enable`)")
    parser.add_argument("--silent", type=str, default="enable", choices=["enable", "disable"],
                        help="Enable or disable writing info from the custom solver. (default = `enable`)")
    parser.add_argument("--fuip_size", type=int, default=1,
                        help="Size of FUIP group in the custom solver. (default = `1`)")
    parser.add_argument("--use_dropped", type=str, default="disable", choices=["enable", "disable"],
                        help="Enable or disable using the dropped nodes like infeasible in the custom solver. (default = `disable`)")
    args = parser.parse_args()

    if args.solver == "enable":
        from solver import Solver

        cutting_mod = 0
        if args.cutting == "fuip":
            cutting_mod = 1
        elif args.cutting == "root":
            cutting_mod = 2

        sl = Solver(path_to_problem=args.problem,
                    with_presolve=args.presolve == "enable",
                    cutting_check=args.cutting_check == "enable",
                    cutting_mod=cutting_mod,
                    trivial_graph_cut=args.trivial_graph_cut == "enable",
                    use_dropped=args.use_dropped == "enable",
                    silent=args.silent == "enable",
                    fuip_size=args.fuip_size)
        sl.solve()
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
