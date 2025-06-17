from extended_highs_model import ExtendedHighsModel
from mip_state import MipState, State
from node import Node


class Solver:
    def __init__(self,
                 path_to_problem: str,
                 with_presolve: bool,
                 cutting_mod: int,
                 silent: bool,
                 convergence_tolerance: float = 1e-4,
                 primal_tolerance: float = 1e-9) -> None:

        self.__with_presolve = with_presolve
        self.__cutting_mod = cutting_mod
        self.__silent = silent

        self.__root_node = Node(ExtendedHighsModel(
            with_presolve,
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

    def solver_step(self, node: Node) -> Node | None:
        new_nodes = node.splitting()
        self.__mip_state.number_of_branches += 1

        if new_nodes is not None:
            left_node, right_node = new_nodes
            self.__mip_state.number_of_relaxations += 2
        else:
            while self.__stack:
                stack_node = self.__stack.pop()
                if self.__mip_state.primal_solution.objective is None or \
                        stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return stack_node
            return None

        # ---------------------------------------------------------------------------------
        self.graphes.append(
            (left_node.exh.graph, left_node.exh.solution.is_infeasible()))
        self.graphes.append(
            (right_node.exh.graph, right_node.exh.solution.is_infeasible()))
        # ---------------------------------------------------------------------------------

        if left_node.is_feasible() and right_node.is_feasible():
            if left_node.exh.solution.objective < right_node.exh.solution.objective:
                if not right_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None or \
                            right_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        self.__stack.append(right_node)
                else:
                    self.__mip_state.update_solution(
                        right_node.exh.solution)

                if not left_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None or \
                            left_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        return left_node
                else:
                    self.__mip_state.update_solution(
                        left_node.exh.solution)

                while self.__stack:
                    stack_node = self.__stack.pop()
                    if self.__mip_state.primal_solution.objective is None or \
                            stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        return stack_node
                return None
            else:
                if not left_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None or \
                            left_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        self.__stack.append(left_node)
                else:
                    self.__mip_state.update_solution(
                        left_node.exh.solution)

                if not right_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None or \
                            right_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        return right_node
                else:
                    self.__mip_state.update_solution(
                        right_node.exh.solution)

                while self.__stack:
                    stack_node = self.__stack.pop()
                    if self.__mip_state.primal_solution.objective is None or \
                            stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        return stack_node
                return None

        elif left_node.is_feasible() and not right_node.is_feasible():
            if right_node.exh.solution.is_infeasible():
                self.__mip_state.number_of_infeasible_nodes += 1

                if self.__with_presolve and self.__cutting_mod > 0:
                    number_of_negative, indices, values = right_node.exh.graph.get_cut()
                    if self.__cutting_mod < 2:
                        self.__mip_state.number_of_relaxations += 1
                    if self.__cutting_mod == 2 or self.__root_node.exh.validate_cut(indices, values):
                        for node in self.__stack:
                            node.exh.add_row(
                                number_of_negative, indices, values)
                        left_node.exh.add_row(
                            number_of_negative, indices, values)

            if not left_node.exh.solution.is_primal:
                if self.__mip_state.primal_solution.objective is None or \
                        left_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return left_node
            else:
                self.__mip_state.update_solution(left_node.exh.solution)

            while self.__stack:
                stack_node = self.__stack.pop()
                if self.__mip_state.primal_solution.objective is None or \
                        stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return stack_node
            return None

        elif not left_node.is_feasible() and right_node.is_feasible():
            if left_node.exh.solution.is_infeasible():
                self.__mip_state.number_of_infeasible_nodes += 1

                if self.__with_presolve and self.__cutting_mod > 0:
                    number_of_negative, indices, values = left_node.exh.graph.get_cut()
                    if self.__cutting_mod < 2:
                        self.__mip_state.number_of_relaxations += 1
                    if self.__cutting_mod == 2 or self.__root_node.exh.validate_cut(indices, values):
                        for node in self.__stack:
                            node.exh.add_row(
                                number_of_negative, indices, values)
                        right_node.exh.add_row(
                            number_of_negative, indices, values)

            if not right_node.exh.solution.is_primal:
                if self.__mip_state.primal_solution.objective is None or \
                        right_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return right_node
            else:
                self.__mip_state.update_solution(right_node.exh.solution)

            while self.__stack:
                stack_node = self.__stack.pop()
                if self.__mip_state.primal_solution.objective is None or \
                        stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return stack_node
            return None

        else:
            if left_node.exh.solution.is_infeasible():
                self.__mip_state.number_of_infeasible_nodes += 1

                if self.__with_presolve and self.__cutting_mod > 0:
                    number_of_negative, indices, values = left_node.exh.graph.get_cut()
                    if self.__cutting_mod < 2:
                        self.__mip_state.number_of_relaxations += 1
                    if self.__cutting_mod == 2 or self.__root_node.exh.validate_cut(indices, values):
                        for node in self.__stack:
                            node.exh.add_row(
                                number_of_negative, indices, values)

            if right_node.exh.solution.is_infeasible():
                self.__mip_state.number_of_infeasible_nodes += 1

                if self.__with_presolve and self.__cutting_mod > 0:
                    number_of_negative, indices, values = right_node.exh.graph.get_cut()
                    if self.__cutting_mod < 2:
                        self.__mip_state.number_of_relaxations += 1
                    if self.__cutting_mod == 2 or self.__root_node.exh.validate_cut(indices, values):
                        for node in self.__stack:
                            node.exh.add_row(
                                number_of_negative, indices, values)

            while self.__stack:
                stack_node = self.__stack.pop()
                if self.__mip_state.primal_solution.objective is None or \
                        stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return stack_node
            return None

    def start(self):
        node = self.__stack.pop()

        while node is not None:
            node = self.solver_step(node=node)

            if node is not None:
                self.__mip_state.update_solution(
                    min(self.__stack + [node], key=lambda x: x.exh.solution.objective).exh.solution)
            elif self.__stack:
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
