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
        left_bound: Bound | None = None
        right_bound: Bound | None = None

        for var, val in zip(self.value[0], self.value[1]):
            if not var.is_general or var.is_conv() or min(val % 1, 1 - val % 1) < self.primal_tolerance:
                continue
            temp_heuristics = heuristic(val)
            if temp_heuristics < min_heuristic_value and temp_heuristics < 0.5 - self.primal_tolerance:
                result_var = var
                min_heuristic_value = temp_heuristics

                if abs(val - var.lower) <= self.primal_tolerance and not isinf(var.lower) and not isinf(var.upper):
                    bound = (var.lower + var.upper) // 2
                    left_bound = Bound(lower=var.lower + 1, upper=bound)
                    right_bound = Bound(lower=bound + 1, upper=var.upper)
                elif abs(val - var.upper) <= self.primal_tolerance and not isinf(var.lower) and not isinf(var.upper):
                    bound = (var.lower + var.upper) // 2 - 1
                    left_bound = Bound(lower=var.lower, upper=bound)
                    right_bound = Bound(lower=bound + 1, upper=var.upper - 1)
                else:
                    if var.upper - var.lower > 10 and not isinf(var.lower) and not isinf(var.upper):
                        bound = (var.lower + var.upper) // 2
                    else:
                        bound = int(val)
                    left_bound = Bound(lower=var.lower, upper=bound)
                    right_bound = Bound(lower=bound + 1, upper=var.upper)

                # print(bound, val, var)
                # print(left_bound, right_bound)

                break

        if result_var is not None:
            return BnBBranch(
                var=result_var,
                left_bound=left_bound,
                right_bound=right_bound
            )
        else:
            raise Exception("Can't find the variavble for branching!")
