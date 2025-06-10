from bound import Bound
from helpers.constraint import Constraint
from helpers.var import Var


class GraphVarNode:
    def __init__(self, iteration: int, var: Var, bound: Bound):
        self.iteration = iteration
        self.var = var
        self.bound = bound

    def __eq__(self, other):
        return self.iteration == other.iteration and self.var.index == other.var.index and self.bound == other.bound

    def __repr__(self):
        return f"GraphVarNode: iteration: {self.iteration}, var: {self.var.__repr__()}, bound: {self.bound.__repr__()}"


class GraphNodeID:
    def __init__(self, iteration: int, var: Var, bound_index: int):
        self.iteration = iteration
        self.var = var
        self.bound_index = bound_index

    def copy(self, new_vars: list[Var]):
        return GraphNodeID(self.iteration, new_vars[self.var.index], self.bound_index)

    def __hash__(self):
        return hash((self.iteration, self.var.index, self.bound_index))

    def __eq__(self, other):
        return self.iteration == other.iteration and self.var.index == other.var.index and self.bound_index == other.bound_index

    def __repr__(self):
        return f"GraphNodeID: iteration: {self.iteration}, var: {self.var.__repr__()}, bound_index: {self.bound_index}"


class GraphNode:
    def __init__(self):
        self.vars_states: dict[Var, list[Bound]] = {}

    def have_var_state(self, var: Var) -> bool:
        if var not in self.vars_states:
            return False
        return not self.vars_states[var][-1].is_strong_upperset(Bound(var.lower, var.upper))

    def add_var_state(self, var: Var) -> int:
        if var in self.vars_states:
            self.vars_states[var].append(Bound(var.lower, var.upper))
        else:
            self.vars_states[var] = [Bound(var.lower, var.upper)]
        return len(self.vars_states[var]) - 1

    def get_last_index(self, var: Var) -> int | None:
        if var in self.vars_states:
            return len(self.vars_states[var]) - 1
        return None

    def get_bound(self, var: Var, bound_index: int) -> Bound:
        return self.vars_states[var][bound_index]

    def copy(self, new_vars: list[Var]):
        new_graph_node = GraphNode()

        for var, states in self.vars_states.items():
            new_states = []
            for bound in states:
                new_states.append(Bound(bound.lower, bound.upper))
            new_graph_node.vars_states[new_vars[var.index]] = new_states

        return new_graph_node


class GraphEdge:
    def __init__(self, first_node: GraphNodeID, second_node: GraphNodeID):
        self.first_node = first_node
        self.second_node = second_node

    def copy(self, new_vars: list[Var]):
        return GraphEdge(self.first_node.copy(new_vars), self.second_node.copy(new_vars))


class Graph:
    def __init__(self, iteration: int = 0):
        self.iteration = iteration
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.origins: list[GraphNodeID] = []

    def get_last_index(self, var: Var) -> tuple[int, int] | None:
        for iteration in range(len(self.nodes) - 1, -1, -1):
            bound_index = self.nodes[iteration].get_last_index(var)
            if bound_index is not None:
                return iteration, bound_index
        return None

    def have_var_state(self, var: Var) -> int:
        for iteration in range(len(self.nodes) - 1, -1, -1):
            if self.nodes[iteration].have_var_state(var):
                return iteration
        return -1

    def add_var_state(self, var: Var, origin: bool = False) -> int | None:
        if (iteration := self.have_var_state(var)) >= 0:
            if origin:
                self.origins.append(GraphNodeID(
                    iteration, var, self.nodes[iteration].get_last_index(var)))
            return None
        if self.iteration >= len(self.nodes):
            graph_node = GraphNode()
            bound_index = graph_node.add_var_state(var)
            self.nodes.append(graph_node)
        else:
            bound_index = self.nodes[self.iteration].add_var_state(
                var)
        if origin:
            self.origins.append(GraphNodeID(self.iteration, var, bound_index))
        return bound_index

    def add_iteration(self) -> None:
        self.iteration += 1

    def get_graph_var_node(self, graph_node_id: GraphNodeID) -> GraphVarNode:
        return GraphVarNode(graph_node_id.iteration,
                            graph_node_id.var,
                            self.nodes[graph_node_id.iteration].get_bound(graph_node_id.var, graph_node_id.bound_index))

    def add_connection(self, var: Var, constr: Constraint) -> None:
        new_var_bound_index = self.add_var_state(var)
        if new_var_bound_index is None:
            return

        for another_var in constr.info:
            if another_var == var:
                continue

            last_index_result = self.get_last_index(another_var)
            if last_index_result is None:
                continue

            self.edges.append(GraphEdge(
                GraphNodeID(last_index_result[0],
                            another_var, last_index_result[1]),
                GraphNodeID(self.iteration, var, new_var_bound_index)))

    def to_plot_info(self) -> tuple[list[GraphVarNode],
                                    list[tuple[GraphVarNode, GraphVarNode]],
                                    list[GraphVarNode]]:
        nodes = {}
        edges = []
        origins = []

        for edge in self.edges:
            first_graph_var_node = self.get_graph_var_node(edge.first_node)
            if edge.first_node not in nodes:
                nodes[edge.first_node] = first_graph_var_node
            if edge.first_node in self.origins:
                origins.append(first_graph_var_node)

            second_graph_var_node = self.get_graph_var_node(edge.second_node)
            if edge.second_node not in nodes:
                nodes[edge.second_node] = second_graph_var_node

            edges.append((first_graph_var_node, second_graph_var_node))

        return list(nodes.values()), edges, origins

    def copy(self, new_vars: list[Var]):
        new_graph = Graph(self.iteration)

        for graph_node in self.nodes:
            new_graph.nodes.append(graph_node.copy(new_vars))

        for edge in self.edges:
            new_graph.edges.append(edge.copy(new_vars))

        for origin in self.origins:
            new_graph.origins.append(origin.copy(new_vars))

        return new_graph
