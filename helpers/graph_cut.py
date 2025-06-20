class GraphCut:
    def __init__(self,
                 number_of_negative: int,
                 indices: list[int],
                 values: list[float],
                 is_trivial: bool) -> None:
        self.number_of_negative = number_of_negative
        self.indices = indices
        self.values = values
        self.is_trivial = is_trivial

    def is_empty(self) -> bool:
        return len(self.indices) == 0
