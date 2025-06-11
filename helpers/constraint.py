from math import isinf
from bound import Bound
from helpers.var import Var


class Constraint:
    def __init__(self, index: int, lower_bound: float, upper_bound: float) -> None:
        self.index = index
        self.lower = lower_bound
        self.upper = upper_bound
        self.info: dict[Var, float] = {}

    def add_var(self, var: Var, coeff: float) -> None:
        self.info[var] = coeff

    def update_lower_upper_by_activity(self) -> None:
        activity = self.activity()
        if activity[0] > self.lower:
            self.lower = activity[0]
        if activity[1] < self.upper:
            self.upper = activity[1]

    def activity(self, without_var: Var | None = None) -> list[float, float]:
        activity = [0, 0]
        for (var, coeff) in self.info.items():
            if without_var is not None and var == without_var:
                continue
            var_activity = minmax(
                var.lower * coeff, var.upper * coeff)
            activity[0] += var_activity[0]
            activity[1] += var_activity[1]
        return activity

    def update_vars(self) -> list[Var] | None:
        vars_for_update: dict[Var, Bound] = {}

        for (var, coeff) in self.info.items():
            activity_without_var = self.activity(without_var=var)
            if coeff > 0:
                new_bound = var.update_lower_upper(
                    (self.lower - activity_without_var[1]) / coeff, (self.upper - activity_without_var[0]) / coeff)
            else:
                new_bound = var.update_lower_upper(
                    (self.upper - activity_without_var[0]) / coeff, (self.lower - activity_without_var[1]) / coeff)
            if new_bound is None:
                continue
            if new_bound.lower > new_bound.upper:
                return None
            vars_for_update[var] = new_bound

        vars_changed = []
        for var, bound in vars_for_update.items():
            var.lower = bound.lower
            var.upper = bound.upper
            vars_changed.append(var)

        if len(vars_for_update) > 0:
            self.update_lower_upper_by_activity()

        return vars_changed

    def copy_empty(self):
        return Constraint(
            index=self.index,
            lower_bound=self.lower,
            upper_bound=self.upper
        )

    def __repr__(self):
        line = ""
        for var in self.info:
            coeff = self.info[var]
            if line == "":
                line += f"{coeff} {var.name} " if coeff > 0 else f"-{str(coeff)[1:]} {var.name} "
            else:
                line += f"+ {coeff} {var.name} " if coeff > 0 else f"- {str(coeff)[1:]} {var.name} "

        return f"Constraint({self.index}): {self.lower} ≤ {line}≤ {self.upper}\n"


def minmax(a: float, b: float) -> tuple[float, float]:
    return (a, b) if a <= b else (b, a)
