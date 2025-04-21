import highspy
from highspy import Highs
from math import ceil, floor


class Presolver:
    def __init__(self, h: highspy.Highs, general_vars_idx: list[int]) -> None:
        self.__is_infeasible = False
        self.__is_converged = False
        self.__converged_vars = {}
        self.__converged_vars_by_stages = {}
        self.__current_stage = 0
        self.__infeasible_var_idx = None

        lp = h.getLp()
        print(h.getLp().a_matrix_.start_)
        print(len(h.getLp().a_matrix_.start_))
        self.__constraints = [Constraint(constr_lb, constr_ub)
                            for constr_lb, constr_ub in zip(lp.row_lower_, lp.row_upper_)]
        self.__vars = [Var(var_idx, h.getVariables()[var_idx].name, lb, ub, var_idx in general_vars_idx)
                     for var_idx, (lb, ub) in enumerate(zip(lp.col_lower_, lp.col_upper_))]

        var_idx = 0
        old_constr_idx = -1
        for constr_idx, coeff in zip(lp.a_matrix_.index_, lp.a_matrix_.value_):
            if constr_idx <= old_constr_idx:
                var_idx += 1
            self.__constraints[constr_idx].add_coeff(var_idx, coeff)
            self.__vars[var_idx].add_constraint(constr_idx)
            old_constr_idx = constr_idx

    def get_converged_vars(self):
        return [self.__vars[var_idx] for var_idx in self.__converged_vars]

    def update_n_times(self, n: int) -> bool:
        for _ in range(n):
            self.__is_converged = not self.__update_all_vars()
        return self.__is_infeasible

    def __update_all_vars(self) -> bool:
        if self.__is_converged:
            return False

        self.__current_stage += 1
        have_changes = False
        for var in self.__vars:
            if var.index in self.__converged_vars:
                continue
            (conv, changes) = self.__update_lower_upper(var.index)
            if self.__is_infeasible:
                return False
            if conv:
                self.__converged_vars[var.index] = True

                if self.__current_stage in self.__converged_vars_by_stages:
                    self.__converged_vars_by_stages[self.__current_stage].append(var.index)
                else:
                    self.__converged_vars_by_stages[self.__current_stage] = [var.index]
            if changes:
                have_changes = changes
        return have_changes

    def __update_lower_upper(self, updating_var_idx: int) -> (bool, bool):
        have_changes = False
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
                if updating_var.update_upper((constraint.upper - min_another_vars_value) / var_coeff):
                    have_changes = True
                if updating_var.update_lower((constraint.lower - max_another_vars_value) / var_coeff):
                    have_changes = True

                new_upper = max_another_vars_value + var_coeff * updating_var.upper
                if new_upper < constraint.upper:
                    constraint.upper = new_upper
                    have_changes = True
                new_lower = min_another_vars_value + var_coeff * updating_var.lower
                if new_lower > constraint.lower:
                    constraint.lower = new_lower
                    have_changes = True
            else:
                if updating_var.update_upper((constraint.lower - max_another_vars_value) / var_coeff):
                    have_changes = True
                if updating_var.update_lower((constraint.upper - min_another_vars_value) / var_coeff):
                    have_changes = True

                new_upper = max_another_vars_value + var_coeff * updating_var.lower
                if new_upper < constraint.upper:
                    constraint.upper = new_upper
                    have_changes = True
                new_lower = min_another_vars_value + var_coeff * updating_var.upper
                if new_lower > constraint.lower:
                    constraint.lower = new_lower
                    have_changes = True

            if updating_var.upper < updating_var.lower or constraint.upper < constraint.lower:
                self.__is_infeasible = True
                self.__infeasible_var_idx = updating_var_idx
                return False, True

            if updating_var.is_conv():
                return True, have_changes

        return False, have_changes

    def __str__(self):
        text = "Presolver{"
        for constraint in self.__constraints:
            text += f"\n\tConstraint{{lower: {constraint.lower}, upper: {constraint.upper}}}: \n\t{{"
            for var_idx in constraint.vars_coeffs:
                var = self.__vars[var_idx]
                text += "\n\t\t" + f"var_index: {var_idx}, var_name: {var.name}, coeff: {constraint.vars_coeffs[var_idx]}, lb: {var.lower}, ub: {var.upper}"
            text += "\n\t}"

        text += f"\n\tconverged: {self.__is_converged} (stages: {self.__current_stage})"
        text += f"\n\tconverged vars (vars: {len(self.__converged_vars)}): {{"
        if len(self.__converged_vars) == 0:
            text += "}"
        else:
            for var_idx in self.__converged_vars.keys():
                var = self.__vars[var_idx]
                text += f"\n\t\tvar_index: {var_idx}, var_name: {var.name}, value: {var.lower}"
            text += "\n\t}"

            text += f"\n\tconverged vars by stage: {{"
            for (key, value) in self.__converged_vars_by_stages.items():
                text += f"\n\t\tstage: {key} {{"
                for var_idx in value:
                    var = self.__vars[var_idx]
                    text += f"\n\t\t\tvar_index: {var_idx}, var_name: {var.name}, value: {var.lower}"
                text += "\n\t\t}"
            text += "\n\t}"

        if self.__is_infeasible:
            var = self.__vars[self.__infeasible_var_idx]
            text += f"\n\tinfeasible var: \n\t\tvar_index: {var_idx}, var_name: {var.name}, lb: {var.lower}, ub: {var.upper}"
        else:
            text += f"\n\tinfeasible: {self.__is_infeasible}"
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
    def __init__(self, index: int, name:str, lower_bound: float, upper_bound: float, is_general: bool) -> None:
        self.index = index
        self.lower = lower_bound
        self.upper = upper_bound
        self.in_constraints = []
        self.general = is_general
        self.name = name

        self.convergence_tolerance = 1e-6

    def is_conv(self):
        return self.upper - self.lower <= self.convergence_tolerance

    def add_constraint(self, constr_idx: int) -> None:
        self.in_constraints.append(constr_idx)

    def update_upper(self, value: float) -> bool:
        if self.general and value != -float("inf") and value != float("inf"):
            value = floor(value)
            if value < self.upper:
                self.upper = value
                return True
        else:
            if value < self.upper:
                self.upper = value
                return True
        return False

    def update_lower(self, value: float) -> bool:
        if self.general and value != -float("inf") and value != float("inf"):
            value = ceil(value)
            if value > self.lower:
                self.lower = value
                return True
        else:
            if value > self.lower:
                self.lower = value
                return True
        return False

if __name__ == "__main__":
    #path = "test.lp"
    #path = "test.mps"
    #path = "test2.lp"
    path = "../../Downloads/benchmark/supportcase16.mps"
    h = Highs()
    h.readModel(path)
    h.silent()

    general = []
    for (var_idx, var_type) in enumerate(h.getLp().integrality_):
        if var_type == highspy.HighsVarType.kInteger:
            general.append(var_idx)

    presolver = Presolver(h, general)
    presolver.update_n_times(100)

    #print(presolver)
    for var in presolver.get_converged_vars():
        h.changeColBounds(var.index, var.lower, var.upper)
    #help(h)
    #help(h.getLp().a_matrix_)
    #print(h.getLp().a_matrix_.value_)
    #print(h.getLp().a_matrix_.start_)
    #print(h.getColEntries(0)[1])
    #print(h.getLp().offset_)
    #print(h.getLp().row_upper_[0])

    h.run()
    #list(map(lambda x: print(x), list(zip(h.getSolution().col_value, list(map(lambda x: x.name, h.getVariables()))))))
    print(h.getInfo().objective_function_value)