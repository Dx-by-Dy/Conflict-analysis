from bound import Bound

class Node:
    def __init__(self, bounds: list[Bound], solution: list[float], dual_value: float) -> None:
        self.bounds = bounds
        self.solution = solution
        self.dual_value = dual_value

    def add_bound(self, bound: Bound) -> list[Bound]:
        return [self.bounds[i].concat(bound) if i == bound.var_id else self.bounds[i] for i in range(len(self.bounds))]

    def __str__(self):
        text = "Node{\n\tBounds:\n"
        for bound in self.bounds:
            text += "\t\t" + str(bound) + "\n"
        text += "\tSolution:\n\t\t" + str(self.solution) + "\n"
        text += "\tDual value:\n\t\t" + str(self.dual_value) + "\n}"
        return text
