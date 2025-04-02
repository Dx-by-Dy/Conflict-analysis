import highspy


class Presolver:
    def __init__(self, lp: highspy.HighsLp, general_vars_idx: list[int]) -> None:
        self.__is_infeasible = False
        self.__infeasible_var_idx = None
        self.__constraints = [Constraint(constr_lb, constr_ub)
                            for constr_lb, constr_ub in zip(lp.row_lower_, lp.row_upper_)]
        self.__vars = [Var(var_idx, lb, ub, var_idx in general_vars_idx)
                     for var_idx, (lb, ub) in enumerate(zip(lp.col_lower_, lp.col_upper_))]

        var_idx = 0
        old_constr_idx = -1
        for constr_idx, coeff in zip(lp.a_matrix_.index_, lp.a_matrix_.value_):
            if constr_idx <= old_constr_idx:
                var_idx += 1
            self.__constraints[constr_idx].add_coeff(var_idx, coeff)
            self.__vars[var_idx].add_constraint(constr_idx)
            old_constr_idx = constr_idx

    def update_n_times(self, n: int) -> bool:
        for _ in range(n):
            self.__update_all_vars()
        return self.__is_infeasible

    def __update_all_vars(self):
        for var_idx in range(len(self.__vars)):
            self.__update_lower_upper(var_idx)

    def __update_lower_upper(self, updating_var_idx: int) -> None:
        if self.__is_infeasible:
            return

        updating_var = self.__vars[updating_var_idx]
        for constraint in self.__constraints:
            if updating_var_idx not in constraint.vars_coeffs:
                continue

            max_another_vars_value = 0
            min_another_vars_value = 0

            var_coeff = constraint.vars_coeffs[updating_var_idx]
            for var_idx in constraint.vars_coeffs.keys():
                if var_idx == updating_var_idx:
                    continue

                var = self.__vars[var_idx]
                coeff = constraint.vars_coeffs[var_idx]
                if coeff > 0:
                    max_another_vars_value += coeff * var.upper
                    min_another_vars_value += coeff * var.lower
                else:
                    max_another_vars_value += coeff * var.lower
                    min_another_vars_value += coeff * var.upper

            if var_coeff > 0:
                updating_var.update_upper((constraint.upper - min_another_vars_value) / var_coeff)
                updating_var.update_lower((constraint.lower - max_another_vars_value) / var_coeff)

                constraint.upper = min(constraint.upper, max_another_vars_value + var_coeff * updating_var.upper)
                constraint.lower = max(constraint.lower, min_another_vars_value + var_coeff * updating_var.lower)
            else:
                updating_var.update_upper((constraint.lower - max_another_vars_value) / var_coeff)
                updating_var.update_lower((constraint.upper - min_another_vars_value) / var_coeff)

                constraint.upper = min(constraint.upper, max_another_vars_value + var_coeff * updating_var.lower)
                constraint.lower = max(constraint.lower, min_another_vars_value + var_coeff * updating_var.upper)

            if updating_var.upper < updating_var.lower or constraint.upper < constraint.lower:
                self.is_infeasible = True
                self.infeasible_var_idx = updating_var_idx
                return

    def __str__(self):
        text = "Presolver{"
        for constraint in self.__constraints:
            text += f"\n\tConstraint{{lower: {constraint.lower}, upper: {constraint.upper}}}: "
            for var_idx in constraint.vars_coeffs:
                var = self.__vars[var_idx]
                text += "\n\t\t" + f"var_index: {var_idx}, coeff: {constraint.vars_coeffs[var_idx]}, lb: {var.lower}, ub: {var.upper}"
            text += "\n\t}"
        text += f"\n\tinfeasible: {self.is_infeasible}"
        text += "\n}"
        return text

class Constraint:
    def __init__(self, lower_bound: float, upper_bound: float) -> None:
        self.lower = lower_bound
        self.upper = upper_bound
        self.vars_coeffs: dict[int, float] = {}

    def add_coeff(self, var_idx: int, coeff: float) -> None:
        self.vars_coeffs[var_idx] = coeff

class Var:
    def __init__(self, index: int, lower_bound: float, upper_bound: float, is_general: bool) -> None:
        self.index = index
        self.lower = lower_bound
        self.upper = upper_bound
        self.in_constraints = []
        self.general = is_general

    def add_constraint(self, constr_idx: int) -> None:
        self.in_constraints.append(constr_idx)

    def update_upper(self, value: float) -> None:
        if self.general and value != -float("inf") and value != float("inf"):
            self.upper = min(self.upper, value // 1)
        else:
            self.upper = min(self.upper, value)

    def update_lower(self, value: float) -> None:
        if self.general and value != -float("inf") and value != float("inf"):
            self.lower = max(self.lower, value // 1)
        else:
            self.lower = max(self.lower, value)
