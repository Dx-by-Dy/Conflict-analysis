class MipState:
    def __init__(self, eps_result) -> None:
        self.__primal_value = float("inf")
        self.__primal_solution = []
        self.__dual_value = -float("inf")
        self.__dual_solution = []
        self.__eps_result = eps_result

    def update_primal_solution(self, primal_value: float, primal_solution: list[float]) -> None:
        if primal_value < self.__primal_value:
            self.__primal_value = primal_value
            self.__primal_solution = primal_solution

    def update_dual_solution(self, dual_value: float, dual_solution: list[float]) -> None:
        self.__dual_value = dual_value
        self.__dual_solution = dual_solution

    def converged(self) -> bool:
        if self.__primal_value <= self.__dual_value:
            return True
        return (self.__primal_value - self.__dual_value) / abs(self.__dual_value) < self.__eps_result

    def primal_value(self) -> float:
        return self.__primal_value

    def primal_solution(self) -> list[float]:
        return self.__primal_solution

    def dual_value(self) -> float:
        return self.__dual_value

    def dual_solution(self) -> list[float]:
        return self.__dual_solution

    def __str__(self) -> str:
        return (f"MipState{{\n\tprimal value: {self.__primal_value} \n\tprimal solution: {self.__primal_solution} \
                \n\tdual value: {self.__dual_value} \n\tdual solution: {self.__dual_solution}\n}}")
