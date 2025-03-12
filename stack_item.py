class StackItem:
    def __init__(self, bounds, solution, dual_value):
        self.bounds = bounds
        self.solution = solution
        self.dual_value = dual_value

    def __str__(self):
        text = "StackItem{\n\tBounds:\n"
        for bound in self.bounds:
            text += "\t\t" + str(bound) + "\n"
        text += "\tSolution:\n\t\t" + str(self.solution) + "\n"
        text += "\tDual value:\n\t\t" + str(self.dual_value) + "\n}"
        return text