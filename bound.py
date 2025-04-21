class Bound:
    def __init__(self, var_id: int, left: int | float, right: int | float) -> None:
        self.var_id = var_id
        self.left = left
        self.right = right

    def concat(self, other):
        return Bound(self.var_id, max(self.left, other.left), min(self.right, other.right))

    def solution_accept(self, solution: list[float]):
        return self.left <= solution[self.var_id] <= self.right

    def __repr__(self):
        return f"Bound{{id: {self.var_id}, left: {self.left}, right: {self.right}}}"
