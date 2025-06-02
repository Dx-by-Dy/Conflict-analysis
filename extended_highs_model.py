import highspy

from bound import BnBCut, Bound
from helpers.constraint import Constraint
from helpers.var import Var


class Solution:
    def __init__(self, objective: float | None = None,
                 value: tuple[list[Var], list[float]] | None = None,
                 primal_tolerance: float = 1e-9):
        self.value = value
        self.objective = objective
        self.primal_tolerance = primal_tolerance
        self.feasible: bool | None = None
        self.is_primal: bool | None = self.__is_primal()

    def set_solution(self, objective: float, value: tuple[list[Var], list[float]], feasible: bool) -> None:
        self.value = value
        self.objective = objective
        self.feasible = feasible
        self.is_primal = self.__is_primal()

    def copy_from_other(self, other):
        self.value = (other.value[0].copy(), other.value[1].copy())
        self.objective = other.objective
        self.primal_tolerance = other.primal_tolerance
        self.is_primal = other.is_primal
        self.feasible = other.feasible

    def __is_primal(self) -> bool | None:
        if self.value is None or self.feasible != True:
            return None
        for var, val in zip(self.value[0], self.value[1]):
            if var.is_general and abs(val - round(val)) >= self.primal_tolerance:
                return False
        return True

    def find_cut(self) -> BnBCut | None:
        def heuristic(x: float): return abs(x % 1 - 0.5)
        result_var: Var | None = None
        min_heuristic_value = 1
        result_val: int | None = None

        for var, val in zip(self.value[0], self.value[1]):
            if not var.is_general:
                continue
            temp_heuristics = heuristic(val)
            if temp_heuristics < min_heuristic_value and temp_heuristics < 0.5 - self.primal_tolerance:
                result_var = var
                min_heuristic_value = temp_heuristics
                result_val = int(val)

        if result_var is not None:
            if abs(result_val - result_var.lower) < self.primal_tolerance:
                result_var.lower = result_val
            if abs(result_val + 1 - result_var.upper) < self.primal_tolerance:
                result_var.upper = result_val + 1

            print(
                f"var: {result_var}, var value: {self.value[1][result_var.index]}")

            return BnBCut(
                var=result_var,
                left_bound=Bound(lower=result_var.lower, upper=result_val),
                right_bound=Bound(lower=result_val + 1, upper=result_var.upper)
            )
        else:
            return None


class ExtendedHighsModel(highspy.Highs):
    def __init__(self, path_to_problem: str | None = None, primal_tolerance: float = 1e-9):

        super().__init__()
        self.silent()

        self.vars: list[Var] = []
        self.constraints: list[Constraint] = []
        self.solution: Solution = Solution(primal_tolerance=primal_tolerance)

        if path_to_problem is None:
            return

        self.readModel(path_to_problem)
        self.presolve()

        lp = self.getLp()
        for var_idx, (var_type, var_name, var_lower, var_upper) in enumerate(zip(lp.integrality_, lp.col_names_, lp.col_lower_, lp.col_upper_)):
            self.vars.append(
                Var(
                    index=var_idx,
                    name=var_name,
                    lower_bound=var_lower,
                    upper_bound=var_upper,
                    is_general=var_type == highspy.HighsVarType.kInteger,
                )
            )

        for constr_idx, (constr_lower, constr_upper) in enumerate(zip(lp.row_lower_, lp.row_upper_)):
            self.constraints.append(
                Constraint(
                    index=constr_idx,
                    lower_bound=constr_lower,
                    upper_bound=constr_upper
                )
            )

        const_idx_and_value = list(
            zip(lp.a_matrix_.index_, lp.a_matrix_.value_)
        )
        for var_idx in range(len(lp.a_matrix_.start_) - 1):
            for idx in range(lp.a_matrix_.start_[var_idx], lp.a_matrix_.start_[var_idx + 1]):
                constr_idx, coeff = const_idx_and_value[idx]
                self.constraints[constr_idx].add_var(self.vars[var_idx], coeff)
                self.vars[var_idx].add_constraint(self.constraints[constr_idx])

    def copy(self):

        res = ExtendedHighsModel()
        res.passModel(self.getModel())
        res.setBasis(self.getBasis())

        for constr in self.constraints:
            res.constraints.append(constr.copy_empty())

        for var in self.vars:
            res.vars.append(var.copy_empty())

        for constr in self.constraints:
            nconstr = res.constraints[constr.index]
            for var in constr.info:
                nvar = res.vars[var.index]
                nconstr.add_var(nvar, constr.info[var])
                nvar.add_constraint(nconstr)

        return res

    def set_consistent(self):
        for var in self.vars:
            self.setContinuous(var.index)

        self.run()
        self.solution.set_solution(objective=self.getInfo().objective_function_value,
                                   value=(
                                       self.vars, self.getSolution().col_value),
                                   feasible=self.getModelStatus() == highspy.HighsModelStatus.kOptimal)

        for var in self.vars:
            if var.is_general:
                self.setInteger(var.index)

    def get_var(self, index: int) -> Var:
        return self.vars[index]

    def __repr__(self):
        text = "ExtendedHighsModel {\n"

        text += "\tVars {\n"
        for var in self.vars:
            text += "\t\t" + var.__repr__()
        text += "\t}\n\n"

        text += "\tConstaints {\n"
        for constr in self.constraints:
            text += "\t\t" + constr.__repr__()
        text += "\t}\n"

        text += "}\n"
        return text


if __name__ == "__main__":
    ex = ExtendedHighsModel("test.lp")

    ex_copy = ex.copy()

    print(ex)
    print(ex_copy)

    # a = {ex.get_var(0): 1}

    print(ex_copy.get_var(0) == ex.get_var(0))
    print(id(ex_copy.get_var(0)), id(ex.get_var(0)))

    v = list(ex.constraints[1].info.keys())[0]
    v.lower = -100

    # print(ex)
    # print(ex_copy)
