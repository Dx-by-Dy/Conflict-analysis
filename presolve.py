import gurobipy as gp


class Rows:
    def __init__(self, dict_of_rows: dict[gp.Constr, list[tuple[gp.Var, float]]]) -> None:
        self.rows = dict_of_rows

    def __str__(self):
        text = "Rows{"
        for row in self.rows.keys():
            text += "\n\tRow{ " + f"Constr{{sence: '{row.Sense}', rhs_value: {row.RHS}}}" + ": "
            for value in self.rows[row]:
                text += "\n\t\t" + f"name: {value[0].VarName}, coeff: {value[1]}, lb: {value[0].LB}, ub: {value[0].UB}"
            text += "\n\t}"
        text += "\n}"
        return text


if __name__ == '__main__':
    # path = "../../Downloads/benchmark/supportcase16.mps"
    path = "test.mps"

    model = gp.read(path)
    model.setParam('OutputFlag', 0)
    # model.getVars()[0].setAttr("ub", 0.1)
    # model.optimize()

    # print(model.ObjVal)
    g = []
    for v in model.getVars():
        if v.VType != "C":
            g += [v.VarName]
            v.setAttr("vType", "C")
    print(g)

    rows = Rows(dict([(con, []) for con in model.getConstrs()]))
    for var in model.getVars():
        col = model.getCol(var)
        for i in range(col.size()):
            rows.rows[col.getConstr(i)].append((var, col.getCoeff(i)))
    print(rows)
