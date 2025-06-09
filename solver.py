from extended_highs_model import ExtendedHighsModel
from mip_state import MipState, State
from node import Node


class Solver:
    def __init__(self, path_to_problem: str,
                 convergence_tolerance: float = 1e-4,
                 primal_tolerance: float = 1e-9) -> None:

        self.__root_node = Node(ExtendedHighsModel(
            path_to_problem, primal_tolerance))
        self.__stack: list[Node] = [self.__root_node]

        self.__mip_state = MipState(
            convergence_tolerance=convergence_tolerance)
        self.__mip_state.update_solution(self.__root_node.exh.solution)

    def solver_step(self, node: Node) -> Node | None:
        new_nodes = node.splitting()
        self.__mip_state.num_of_branch += 1

        if new_nodes is not None:
            left_node, right_node = new_nodes
        else:
            while self.__stack:
                stack_node = self.__stack.pop()
                if self.__mip_state.primal_solution.objective is None or \
                        stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return stack_node
            return None

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
            self.__mip_state.num_of_infeasible_nodes += 1

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
            self.__mip_state.num_of_infeasible_nodes += 1

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
            self.__mip_state.num_of_infeasible_nodes += 2

            while self.__stack:
                stack_node = self.__stack.pop()
                if self.__mip_state.primal_solution.objective is None or \
                        stack_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return stack_node
            return None

    def start(self):
        graphes = []
        node = self.__stack.pop()

        graphes += [node.exh.graph]

        while node is not None:
            node = self.solver_step(node=node)

            if node is not None:
                graphes += [node.exh.graph]

                self.__mip_state.update_solution(
                    min(self.__stack + [node], key=lambda x: x.exh.solution.objective).exh.solution)
            elif self.__stack:
                self.__mip_state.update_solution(
                    min(self.__stack, key=lambda x: x.exh.solution.objective).exh.solution)

            print(f"primal value: {self.__mip_state.primal_solution.objective}\t" +
                  f"dual value: {self.__mip_state.dual_solution.objective}\t" +
                  f"number of branching: {self.__mip_state.num_of_branch}\t" +
                  f"number of infisible nodes: {self.__mip_state.num_of_infeasible_nodes}"
                  )

            if self.__mip_state.state == State.Converged:
                break

        self.__mip_state.on_end()

        return graphes

    def result(self) -> str:
        return self.__mip_state.__repr__()
