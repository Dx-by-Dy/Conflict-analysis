from extended_highs_model import ExtendedHighsModel
from mip_state import MipState, State
from node import Node


class Solver:
    def __init__(self,
                 path_to_problem: str,
                 with_presolve: bool,
                 cutting_check: bool,
                 cutting_mod: int,
                 silent: bool,
                 trivial_graph_cut: bool,
                 fuip_size: int = 1,
                 convergence_tolerance: float = 1e-4,
                 primal_tolerance: float = 1e-9) -> None:

        self.__with_presolve = with_presolve
        self.__cutting_check = cutting_check
        self.__cutting_mod = cutting_mod
        self.__trivial_graph_cut = trivial_graph_cut
        self.__silent = silent

        self.__root_node = Node(ExtendedHighsModel(
            with_presolve,
            cutting_mod,
            fuip_size,
            path_to_problem,
            primal_tolerance))
        self.__root_node.exh.set_consistent()
        self.__stack: list[Node] = [self.__root_node]

        self.__mip_state = MipState(
            convergence_tolerance=convergence_tolerance)
        self.__mip_state.update_solution(self.__root_node.exh.solution)

        # -----------------------
        self.graphes = [(self.__root_node.exh.graph,
                         self.__root_node.exh.solution.is_infeasible())]
        # -----------------------

    def add_to_stack(self, first_node: Node, second_node: Node) -> None:
        def add_to_stack_or_mip_state_update(node: Node) -> None:
            if not node.exh.solution.is_primal:
                if self.__mip_state.primal_solution.objective is None or \
                        node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    self.__stack.append(node)
            else:
                self.__mip_state.update_solution(node.exh.solution)

        if not first_node.is_feasible() and not second_node.is_feasible():
            self.change_stack_and_mip_state_by_node(first_node)
            self.change_stack_and_mip_state_by_node(second_node)
            return
        if first_node.is_feasible() and second_node.is_feasible():
            if first_node.exh.solution.objective > second_node.exh.solution.objective:
                first_node, second_node = second_node, first_node
            add_to_stack_or_mip_state_update(first_node)
            add_to_stack_or_mip_state_update(second_node)
            return
        if second_node.is_feasible():
            first_node, second_node = second_node, first_node
        add_to_stack_or_mip_state_update(first_node)
        self.change_stack_and_mip_state_by_node(second_node)

    def change_stack_and_mip_state_by_node(self, node: Node) -> None:
        if node.exh.solution.is_infeasible():
            self.__mip_state.number_of_infeasible_nodes += 1
            if self.__with_presolve and self.__cutting_mod > 0:
                graph_cut = node.exh.graph.get_graph_cut()
                if not graph_cut.is_empty() and (not graph_cut.is_trivial or self.__trivial_graph_cut):
                    if self.__cutting_check:
                        self.__mip_state.number_of_relaxations += 1
                    if not self.__cutting_check or self.__root_node.exh.validate_cut(graph_cut):
                        for stack_node in self.__stack:
                            stack_node.exh.add_row(graph_cut)

    def step(self, node: Node) -> None:
        if not node.exh.is_consistent:
            self.__mip_state.number_of_relaxations += 1
            node.exh.set_consistent()
            if not node.is_feasible():
                self.change_stack_and_mip_state_by_node(node)
                return

        new_nodes = node.branching()
        self.__mip_state.number_of_branches += 1

        if new_nodes is not None:
            left_node, right_node = new_nodes

            # ---------------------------------------------------------------------------------
            self.graphes.append(
                (left_node.exh.graph, left_node.exh.solution.is_infeasible()))
            self.graphes.append(
                (right_node.exh.graph, right_node.exh.solution.is_infeasible()))
            # ---------------------------------------------------------------------------------

            self.__mip_state.number_of_relaxations += 2
            self.add_to_stack(left_node, right_node)

    def solve(self):
        while self.__stack:

            node = self.__stack.pop()
            if self.__mip_state.primal_solution.objective is None or \
                    node.exh.solution.objective < self.__mip_state.primal_solution.objective:

                self.step(node)

                if self.__stack:
                    self.__mip_state.update_solution(
                        min(self.__stack, key=lambda x: x.exh.solution.objective).exh.solution)

                if not self.__silent:
                    self.printing_info()

            if self.__mip_state.state == State.Converged:
                break

        self.__mip_state.on_end()

        # --------------------------
        return self.graphes
        # --------------------------

    def printing_info(self) -> None:
        print(f"number of branches: {self.__mip_state.number_of_branches}\t" +
              f"primal value: {self.__mip_state.primal_solution.objective}\t" +
              f"dual value: {self.__mip_state.dual_solution.objective}\t" +
              f"number of infisible nodes: {self.__mip_state.number_of_infeasible_nodes}"
              )

    def result(self) -> MipState:
        return self.__mip_state
