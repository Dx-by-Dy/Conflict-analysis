from extended_highs_model import Solution
from enum import Enum, auto
from node import Branchability, Node


class BranchabilityStatistic:
    def __init__(self):
        self.statistic: dict[Branchability, int] = {}
        for item in list(Branchability):
            self.statistic[item] = 0

    def add(self, item: Branchability) -> None:
        self.statistic[item] += 1

    def __repr__(self, tabs: int = 0):
        text = "\t" * tabs + "BranchabilityStatistic {\n"
        for item, value in self.statistic.items():
            text += "\t" * tabs + f"\t{item}: {value}\n"
        text += "\t" * tabs + "}"
        return text


class State(Enum):
    InSolving = auto()
    Converged = auto()
    Infeasible = auto()


class MipState:
    def __init__(self, convergence_tolerance: float) -> None:
        self.state = State.InSolving
        self.primal_solution: Solution = Solution()
        self.dual_solution: Solution = Solution()
        self.convergence_tolerance = convergence_tolerance

        self.number_of_branches = 0
        self.branchability_statistic = BranchabilityStatistic()
        self.number_of_relaxations = 0
        self.number_of_non_trivial_graph_cuts = 0
        self.number_of_objective_changes = 0
        self.number_of_resolved_nodes = 0

    def __check_convergency(self) -> None:
        if self.primal_solution.objective is None or self.dual_solution.objective is None:
            return
        if self.primal_solution.objective <= self.dual_solution.objective or \
            (self.primal_solution.objective - self.dual_solution.objective) \
                / max(abs(self.dual_solution.objective), abs(self.primal_solution.objective)) < self.convergence_tolerance:
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

    def check_node(self, node: Node) -> bool:
        if self.primal_solution.objective is None:
            return True
        if node.exh.solution.objective is None or node.exh.solution.objective > self.primal_solution.objective:
            return False
        return (self.primal_solution.objective - node.exh.solution.objective) \
            / max(abs(self.primal_solution.objective), abs(node.exh.solution.objective)) > self.convergence_tolerance

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
        text += f"\n\tnumber of relaxations: {self.number_of_relaxations}"
        text += f"\n\tnumber of non trivial graph cuts: {self.number_of_non_trivial_graph_cuts}"
        text += f"\n\tnumber of objective changes: {self.number_of_objective_changes}"
        text += f"\n\tnumber of resolved nodes: {self.number_of_resolved_nodes}"
        text += "\n" + self.branchability_statistic.__repr__(1)
        text += "\n}"
        return text
