import highspy

from bound import Bound
from graph import Graph
from helpers.constraint import Constraint
from helpers.graph_cut import GraphCut
from helpers.solution import Solution
from helpers.var import Var


class ExtendedHighsModel(highspy.Highs):
    def __init__(self,
                 with_presolve: bool,
                 cutting_mod: int = 1,
                 fuip_size: int = 1,
                 path_to_problem: str | None = None,
                 primal_tolerance: float = 1e-9):

        super().__init__()
        self.silent()

        self.vars: list[Var] = []
        self.constraints: list[Constraint] = []
        self.solution: Solution = Solution(primal_tolerance=primal_tolerance)
        self.presolver_stopped = False
        self.with_presolve = with_presolve
        self.graph = Graph(fuip_size=fuip_size, cutting_mod=cutting_mod)
        self.is_consistent: bool = False

        if path_to_problem is None:
            return

        self.readModel(path_to_problem)
        self.presolve()

        lp = self.getLp()
        for var_idx, (var_type, var_name, var_lower, var_upper) in enumerate(zip(lp.integrality_, lp.col_names_, lp.col_lower_, lp.col_upper_)):
            self.vars.append(
                Var(
                    index=var_idx,
                    name=var_name,
                    lower_bound=var_lower,
                    upper_bound=var_upper,
                    is_general=var_type == highspy.HighsVarType.kInteger,
                )
            )

        for constr_idx, (constr_lower, constr_upper) in enumerate(zip(lp.row_lower_, lp.row_upper_)):
            self.constraints.append(
                Constraint(
                    index=constr_idx,
                    lower_bound=constr_lower,
                    upper_bound=constr_upper
                )
            )

        const_idx_and_value = list(
            zip(lp.a_matrix_.index_, lp.a_matrix_.value_)
        )
        for var_idx in range(len(lp.a_matrix_.start_) - 1):
            for idx in range(lp.a_matrix_.start_[var_idx], lp.a_matrix_.start_[var_idx + 1]):
                constr_idx, coeff = const_idx_and_value[idx]
                self.constraints[constr_idx].add_var(self.vars[var_idx], coeff)
                self.vars[var_idx].add_constraint(self.constraints[constr_idx])

        for var in self.vars:
            self.setContinuous(var.index)

    def copy(self):
        res = ExtendedHighsModel(self.with_presolve)
        res.passModel(self.getModel())
        res.setBasis(self.getBasis())

        for constr in self.constraints:
            res.constraints.append(constr.copy_empty())

        for var in self.vars:
            res.vars.append(var.copy_empty())

        for constr in self.constraints:
            nconstr = res.constraints[constr.index]
            for var in constr.info:
                nvar = res.vars[var.index]
                nconstr.add_var(nvar, constr.info[var])
                nvar.add_constraint(nconstr)

        res.graph = self.graph.copy(res.vars)
        return res

    def add_row(self, graph_cut: GraphCut) -> None:
        self.is_consistent = False
        self.addRow(1 - graph_cut.number_of_negative, float("inf"),
                    len(graph_cut.indices), graph_cut.indices, graph_cut.values)
        self.constraints.append(Constraint(len(self.constraints), 1 -
                                           graph_cut.number_of_negative, float("inf")))
        for index, coeff in zip(graph_cut.indices, graph_cut.values):
            self.constraints[-1].add_var(self.vars[index], coeff)
            self.vars[index].add_constraint(self.constraints[-1])

    def delete_last_row(self) -> None:
        self.is_consistent = False
        constr = self.constraints.pop()
        self.deleteRows(1, [constr.index])
        for var in constr.info:
            var.remove_last_constraint()

    def validate_cut(self, graph_cut: GraphCut) -> bool:
        for index, val in zip(graph_cut.indices, graph_cut.values):
            if val == -1:
                self.changeColBounds(index, 1, 1)
            else:
                self.changeColBounds(index, 0, 0)

        self.run()
        status = self.getModelStatus()

        for index in graph_cut.indices:
            self.changeColBounds(
                index, self.vars[index].lower, self.vars[index].upper)

        return status == highspy.HighsModelStatus.kInfeasible

    def change_var_bounds(self, var: Var, lower: float, upper: float) -> None:
        self.is_consistent = False
        self.changeColBounds(var.index, lower, upper)
        self.vars[var.index].lower = lower
        self.vars[var.index].upper = upper

    def set_consistent(self, branched_var: Var | None = None) -> bool:
        if self.is_consistent:
            return
        self.is_consistent = True

        if self.with_presolve:
            if branched_var is not None:
                self.graph.new_depth(self.vars[branched_var.index])
            self.update_vars_bounds()

        self.run()
        return self.solution.set_solution(objective=self.getInfo().objective_function_value,
                                          value=(
                                              self.vars, self.getSolution().col_value),
                                          status=self.getModelStatus())

    def update_vars_bounds(self):
        for i in range(10):
            have_changes = False
            constrs_updates: list[dict[Var, Bound]] = []
            for constr in self.constraints:
                if not constr.update_vars(constrs_updates):
                    self.presolver_stopped = True
                    return False

            for constr_index, constr_update in enumerate(constrs_updates):
                if len(constr_update) == 0:
                    continue
                for var, bound in constr_update.items():
                    if not var.is_valid_update(bound.lower, bound.upper):
                        continue
                    self.change_var_bounds(var, bound.lower, bound.upper)
                    self.graph.add_connection(
                        var, self.constraints[constr_index])
                self.constraints[constr_index].update_lower_upper_by_activity()
                self.changeRowBounds(
                    constr_index, self.constraints[constr_index].lower, self.constraints[constr_index].upper)
                have_changes = True

            self.graph.next_iteration()
            self.presolver_stopped = not have_changes
            if self.presolver_stopped:
                break
        return True

    def get_var(self, index: int) -> Var:
        return self.vars[index]

    def __repr__(self):
        text = "ExtendedHighsModel {\n"

        text += "\tVars {\n"
        for var in self.vars:
            text += "\t\t" + var.__repr__() + "\n"
        text += "\t}\n\n"

        text += "\tConstaints {\n"
        for constr in self.constraints:
            text += "\t\t" + constr.__repr__()
        text += "\t}\n"

        text += "}\n"
        return text


if __name__ == "__main__":
    ex = ExtendedHighsModel("problems/problem_from_article_mod.lp")
    print(ex)
    print(ex.update_vars_bounds())
    print(ex)
