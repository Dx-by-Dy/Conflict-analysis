from extended_highs_model import ExtendedHighsModel
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
        self.__root_node.exh.set_consistent()

        self.__mip_state = MipState(
            convergence_tolerance=convergence_tolerance)
        self.__mip_state.update_solution(self.__root_node.exh.solution)
        self.__stack: list[Node] = [self.__root_node]

        # -----------------------
        self.graphes = [(self.__root_node.exh.graph,
                         self.__root_node.exh.solution.is_infeasible())]
        # -----------------------

    # def __set_branchability(self, node: Node) -> None:
    #     if node.exh.solution.is_infeasible():
    #         node.branchability = Branchability.Infeasible
    #     elif node.exh.solution.is_feasible() and node.exh.solution.is_primal:
    #         node.branchability = Branchability.IntFeasible
    #     elif node.exh.solution.is_feasible() and self.__mip_state.check_branchability_of_node(node):
    #         node.branchability = Branchability.Branchable
    #     else:
    #         node.branchability = Branchability.Dropped

    def __analyze(self, node: Node) -> None:
        if node.exh.solution.is_infeasible():
            branchability = Branchability.Infeasible
            self.__update_by_infeasible_node(node)
        elif node.exh.solution.is_feasible() and node.exh.solution.is_primal:
            branchability = Branchability.IntFeasible
            self.__mip_state.update_solution(node.exh.solution)
        elif node.exh.solution.is_feasible() and self.__mip_state.check_branchability_of_node(node):
            branchability = Branchability.Branchable
        else:
            branchability = Branchability.Dropped
            if self.__use_dropped:
                self.__update_by_infeasible_node(node)

        if node.branchability == Branchability.Unknown:
            self.__mip_state.branchability_statistic.add(branchability)
        node.branchability = branchability

    def __branch(self, node: Node) -> tuple[Node, Node]:
        self.__mip_state.number_of_branches += 1

        bnb_branch = node.exh.solution.find_bnb_branch()

        left_exh = node.exh.copy()
        right_exh = node.exh.copy()

        left_exh.change_var_bounds(
            bnb_branch.var, bnb_branch.left_bound.lower, bnb_branch.left_bound.upper)
        right_exh.change_var_bounds(
            bnb_branch.var, bnb_branch.right_bound.lower, bnb_branch.right_bound.upper)

        left_node = Node(left_exh)
        left_node.exh.set_consistent(bnb_branch.var)

        right_node = Node(right_exh)
        right_node.exh.set_consistent(bnb_branch.var)

        # ---------------------------------------------------------------------------------
        self.graphes.append(
            (left_node.exh.graph, left_node.exh.solution.is_infeasible()))
        self.graphes.append(
            (right_node.exh.graph, right_node.exh.solution.is_infeasible()))
        # ---------------------------------------------------------------------------------
        self.__mip_state.number_of_relaxations += 2

        return sort_nodes(left_node, right_node)

    # def __realize_potential(self, node: Node, with_branch: bool) -> None:
    #     if node.branchability == Branchability.Branchable:
    #         if with_branch:
    #             left_node, right_node = self.__branch(node)
    #             self.__realize_potential(left_node, False)
    #             self.__set_branchability(right_node)
    #             self.__realize_potential(right_node, False)
    #         else:
    #             self.__mip_state.branchability_statistic.add(
    #                 Branchability.Branchable)
    #             self.__stack.append(node)
    #     elif node.branchability == Branchability.IntFeasible:
    #         self.__mip_state.branchability_statistic.add(
    #             Branchability.IntFeasible)
    #         self.__mip_state.update_solution(node.exh.solution)
    #     elif node.branchability == Branchability.Infeasible:
    #         self.__mip_state.branchability_statistic.add(
    #             Branchability.Infeasible)
    #         self.__update_by_infeasible_node(node)
    #     elif node.branchability == Branchability.Dropped:
    #         self.__mip_state.branchability_statistic.add(
    #             Branchability.Dropped)
    #         if self.__use_dropped:
    #             self.__update_by_infeasible_node(node)
    #     elif node.branchability == Branchability.Unknown:
    #         self.__mip_state.branchability_statistic.add(
    #             Branchability.Unknown)

    def __update_by_infeasible_node(self, node: Node) -> None:
        # self.__mip_state.number_of_infeasible_nodes += 1
        if self.__with_presolve and self.__cutting_mod > 0:
            graph_cut = node.exh.graph.get_graph_cut()
            if not graph_cut.is_empty() and (not graph_cut.is_trivial or self.__trivial_graph_cut):
                if not graph_cut.is_trivial:
                    self.__mip_state.number_of_non_trivial_graph_cuts += 1
                if self.__cutting_check:
                    self.__mip_state.number_of_relaxations += 1
                if not self.__cutting_check or self.__root_node.exh.validate_cut(graph_cut):
                    for stack_node in self.__stack:
                        stack_node.exh.add_row(graph_cut)

    def __step(self, node: Node) -> None:
        if node.exh.set_consistent():
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
