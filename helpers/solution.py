from bound import BnBCut, Bound
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
