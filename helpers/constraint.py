from math import isinf


class Constraint:
    from helpers.var import Var

    def __init__(self, index: int, lower_bound: float, upper_bound: float) -> None:
        from helpers.var import Var

        self.index = index
        self.lower = lower_bound
        self.upper = upper_bound
        self.info: dict[Var, float] = {}

    def add_var(self, var: Var, coeff: float) -> None:
        self.info[var] = coeff

    def update_lower_upper_by_activity(self, activity: list[float, float]) -> bool:
        have_changes = False
        if activity[0] > self.lower:
            self.lower = activity[0]
            have_changes = True
        if activity[1] < self.upper:
            self.upper = activity[1]
            have_changes = True
        return have_changes

    def activity(self, without_var: Var | None = None) -> list[float, float]:
        activity = [0, 0]
        for (var, coeff) in self.info.items():
            if var == without_var:
                continue
            var_activity = minmax(
                var.lower * coeff, var.upper * coeff)
            activity[0] += var_activity[0]
            activity[1] += var_activity[1]
        return activity

    def update_vars(self) -> tuple[list[Var], bool] | None:
        vars_changed = []

        for (var, coeff) in self.info.items():
            var_changed = False
            var_activity = minmax(
                var.lower * coeff, var.upper * coeff)
            activity_without_var = self.activity(without_var=var)
            if coeff > 0:
                var_changed |= var.update_lower(
                    (self.lower - activity_without_var[1]) / coeff)
                var_changed |= var.update_upper(
                    (self.upper - activity_without_var[0]) / coeff)
            else:
                var_changed |= var.update_upper(
                    (self.lower - activity_without_var[1]) / coeff)
                var_changed |= var.update_lower(
                    (self.upper - activity_without_var[0]) / coeff)
            var_activity = minmax(
                var.lower * coeff, var.upper * coeff)
            activity = [activity_without_var[0] + var_activity[0],
                        activity_without_var[1] + var_activity[1]]

            if var_changed:
                vars_changed.append(var)

            if var.lower > var.upper:
                return None

            constr_changed = self.update_lower_upper_by_activity(activity)
        return vars_changed, constr_changed

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
