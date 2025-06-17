from math import ceil, floor, isinf

from bound import Bound


class Var:
    def __init__(self, index: int, name: str, lower_bound: float, upper_bound: float,
                 is_general: bool, convergence_tolerance: float = 1e-6) -> None:
        from helpers.constraint import Constraint

        self.index: int = index
        self.lower: float = lower_bound
        self.upper: float = upper_bound
        self.in_constraints: list[Constraint] = []
        self.is_general: bool = is_general
        self.name: str = name
        self.convergence_tolerance: float = convergence_tolerance

    def is_conv(self) -> bool:
        return abs(self.upper - self.lower) <= self.convergence_tolerance

    def value(self) -> float | None:
        if not self.is_conv():
            return None
        if self.is_general:
            return self.lower
        return (self.lower + self.upper) / 2

    def add_constraint(self, constr) -> None:
        self.in_constraints.append(constr)

    def remove_last_constraint(self) -> None:
        self.in_constraints.pop()

    def update_lower_upper(self, new_lower: float, new_upper: float) -> Bound | None:
        updated_lower = None
        if self.is_general and not isinf(new_lower):
            new_lower = ceil(new_lower)
            if new_lower > self.lower:
                updated_lower = new_lower
        else:
            if new_lower > self.lower:
                updated_lower = new_lower

        updated_upper = None
        if self.is_general and not isinf(new_upper):
            new_upper = floor(new_upper)
            if new_upper < self.upper:
                updated_upper = new_upper
        else:
            if new_upper < self.upper:
                updated_upper = new_upper

        if updated_lower is None and updated_upper is None:
            return None
        if updated_lower is None:
            updated_lower = self.lower
        if updated_upper is None:
            updated_upper = self.upper

        return Bound(updated_lower, updated_upper)

    def is_valid_update(self, new_lower: float, new_upper: float) -> bool:
        if self.is_general and not isinf(new_lower):
            new_lower = ceil(new_lower)
            if new_lower > self.lower:
                return True
        else:
            if new_lower > self.lower:
                return True

        if self.is_general and not isinf(new_upper):
            new_upper = floor(new_upper)
            if new_upper < self.upper:
                return True
        else:
            if new_upper < self.upper:
                return True

        return False

    def copy_empty(self):
        return Var(
            index=self.index,
            name=self.name,
            lower_bound=self.lower,
            upper_bound=self.upper,
            is_general=self.is_general,
            convergence_tolerance=self.convergence_tolerance
        )

    def __eq__(self, other):
        return self.index == other.index

    def __hash__(self):
        return hash(self.index)

    def __repr__(self):
        if self.is_conv():
            return f"Var({self.index}) [{self.name}] {{ value: {self.value()}, integer: {self.is_general}" + " }"
        else:
            return f"Var({self.index}) [{self.name}] {{ lb: {self.lower}, ub: {self.upper}, integer: {self.is_general}" + " }"
