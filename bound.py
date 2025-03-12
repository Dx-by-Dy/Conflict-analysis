class Bound:
    def __init__(self, var_id, left, right):
        self.var_id = var_id
        self.left = left
        self.right = right

    def __str__(self):
        return f"Bound[id: {self.var_id}, left: {self.left}, right: {self.right}]"