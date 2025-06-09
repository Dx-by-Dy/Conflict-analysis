

from bound import Bound
from helpers.var import Var
from extended_highs_model import ExtendedHighsModel


class Node:
    def __init__(self, exh: ExtendedHighsModel):
        self.exh = exh
        self.external_bounds: dict[Var, Bound] = {}

    def set_consistent(self) -> None:
        self.exh.set_consistent()

    def splitting(self):
        cut = self.exh.solution.find_cut()

        if cut is None:
            return None

        left_exh = self.exh.copy()
        right_exh = self.exh.copy()

        left_exh.change_var_bounds(
            cut.var, cut.left_bound.lower, cut.left_bound.upper)
        right_exh.change_var_bounds(
            cut.var, cut.right_bound.lower, cut.right_bound.upper)

        left_node = Node(left_exh)
        left_node.external_bounds = self.external_bounds.copy()
        left_node.external_bounds[cut.var] = cut.left_bound
        left_node.set_consistent()

        right_node = Node(right_exh)
        right_node.external_bounds = self.external_bounds.copy()
        right_node.external_bounds[cut.var] = cut.right_bound
        right_node.set_consistent()

        return left_node, right_node

    def is_feasible(self) -> bool:
        return self.exh.solution.feasible
