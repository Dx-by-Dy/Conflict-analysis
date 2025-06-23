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
    if right_node.branchability.value < left_node.branchability.value or \
            (left_node.branchability == Branchability.Branchable and
             right_node.branchability == Branchability.Branchable and
             right_node.exh.solution.objective < left_node.exh.solution.objective):
        return right_node, left_node
    return left_node, right_node
