from bound import Bound
from helpers.constraint import Constraint
from helpers.graph_cut import GraphCut
from helpers.var import Var


class GraphNode:
    def __init__(self, depth: int, iteration: int, var: Var):
        self.depth = depth
        self.iteration = iteration
        self.var = var
        self.bound = Bound(var.lower, var.upper)
        self.input_nodes: list[int] = []
        self.output_nodes: list[int] = []

    def copy(self, new_vars: list[Var]):
        new_graph_node = GraphNode(
            self.depth, self.iteration, new_vars[self.var.index])
        new_graph_node.bound = Bound(
            new_graph_node.var.lower, new_graph_node.var.upper)
        for node_idx in self.input_nodes:
            new_graph_node.input_nodes.append(node_idx)
        for node_idx in self.output_nodes:
            new_graph_node.output_nodes.append(node_idx)
        return new_graph_node


class GraphEdge:
    def __init__(self, first_node_index: int, second_node_index: int):
        self.first_node_index = first_node_index
        self.second_node_index = second_node_index

    def copy(self):
        return GraphEdge(self.first_node_index, self.second_node_index)


class Graph:
    def __init__(self, depth: int = 0, iteration: int = 0, fuip_size: int = 1, cutting_mod: int = 1):
        self.iteration = iteration
        self.depth = depth
        self.vars_index: dict[Var, list[int]] = {}
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self.origins: list[int] = []
        self.drains: list[set[int]] = [set()]
        self.fuip_size = fuip_size
        self.cutting_mod = cutting_mod
        self.end_of_index = 0

    def get_last_node_index(self, var: Var) -> int:
        return self.vars_index[var][-1]

    def new_depth(self, var: Var) -> None:
        self.depth += 1
        self.iteration = 0
        node_idx = self.add_node(var)
        self.add_all_to_index()
        self.origins.append(node_idx)
        self.drains.append({node_idx})
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
            self.add_node_connection(another_node_index, new_node_index)

    def add_node_connection(self, from_node: int, in_node: int) -> None:
        self.nodes[from_node].output_nodes.append(in_node)
        self.nodes[in_node].input_nodes.append(from_node)

        if self.nodes[from_node].depth <= self.nodes[in_node].depth:
            self.drains[self.depth].discard(from_node)
        if len(self.nodes[in_node].output_nodes) == 0:
            self.drains[self.depth].add(in_node)

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

        if len(self.origins) > 0 and self.origins[-1] not in origins:
            origins.append(self.origins[-1])

        return nodes, edges, origins

    def copy(self, new_vars: list[Var]):
        new_graph = Graph(self.depth, self.iteration,
                          self.fuip_size, self.cutting_mod)

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

        for idx, sets in enumerate(self.drains):
            if idx == 0:
                continue
            new_graph.drains.append(sets.copy())

        return new_graph

    def find_FUIP(self) -> list[int]:
        graph_cut: list[int] = []

        current_implication_set: dict[int,
                                      dict[int, set[int]]] = {}
        number_nodes_on_depth: dict[int, int] = {}
        max_nodes_iteration_on_depth: dict[int, int] = {}

        for depth in range(1, self.depth + 1):
            current_implication_set[depth] = {}
            number_nodes_on_depth[depth] = 0
            max_nodes_iteration_on_depth[depth] = 0

            for node_idx in self.drains[depth]:
                if self.nodes[node_idx].iteration in current_implication_set[depth]:
                    current_implication_set[depth][self.nodes[node_idx].iteration].add(
                        node_idx)
                else:
                    current_implication_set[depth][self.nodes[node_idx].iteration] = {
                        node_idx}
                max_nodes_iteration_on_depth[depth] = max(
                    self.nodes[node_idx].iteration, max_nodes_iteration_on_depth[depth])
                number_nodes_on_depth[depth] += 1

        for depth in range(self.depth, 0, -1):
            if number_nodes_on_depth[depth] <= self.fuip_size:
                for it in range(0, max_nodes_iteration_on_depth[depth] + 1):
                    if it in current_implication_set[depth]:
                        for node_idx in current_implication_set[depth][it]:
                            graph_cut.append(node_idx)
                continue

            for iteration in range(max_nodes_iteration_on_depth[depth], -1, -1):
                if iteration not in current_implication_set[depth]:
                    continue

                removed_nodes = set()
                ready = False
                for node_idx in current_implication_set[depth][iteration]:
                    for implication_node_idx in self.nodes[node_idx].input_nodes:
                        implication_node = self.nodes[implication_node_idx]
                        if implication_node.depth == 0:
                            continue

                        if implication_node.iteration in current_implication_set[implication_node.depth]:
                            if implication_node_idx not in current_implication_set[implication_node.depth][implication_node.iteration]:
                                current_implication_set[implication_node.depth][implication_node.iteration].add(
                                    implication_node_idx)
                                number_nodes_on_depth[implication_node.depth] += 1
                        else:
                            current_implication_set[implication_node.depth][implication_node.iteration] = {
                                implication_node_idx}
                            number_nodes_on_depth[implication_node.depth] += 1

                    number_nodes_on_depth[depth] -= 1
                    removed_nodes.add(node_idx)
                    if number_nodes_on_depth[depth] <= self.fuip_size:
                        for it in range(0, iteration + 1):
                            if it in current_implication_set[depth]:
                                for node_idx in current_implication_set[depth][it]:
                                    if node_idx not in removed_nodes:
                                        graph_cut.append(node_idx)
                        break
                if ready:
                    break

                current_implication_set[depth].pop(iteration)

        return graph_cut

    def get_front_nodes_indices(self) -> list[int]:
        if self.cutting_mod == 0:
            return []
        elif self.cutting_mod == 1:
            return self.find_FUIP()
        elif self.cutting_mod == 2:
            return self.origins
        raise ValueError

    def get_graph_cut(self) -> GraphCut:
        nodes_indices = self.get_front_nodes_indices()

        indices = []
        values = []
        number_of_negative = 0
        is_trivial = True
        for node_idx in nodes_indices:
            if self.nodes[node_idx].bound.lower > 0:
                number_of_negative += 1
                values.append(-1)
            else:
                values.append(1)
            indices.append(self.nodes[node_idx].var.index)

            if self.nodes[node_idx].iteration > 0:
                is_trivial = False

        return GraphCut(number_of_negative, indices, values, is_trivial)
