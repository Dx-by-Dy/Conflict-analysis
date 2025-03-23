class Bound:
    def __init__(self, var_id: int, left: int, right: int) -> None:
        self.var_id = var_id
        self.left = left
        self.right = right

    def concat(self, other):
        return Bound(self.var_id, max(self.left, other.left), min(self.right, other.right))

    def __str__(self):
        return f"Bound{{id: {self.var_id}, left: {self.left}, right: {self.right}}}"
