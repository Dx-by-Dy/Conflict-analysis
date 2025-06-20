from extended_highs_model import ExtendedHighsModel


class Node:
    def __init__(self, exh: ExtendedHighsModel):
        self.exh = exh

    def branching(self):
        bnb_branch = self.exh.solution.find_bnb_branch()

        if bnb_branch is None:
            return None

        left_exh = self.exh.copy()
        right_exh = self.exh.copy()

        left_exh.change_var_bounds(
            bnb_branch.var, bnb_branch.left_bound.lower, bnb_branch.left_bound.upper)
        right_exh.change_var_bounds(
            bnb_branch.var, bnb_branch.right_bound.lower, bnb_branch.right_bound.upper)

        left_node = Node(left_exh)
        left_node.exh.set_consistent(bnb_branch.var)

        right_node = Node(right_exh)
        right_node.exh.set_consistent(bnb_branch.var)

        return left_node, right_node

    def is_feasible(self) -> bool:
        return self.exh.solution.is_feasible()
