from bound import Bound
from helpers.constraint import Constraint
from helpers.var import Var


# для индентификации вершины достаточно var, bound. Также требуется дополнительная информация о глубине вершины.
class GraphNode:
    def __init__(self, depth: int, iteration: int, var: Var):
        self.depth = depth
        self.iteration = iteration
        self.var = var
        self.bound = Bound(var.lower, var.upper)

    def copy(self, new_vars: list[Var]):
        new_graph_node = GraphNode(
            self.depth, self.iteration, new_vars[self.var.index])
        new_graph_node.bound = Bound(
            new_graph_node.var.lower, new_graph_node.var.upper)
        return new_graph_node


class GraphEdge:
    def __init__(self, first_node_index: int, second_node_index: int):
        self.first_node_index = first_node_index
        self.second_node_index = second_node_index

    def copy(self):
        return GraphEdge(self.first_node_index, self.second_node_index)


class Graph:
    def __init__(self, depth: int = 0, iteration: int = 0):
        self.iteration = iteration
        self.depth = depth
        self.vars_index: dict[Var, list[int]] = {}
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.origins: list[int] = []
        self.end_of_index = 0

    def get_last_node_index(self, var: Var) -> int:
        return self.vars_index[var][-1]

    def new_depth(self, var: Var) -> None:
        self.depth += 1
        self.iteration = 0
        node_idx = self.add_node(var)
        self.add_all_to_index()
        self.origins.append(node_idx)
        self.iteration = 1

    def next_iteration(self) -> None:
        self.iteration += 1
        self.add_all_to_index()

    def add_all_to_index(self) -> None:
        for node_idx in range(self.end_of_index, len(self.nodes)):
            node = self.nodes[node_idx]
            if node.var in self.vars_index:
                self.vars_index[node.var].append(node_idx)
            else:
                self.vars_index[node.var] = [node_idx]
        self.end_of_index = len(self.nodes)

    def add_node(self, var: Var) -> int:
        self.nodes.append(GraphNode(self.depth, self.iteration, var))
        return len(self.nodes) - 1

    def add_connection(self, var: Var,  constr: Constraint) -> None:
        new_node_index = self.add_node(var)

        for another_var in constr.info:
            if another_var == var or another_var not in self.vars_index:
                continue
            another_node_index = self.get_last_node_index(another_var)

            self.edges.append(
                GraphEdge(another_node_index, new_node_index))

    def to_plot_info(self) -> tuple[dict[int, GraphNode],
                                    list[tuple[int, int]],
                                    list[int]]:
        nodes = {}
        edges = []
        origins = []

        for edge in self.edges:
            if edge.first_node_index not in nodes:
                nodes[edge.first_node_index] = self.nodes[edge.first_node_index]
            if edge.first_node_index in self.origins:
                origins.append(edge.first_node_index)

            if edge.second_node_index not in nodes:
                nodes[edge.second_node_index] = self.nodes[edge.second_node_index]

            edges.append((edge.first_node_index, edge.second_node_index))

        return nodes, edges, origins

    def copy(self, new_vars: list[Var]):
        new_graph = Graph(self.depth, self.iteration)

        for var, states in self.vars_index.items():
            new_states = []
            for node_index in states:
                new_states.append(node_index)
            new_graph.vars_index[new_vars[var.index]] = new_states

        for graph_node in self.nodes:
            new_graph.nodes.append(graph_node.copy(new_vars))

        for edge in self.edges:
            new_graph.edges.append(edge.copy())

        for node_index in self.origins:
            new_graph.origins.append(node_index)
        new_graph.end_of_index = len(new_graph.nodes)

        return new_graph
