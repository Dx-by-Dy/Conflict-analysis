


class Constraint:
    def __init__(self, index: int, lower_bound: float, upper_bound: float) -> None:
        from helpers.var import Var

        self.index = index
        self.lower = lower_bound
        self.upper = upper_bound
        self.info: dict[Var, float] = {}

    def add_var(self, var, coeff: float) -> None:
        self.info[var] = coeff

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
