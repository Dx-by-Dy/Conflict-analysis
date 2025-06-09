from bound import Bound
from helpers.constraint import Constraint
from helpers.var import Var


class GraphNodes:
    def __init__(self):
        self.vars_state: list[dict[Var, list[Bound]]] = []

    def add_var_state(self, var: Var, iteration: int) -> int:
        bound = Bound(var.lower, var.upper)
        if iteration < len(self.vars_state):
            if var in self.vars_state[iteration]:
                self.vars_state[iteration][var].append(bound)
            else:
                self.vars_state[iteration][var] = [bound]
        else:
            self.vars_state.append({var: [bound]})

        return len(self.vars_state[iteration][var]) - 1

    def get_index(self, var: Var, iteration: int) -> int | None:
        if var in self.vars_state[iteration]:
            return len(self.vars_state[iteration][var]) - 1
        return None

    def get_bound(self, index: tuple[int,
                                     Var, int]) -> Bound:
        return self.vars_state[index[0]][index[1]][index[2]]


class GraphEdges:
    def __init__(self):
        self.vars_connections: list[tuple[tuple[int,
                                                Var, int], tuple[int, Var, int]]] = []

    def add_connection(self, first_node: tuple[int,
                                               Var, int], second_node: tuple[int,
                                                                             Var, int]) -> None:
        self.vars_connections.append((first_node, second_node))


class Graph:
    def __init__(self):
        self.iteration = 0
        self.nodes = GraphNodes()
        self.edges = GraphEdges()

    def add_iteration(self) -> None:
        self.iteration += 1

    def add_connection(self, var: Var, constr: Constraint) -> None:
        new_node_index = self.nodes.add_var_state(var, self.iteration)

        for another_var in constr.info:
            if another_var == var:
                continue

            iteration = self.iteration
            while node_index := self.nodes.get_index(another_var, iteration) is None:
                iteration -= 1
                if iteration == -1:
                    break
            if iteration == -1:
                continue

            self.edges.add_connection(
                (iteration, another_var, node_index), (self.iteration, var, new_node_index))

    def to_plot_info(self) -> tuple[list[tuple[int, Var, Bound]], list[tuple[tuple[int, Var, Bound], tuple[int, Var, Bound]]]]:

        node_idx = 0
        nodes = {}
        edges = []
        for edge in self.edges.vars_connections:
            if edge[0] not in nodes:
                nodes[edge[0]] = (node_idx, edge[0][1],
                                  self.nodes.get_bound(edge[0]))
                node_idx += 1
            if edge[1] not in nodes:
                nodes[edge[1]] = (node_idx, edge[1][1],
                                  self.nodes.get_bound(edge[1]))
                node_idx += 1

            edges.append((nodes[edge[0]], nodes[edge[1]]))

        return [v for v in nodes.values()], edges
