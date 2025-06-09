import highspy

from graph import Graph
from helpers.constraint import Constraint
from helpers.solution import Solution
from helpers.var import Var


class ExtendedHighsModel(highspy.Highs):
    def __init__(self, path_to_problem: str | None = None, primal_tolerance: float = 1e-9):

        super().__init__()
        self.silent()

        self.vars: list[Var] = []
        self.constraints: list[Constraint] = []
        self.solution: Solution = Solution(primal_tolerance=primal_tolerance)
        self.presolver_stopped = False
        self.graph = Graph()

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

    def copy(self):
        res = ExtendedHighsModel()
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

        # TODO: change col bound!

        return res

    def change_var_bounds(self, var: Var, lower: float, upper: float) -> None:
        self.changeColBounds(var.index, lower, upper)
        self.vars[var.index].lower = lower
        self.vars[var.index].upper = upper

    def set_consistent(self) -> None:
        self.update_vars_bounds()
        for var in self.vars:
            self.setContinuous(var.index)

        self.run()
        self.solution.set_solution(objective=self.getInfo().objective_function_value,
                                   value=(
                                       self.vars, self.getSolution().col_value),
                                   feasible=self.getModelStatus() == highspy.HighsModelStatus.kOptimal)

        for var in self.vars:
            if var.is_general:
                self.setInteger(var.index)

    def update_vars_bounds(self):
        for i in range(10):
            have_changes = False
            graph_changed = False
            for constr in self.constraints:
                update_res = constr.update_vars()
                if update_res is None:
                    self.presolver_stopped = True
                    return False
                for var in update_res[0]:
                    self.graph.add_connection(var, constr)
                    graph_changed = True
                have_changes |= (len(update_res[0]) != 0 or update_res[1])
            self.presolver_stopped = not have_changes
            if graph_changed:
                self.graph.add_iteration()
            if self.presolver_stopped:
                break
        return True

    def get_var(self, index: int) -> Var:
        return self.vars[index]

    def __repr__(self):
        text = "ExtendedHighsModel {\n"

        text += "\tVars {\n"
        for var in self.vars:
            text += "\t\t" + var.__repr__()
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
