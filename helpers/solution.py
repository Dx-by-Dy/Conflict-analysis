from math import isinf
import highspy
from bound import BnBBranch, Bound
from helpers.var import Var


class Solution:
    def __init__(self,
                 objective: float | None = None,
                 value: tuple[list[Var], list[float]] | None = None,
                 primal_tolerance: float = 1e-9):
        self.value = value
        self.objective = objective
        self.primal_tolerance = primal_tolerance
        self.status: highspy.HighsModelStatus | None = None
        self.is_primal: bool | None = self.__is_primal()

    def set_solution(self, objective: float, value: tuple[list[Var], list[float]], status: highspy.HighsModelStatus) -> bool:
        if isinf(objective):
            objective = None

        changed = self.objective is not None and ((objective is None and self.objective is not None) or abs(
            objective - self.objective) >= 1e-4)

        self.value = value
        self.objective = objective
        self.status = status
        self.is_primal = self.__is_primal()

        return changed

    def copy_from_other(self, other):
        self.value = (other.value[0].copy(), other.value[1].copy())
        self.objective = other.objective
        self.primal_tolerance = other.primal_tolerance
        self.is_primal = other.is_primal
        self.status = other.status

    def __is_primal(self) -> bool | None:
        if self.value is None or not self.is_feasible():
            return None
        for var, val in zip(self.value[0], self.value[1]):
            if var.is_general and abs(val - round(val)) >= self.primal_tolerance:
                return False
        return True

    def is_feasible(self) -> bool:
        return self.status == highspy.HighsModelStatus.kOptimal

    def is_infeasible(self) -> bool:
        return self.status == highspy.HighsModelStatus.kInfeasible

    def find_bnb_branch(self) -> BnBBranch:
        def heuristic(x: float): return abs(x % 1 - 0.5)
        result_var: Var | None = None
        min_heuristic_value = 1
        result_val: int | None = None

        for var, val in zip(self.value[0], self.value[1]):
            # if not var.is_general or var.is_conv():
            #     continue
            # temp_heuristics = heuristic(val)
            # if temp_heuristics < min_heuristic_value and temp_heuristics < 0.5 - self.primal_tolerance:
            #     result_var = var
            #     min_heuristic_value = temp_heuristics
            #     result_val = int(val)

            if not var.is_general or var.is_conv() or val % 1 < self.primal_tolerance:
                continue
            result_var = var
            result_val = int(val)
            break

        if result_var is not None:
            return BnBBranch(
                var=result_var,
                left_bound=Bound(lower=result_var.lower, upper=result_val),
                right_bound=Bound(lower=result_val + 1, upper=result_var.upper)
            )
        else:
            raise Exception("Can't find the variavle for branching!")
