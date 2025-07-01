from extended_highs_model import ExtendedHighsModel
from enum import Enum, auto


class Branchability(Enum):
    Branchable = auto()
    IntFeasible = auto()
    Infeasible = auto()
    Dropped = auto()
    Unknown = auto()


class Node:
    def __init__(self, exh: ExtendedHighsModel):
        self.exh = exh
        self.branchability = Branchability.Unknown


def sort_nodes(left_node: Node, right_node: Node) -> tuple[Node, Node]:
    return left_node, right_node

    if left_node.exh.solution.is_feasible():
        return right_node, left_node
    if (left_node.exh.solution.is_feasible() and
        left_node.exh.solution.is_feasible() and
            right_node.exh.solution.objective > left_node.exh.solution.objective):
        return right_node, left_node

    return left_node, right_node
