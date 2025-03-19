import random

import highspy
from bound import Bound
from mip_state import MipState
from stack_item import StackItem

class BnB:
    def __init__(self, path: str, eps_result: float = 1e-6, eps_integer: float = 1e-18, max_var_value: int = 10 ** 3) -> None:
        self.__solver = highspy.Highs()
        self.__solver.readModel(path)
        self.__solver.silent()
        self.__max_var_value = max_var_value

        self.__generalize = self.__generalize()
        self.__mip_state = MipState(eps_result)
        self.__eps_integer = eps_integer
        self.__stack = []

        bounds = []
        for i in range(self.__solver.getNumCol()):
            bounds.append(Bound(i, 0, self.__max_var_value))
            self.__solver.changeColBounds(i, 0, self.__max_var_value)

        self.__solver.run()

        if self.__solver.getModelStatus().value != 7:
            self.__stopped = True
        else:
            self.__stopped = False
            objective_function_value = self.__solver.getInfo().objective_function_value
            solution = self.__solver.getSolution().col_value
            self.__mip_state.update_dual_solution(objective_function_value, solution)
            if self.__check_on_primal(solution):
                self.__stopped = True
                self.__mip_state.update_primal_solution(objective_function_value, solution)
            else:
                self.__stack = [StackItem(bounds, solution, objective_function_value)]

    def __check_on_primal(self, dual_solution: list[float]) -> bool:
        for i in self.__generalize:
            if abs(dual_solution[i] - (dual_solution[i] // 1)) > self.__eps_integer:
                return False
        return True

    def __generalize(self):
        generalize = []
        for i in range(self.__solver.getNumCol()):
            if self.__solver.getColIntegrality(i)[1].value == 1:
                generalize.append(i)
                self.__solver.setContinuous(i)
        return generalize

    def result(self) -> None | MipState:
        if self.__stopped:
            return self.__mip_state
        else:
            print("Not ready")
            return None

    def start(self) -> None:
        if self.__stopped:
            return

        stack_item = self.__stack.pop()
        while stack_item is not None:
            #print(self.__mip_state.dual_value(), len(stack_item.bounds))
            #print(stack_item.solution)
            left_bound, right_bound = self.__find_cut(stack_item)

            left_solver = highspy.Highs()
            left_solver.passModel(self.__solver.getModel())
            left_solver.silent()
            left_bounds = stack_item.add_bound(left_bound)
            # left_solver.changeColBounds(left_bound.var_id, left_bound.left, left_bound.right)

            right_solver = highspy.Highs()
            right_solver.passModel(self.__solver.getModel())
            right_solver.silent()
            right_bounds = stack_item.add_bound(right_bound)
            # right_solver.changeColBounds(right_bound.var_id, right_bound.left, right_bound.right)
            for i in range(len(stack_item.bounds)):
                left_solver.changeColBounds(left_bounds[i].var_id, left_bounds[i].left, left_bounds[i].right)
                right_solver.changeColBounds(right_bounds[i].var_id, right_bounds[i].left, right_bounds[i].right)

            left_solver.run()
            right_solver.run()

            print(self.__mip_state.dual_value())
            print(stack_item.dual_value, left_solver.getInfo().objective_function_value, right_solver.getInfo().objective_function_value)

            if left_solver.getModelStatus().value == 7 and right_solver.getModelStatus().value == 7:
                print(1)
                left_objective_function_value = left_solver.getInfo().objective_function_value
                left_solution = left_solver.getSolution().col_value
                right_objective_function_value = right_solver.getInfo().objective_function_value
                right_solution = right_solver.getSolution().col_value

                if left_objective_function_value < right_objective_function_value:
                    if self.__check_on_primal(right_solution):
                        self.__mip_state.update_primal_solution(right_objective_function_value, right_solution)
                    elif right_objective_function_value < self.__mip_state.primal_value():
                        self.__stack.append(StackItem(right_bounds, right_solution,
                                               right_objective_function_value))
                    if self.__mip_state_update(left_objective_function_value, left_solution):
                        self.__stopped = True
                        return
                    if left_objective_function_value < self.__mip_state.primal_value():
                        stack_item = StackItem(left_bounds, left_solution,
                                       left_objective_function_value)
                    else:
                        if not self.__stack:
                            self.__stopped = True
                            return

                        min_idx = 0
                        min_val = self.__stack[0].dual_value
                        for idx, val in enumerate(self.__stack):
                            if val.dual_value < min_val:
                                min_val = val.dual_value
                                min_idx = idx

                        if self.__mip_state.primal_value() <= self.__stack[min_idx].dual_value:
                            self.__mip_state.update_dual_solution(self.__mip_state.primal_value(),
                                                                  self.__mip_state.primal_solution())
                            self.__stopped = True
                            return

                        self.__mip_state.update_dual_solution(self.__stack[min_idx].dual_value,
                                                              self.__stack[min_idx].solution)

                        stack_item = self.__stack.pop()
                        if self.__mip_state.converged():
                            self.__stopped = True
                            return
                else:
                    if self.__check_on_primal(left_solution):
                        self.__mip_state.update_primal_solution(left_objective_function_value, left_solution)
                    elif left_objective_function_value < self.__mip_state.primal_value():
                        self.__stack.append(StackItem(left_bounds, left_solution,
                              left_objective_function_value))
                    if self.__mip_state_update(right_objective_function_value, right_solution):
                        self.__stopped = True
                        return
                    if right_objective_function_value < self.__mip_state.primal_value():
                        stack_item = StackItem(right_bounds, right_solution,
                                           right_objective_function_value)
                    else:
                        if not self.__stack:
                            self.__stopped = True
                            return

                        min_idx = 0
                        min_val = self.__stack[0].dual_value
                        for idx, val in enumerate(self.__stack):
                            if val.dual_value < min_val:
                                min_val = val.dual_value
                                min_idx = idx

                        if self.__mip_state.primal_value() <= self.__stack[min_idx].dual_value:
                            self.__mip_state.update_dual_solution(self.__mip_state.primal_value(),
                                                                  self.__mip_state.primal_solution())
                            self.__stopped = True
                            return

                        self.__mip_state.update_dual_solution(self.__stack[min_idx].dual_value,
                                                              self.__stack[min_idx].solution)

                        stack_item = self.__stack.pop()
                        if self.__mip_state.converged():
                            self.__stopped = True
                            return

            elif left_solver.getModelStatus().value != 7 and right_solver.getModelStatus().value == 7:
                print(2)
                right_objective_function_value = right_solver.getInfo().objective_function_value
                right_solution = right_solver.getSolution().col_value

                if self.__mip_state_update(right_objective_function_value, right_solution):
                    self.__stopped = True
                    return
                if right_objective_function_value < self.__mip_state.primal_value():
                    stack_item = StackItem(right_bounds, right_solution,
                                       right_objective_function_value)
                else:
                    if not self.__stack:
                        self.__stopped = True
                        return

                    min_idx = 0
                    min_val = self.__stack[0].dual_value
                    for idx, val in enumerate(self.__stack):
                        if val.dual_value < min_val:
                            min_val = val.dual_value
                            min_idx = idx

                    if self.__mip_state.primal_value() <= self.__stack[min_idx].dual_value:
                        self.__mip_state.update_dual_solution(self.__mip_state.primal_value(),
                                                              self.__mip_state.primal_solution())
                        self.__stopped = True
                        return

                    self.__mip_state.update_dual_solution(self.__stack[min_idx].dual_value,
                                                          self.__stack[min_idx].solution)

                    stack_item = self.__stack.pop()
                    if self.__mip_state.converged():
                        self.__stopped = True
                        return

            elif left_solver.getModelStatus().value == 7 and right_solver.getModelStatus().value != 7:
                print(3)
                left_objective_function_value = left_solver.getInfo().objective_function_value
                left_solution = left_solver.getSolution().col_value

                if self.__mip_state_update(left_objective_function_value, left_solution):
                    self.__stopped = True
                    return
                if left_objective_function_value < self.__mip_state.primal_value():
                    stack_item = StackItem(left_bounds, left_solution,
                                           left_objective_function_value)
                else:
                    if not self.__stack:
                        self.__stopped = True
                        return

                    min_idx = 0
                    min_val = self.__stack[0].dual_value
                    for idx, val in enumerate(self.__stack):
                        if val.dual_value < min_val:
                            min_val = val.dual_value
                            min_idx = idx

                    if self.__mip_state.primal_value() <= self.__stack[min_idx].dual_value:
                        self.__mip_state.update_dual_solution(self.__mip_state.primal_value(),
                                                              self.__mip_state.primal_solution())
                        self.__stopped = True
                        return

                    self.__mip_state.update_dual_solution(self.__stack[min_idx].dual_value,
                                                          self.__stack[min_idx].solution)

                    stack_item = self.__stack.pop()
                    if self.__mip_state.converged():
                        self.__stopped = True
                        return

            else:
                print(4)
                if not self.__stack:
                    self.__stopped = True
                    return

                min_idx = 0
                min_val = self.__stack[0].dual_value
                for idx, val in enumerate(self.__stack):
                    if val.dual_value < min_val:
                        min_val = val.dual_value
                        min_idx = idx

                if self.__mip_state.primal_value() <= self.__stack[min_idx].dual_value:
                    self.__mip_state.update_dual_solution(self.__mip_state.primal_value(), self.__mip_state.primal_solution())
                    self.__stopped = True
                    return

                self.__mip_state.update_dual_solution(self.__stack[min_idx].dual_value, self.__stack[min_idx].solution)

                stack_item = self.__stack.pop()
                if self.__mip_state.converged():
                    self.__stopped = True
                    return

    def __mip_state_update(self, objective_function_value: float, solution: list[float]) -> bool:
        if objective_function_value < min([val.dual_value for val in self.__stack] + [self.__mip_state.primal_value()]):
            self.__mip_state.update_dual_solution(objective_function_value, solution)
        if self.__check_on_primal(solution):
            self.__mip_state.update_primal_solution(objective_function_value, solution)
        return self.__mip_state.converged()

    def __find_cut(self, stack_item: StackItem) -> tuple[Bound, Bound]:
        # TODO change logic
        heuristics = lambda x: abs(x - 0.5)
        result_id = 0
        min_heuristic_value = self.__solver.inf
        result = 0
        # random.shuffle(self.__generalize)

        for i in self.__generalize:
            value = stack_item.solution[i]
            lower = value // 1
            temp_heuristics = heuristics(value - lower)
            if temp_heuristics < min_heuristic_value:
                result_id = i
                min_heuristic_value = temp_heuristics
                result = int(lower)

        return Bound(result_id, 0, result), Bound(result_id, result + 1, self.__max_var_value)
