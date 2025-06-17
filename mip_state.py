from extended_highs_model import Solution
from enum import Enum


class State(Enum):
    InSolving = 0
    Converged = 1
    Infeasible = 2


class MipState:
    def __init__(self, convergence_tolerance: float = 1e-4) -> None:
        self.state = State.InSolving
        self.primal_solution: Solution = Solution()
        self.dual_solution: Solution = Solution()
        self.convergence_tolerance = convergence_tolerance

        self.number_of_branches = 0
        self.number_of_infeasible_nodes = 0
        self.number_of_relaxations = 0

    def __check_convergency(self) -> None:
        if self.primal_solution.objective is None or self.dual_solution.objective is None:
            return
        if self.primal_solution.objective <= self.dual_solution.objective or \
            (self.primal_solution.objective - self.dual_solution.objective) \
                / abs(self.dual_solution.objective) < self.convergence_tolerance:
            self.dual_solution.copy_from_other(self.primal_solution)
            self.state = State.Converged
            return

    def on_end(self) -> None:
        if self.primal_solution.objective is None:
            self.state = State.Infeasible
            self.dual_solution = Solution()
            return
        if self.state == State.InSolving:
            self.state = State.Converged
            return

    def update_solution(self, solution: Solution) -> None:
        if solution.is_primal:
            if self.primal_solution.objective is None or \
                    solution.objective < self.primal_solution.objective:
                self.primal_solution.copy_from_other(solution)
        else:
            self.dual_solution.copy_from_other(solution)
        self.__check_convergency()

    def __repr__(self):
        if self.primal_solution.objective is None:
            text = f"MipState [{self.state}] {{\n\tprimal value: None"
        else:
            text = f"MipState [{self.state}] {{\n\tprimal value: {self.primal_solution.objective}"
            if len(self.primal_solution.value[1]) < 20:
                text += "\n\tprimal solution: " + \
                    str(self.primal_solution.value[1])
            else:
                text += "\n\tprimal solution: [" + ", ".join(map(str, self.primal_solution.value[1][:10])) + ", ..., " + ", ".join(
                    map(str, self.primal_solution.value[1][-10:])) + "]"
        if self.dual_solution.objective is None:
            text += "\n\tdual value: None"
        else:
            text += "\n\tdual value: " + str(self.dual_solution.objective)
            if len(self.dual_solution.value[1]) < 20:
                text += "\n\tdual solution: " + \
                    str(self.dual_solution.value[1])
            else:
                text += "\n\tdual solution: [" + ", ".join(map(str, self.dual_solution.value[1][:10])) + ", ..., " + ", ".join(
                    map(str, self.dual_solution.value[1][-10:])) + "]"
        text += f"\n\tnumber of branches: {self.number_of_branches}"
        text += f"\n\tnumber of infisible nodes: {self.number_of_infeasible_nodes}"
        text += f"\n\tnumber of relaxations: {self.number_of_relaxations}"
        text += "\n}"
        return text
