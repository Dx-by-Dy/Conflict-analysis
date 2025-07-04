class Bound:
    def __init__(self, lower: float, upper: float):
        self.lower = lower
        self.upper = upper

    def copy(self):
        return Bound(
            lower=self.lower,
            upper=self.upper
        )

    def __repr__(self):
        return f"Bound {{lower: {self.lower}, upper: {self.upper}" + " }"

    def __eq__(self, other):
        return self.lower == other.lower and self.upper == other.upper


class BnBBranch:
    from helpers.var import Var

    def __init__(self, var: Var, left_bound: Bound, right_bound: Bound):
        self.var = var
        self.left_bound = left_bound
        self.right_bound = right_bound

    def __repr__(self):
        return f"BnBBranch: var= {self.var.__repr__()}, left_bound= {self.left_bound.__repr__()}, right_bound= {self.right_bound.__repr__()}"
