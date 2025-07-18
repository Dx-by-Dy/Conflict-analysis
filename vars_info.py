class VarsInfo:
    def __init__(self, number_of_vars: int):
        self.info = [VarInfo(i) for i in range(number_of_vars)]


class VarInfo:
    def __init__(self, index: int):
        self.index: int = index
        self.number_of_braching_right: int = 0
        self.number_of_braching_left: int = 0
        self.cumul_diff_right: float = 0
        self.cumul_diff_left: float = 0

    def check_var(self, index: int) -> bool:
        min(self.number_of_braching_left, self.number_of_braching_right) >= 2

    def update(self, lp_diff: float, frac: float, is_right: bool) -> None:
        if is_right:
            self.cumul_diff_right += lp_diff / frac
            self.number_of_braching_right += 1
        else:
            self.cumul_diff_left += lp_diff / frac
            self.number_of_braching_left += 1
