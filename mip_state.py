class MipState:
    def __init__(self, eps_result) -> None:
        self.__primal_value = float("inf")
        self.__primal_solution = []
        self.__dual_value = -float("inf")
        self.__dual_solution = []
        self.__eps_result = eps_result

        self.__num_of_branch = 0
        self.__num_of_infeasibility_nodes = 0
        self.__state_of_infeasibility_nodes = []

    def add_branch(self) -> None:
        self.__num_of_branch += 1

    def add_infeasibility_node(self, lower_bound: list[float], upper_bound: list[float]) -> None:
        self.__num_of_infeasibility_nodes += 1
        self.__state_of_infeasibility_nodes.append((lower_bound, upper_bound))

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
        text = "MipState{\n\tprimal value: " + str(self.__primal_value)
        if len(self.__primal_solution) < 20:
            text += "\n\tprimal solution: " + str(self.__primal_solution)
        else:
            text += "\n\tprimal solution: [" + ", ".join(map(str, self.__primal_solution[:10])) + ", ..., " + ", ".join(map(str, self.__primal_solution[-10:])) + "]"
        text += "\n\tdual value: " + str(self.__dual_value)
        if len(self.__dual_solution) < 20:
            text += "\n\tdual solution: " + str(self.__dual_solution)
        else:
            text += "\n\tdual solution: [" + ", ".join(map(str, self.__dual_solution[:10])) + ", ..., " + ", ".join(map(str, self.__dual_solution[-10:])) + "]"
        text += "\n\tnum of infeasibility nodes: " + str(self.__num_of_infeasibility_nodes)
        text += "\n\tbounds of infeasible bodes: " + str(self.__state_of_infeasibility_nodes)
        text += "\n}}"
        return text
