from math import isinf
from bound import Bound
from extended_highs_model import ExtendedHighsModel, SolveRes
from mip_state import MipState, State
from node import Branchability, Node, sort_nodes


class Solver:
    def __init__(self,
                 path_to_problem: str,
                 with_presolve: bool,
                 cutting_check: bool,
                 cutting_mod: int,
                 silent: bool,
                 trivial_graph_cut: bool,
                 use_dropped: bool,
                 fuip_size: int = 1,
                 convergence_tolerance: float = 1e-4,
                 primal_tolerance: float = 1e-9) -> None:

        self.__with_presolve = with_presolve
        self.__cutting_check = cutting_check
        self.__cutting_mod = cutting_mod
        self.__trivial_graph_cut = trivial_graph_cut
        self.__use_dropped = use_dropped
        self.__silent = silent

        self.__root_node = Node(ExtendedHighsModel(
            with_presolve,
            cutting_mod,
            fuip_size,
            path_to_problem,
            primal_tolerance))
        self.__root_node.exh.solve()

        self.__mip_state = MipState(convergence_tolerance)
        self.__mip_state.update_solution(self.__root_node.exh.solution)
        self.__stack: list[Node] = [self.__root_node]

        self.__analyze(self.__root_node)

        # -----------------------
        self.graphes = [(self.__root_node.exh.graph,
                         self.__root_node.exh.solution.is_infeasible())]
        # -----------------------

    def __analyze(self, node: Node) -> None:
        if node.branchability != Branchability.Unknown:
            return

        if node.exh.solution.is_infeasible():
            branchability = Branchability.Infeasible
            self.__update_by_infeasible_node(node)
        elif node.exh.solution.is_feasible() and node.exh.solution.is_primal:
            branchability = Branchability.IntFeasible
            self.__mip_state.update_solution(node.exh.solution)
        elif node.exh.solution.is_feasible() and self.__mip_state.check_node(node):
            branchability = Branchability.Branchable
        else:
            branchability = Branchability.Dropped
            if self.__use_dropped:
                self.__update_by_infeasible_node(node)

        self.__mip_state.branchability_statistic.add(branchability)
        node.branchability = branchability

    def __branch(self, node: Node) -> tuple[Node, Node]:
        self.__mip_state.number_of_branches += 1

        max_diff = 0
        nodes: tuple[Node, Node] = ()
        for var, val in zip(node.exh.solution.value[0], node.exh.solution.value[1]):
            if not var.is_general or var.is_conv() or min(val % 1, 1 - val % 1) < node.exh.solution.primal_tolerance:
                continue

            if abs(val - var.lower) <= node.exh.solution.primal_tolerance and not isinf(var.lower) and not isinf(var.upper):
                bound = (var.lower + var.upper) // 2
                left_bound = Bound(lower=var.lower + 1, upper=bound)
                right_bound = Bound(lower=bound + 1, upper=var.upper)
            elif abs(val - var.upper) <= node.exh.solution.primal_tolerance and not isinf(var.lower) and not isinf(var.upper):
                bound = (var.lower + var.upper) // 2 - 1
                left_bound = Bound(lower=var.lower, upper=bound)
                right_bound = Bound(lower=bound + 1, upper=var.upper - 1)
            else:
                if var.upper - var.lower > 10 and not isinf(var.lower) and not isinf(var.upper):
                    bound = (var.lower + var.upper) // 2
                else:
                    bound = int(val)
                left_bound = Bound(lower=var.lower, upper=bound)
                right_bound = Bound(lower=bound + 1, upper=var.upper)

            left_exh = node.exh.copy()
            right_exh = node.exh.copy()

            left_exh.change_var_bounds(
                var, left_bound.lower, left_bound.upper)
            right_exh.change_var_bounds(
                var, right_bound.lower, right_bound.upper)

            left_node = Node(left_exh)
            left_node.exh.solve(var)

            right_node = Node(right_exh)
            right_node.exh.solve(var)

            self.__analyze(left_node)
            self.__analyze(right_node)

            if left_node.branchability == Branchability.Branchable or len(nodes) == 0:
                diff = left_node.exh.solution.objective - node.exh.solution.objective
                if diff >= max_diff:
                    max_diff = diff
                    nodes = (left_node, right_node)

            if right_node.branchability == Branchability.Branchable or len(nodes) == 0:
                diff = right_node.exh.solution.objective - node.exh.solution.objective
                if diff >= max_diff:
                    max_diff = diff
                    nodes = (left_node, right_node)

            self.__mip_state.number_of_relaxations += 2

        # ---------------------------------------------------------------------------------
        self.graphes.append(
            (nodes[0].exh.graph, nodes[0].exh.solution.is_infeasible()))
        self.graphes.append(
            (nodes[1].exh.graph, nodes[1].exh.solution.is_infeasible()))
        # ---------------------------------------------------------------------------------

        return sort_nodes(nodes[0], nodes[1])

    def __update_by_infeasible_node(self, node: Node) -> None:
        # print(len(node.exh.getDualRay()[2]), len(node.exh.constraints))
        if self.__with_presolve and self.__cutting_mod > 0:
            graph_cut = node.exh.graph.get_graph_cut()
            if not graph_cut.is_empty() and (not graph_cut.is_trivial or self.__trivial_graph_cut):
                if not graph_cut.is_trivial:
                    self.__mip_state.number_of_non_trivial_graph_cuts += 1
                if self.__cutting_check:
                    self.__mip_state.number_of_resolved_nodes += 1
                if not self.__cutting_check or self.__root_node.exh.validate_cut(graph_cut):
                    for stack_node in self.__stack:
                        stack_node.exh.add_row(graph_cut)

    def __step(self, node: Node) -> None:
        res_solve = node.exh.solve()
        if res_solve == SolveRes.ResolvedAndChanged or res_solve == SolveRes.ResolvedAndUnchanged:
            self.__mip_state.number_of_resolved_nodes += 1
            node.branchability = Branchability.Unknown
            if res_solve == SolveRes.ResolvedAndChanged:
                self.__mip_state.number_of_objective_changes += 1

        self.__analyze(node)

        if node.branchability != Branchability.Branchable:
            return

        for child_node in self.__branch(node):
            self.__analyze(child_node)
            if child_node.branchability == Branchability.Branchable:
                self.__stack.append(child_node)

    def solve(self):
        while self.__stack:

            node = self.__stack.pop()

            if not self.__silent:
                self.printing_info(node)

            self.__step(node)

            if self.__stack:
                self.__mip_state.update_solution(
                    min(self.__stack, key=lambda x: x.exh.solution.objective).exh.solution)

            if self.__mip_state.state == State.Converged:
                break

        self.__mip_state.on_end()

        # --------------------------
        return self.graphes
        # --------------------------

    def printing_info(self, node: Node) -> None:
        print(f"number of branches: {self.__mip_state.number_of_branches}\t" +
              f"depth: {node.exh.graph.depth}\t" +
              f"primal value: {self.__mip_state.primal_solution.objective}\t" +
              f"dual value: {self.__mip_state.dual_solution.objective}\t"
              )

    def result(self) -> MipState:
        return self.__mip_state
