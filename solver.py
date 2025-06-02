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
        print(self.__mip_state.primal_solution.objective,
              self.__mip_state.dual_solution.objective)

        if self.__stack:
            self.__mip_state.update_solution(
                min(self.__stack, key=lambda x: x.exh.solution.objective).exh.solution)

        print(self.__mip_state.primal_solution.objective,
              self.__mip_state.dual_solution.objective)

        new_nodes = node.splitting()
        if new_nodes is not None:
            left_node, right_node = new_nodes
        else:
            if self.__stack:
                return self.__stack.pop()
            else:
                return None

        if left_node.is_feasible() and right_node.is_feasible():
            if left_node.exh.solution.objective < right_node.exh.solution.objective:
                if not right_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None:
                        self.__stack.append(right_node)
                    elif right_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        self.__stack.append(right_node)
                else:
                    self.__mip_state.update_solution(right_node.exh.solution)

                if not left_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None:
                        return left_node
                    elif left_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        return left_node
                else:
                    self.__mip_state.update_solution(left_node.exh.solution)

                if self.__stack:
                    return self.__stack.pop()
                return None
            else:
                if not left_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None:
                        self.__stack.append(left_node)
                    elif left_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        self.__stack.append(left_node)
                else:
                    self.__mip_state.update_solution(left_node.exh.solution)

                if not right_node.exh.solution.is_primal:
                    if self.__mip_state.primal_solution.objective is None:
                        return right_node
                    elif right_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                        return right_node
                else:
                    self.__mip_state.update_solution(right_node.exh.solution)

                if self.__stack:
                    return self.__stack.pop()
                return None

        elif left_node.is_feasible() and not right_node.is_feasible():
            if not left_node.exh.solution.is_primal:
                if self.__mip_state.primal_solution.objective is None:
                    return left_node
                elif left_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return left_node
            else:
                self.__mip_state.update_solution(left_node.exh.solution)

            if self.__stack:
                return self.__stack.pop()
            return None

        elif not left_node.is_feasible() and right_node.is_feasible():
            if not right_node.exh.solution.is_primal:
                if self.__mip_state.primal_solution.objective is None:
                    return right_node
                elif right_node.exh.solution.objective < self.__mip_state.primal_solution.objective:
                    return right_node
            else:
                self.__mip_state.update_solution(right_node.exh.solution)

            if self.__stack:
                return self.__stack.pop()
            return None

        else:
            if self.__stack:
                return self.__stack.pop()
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

            if self.__mip_state.state == State.Converged:
                return

        self.__mip_state.on_end()

    def result(self) -> str:
        return self.__mip_state.__repr__()


if __name__ == "__main__":
    from highspy import Highs

    path = "test.lp"

    sl = Solver(path)
    sl.start()
    print(sl.result())

    h = Highs()
    h.readModel(path)
    h.silent()

    h.run()
    print(h.getSolution().col_value)
    print(h.getInfo().objective_function_value)
