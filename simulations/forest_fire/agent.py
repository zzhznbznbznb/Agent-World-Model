from mesa import Agent


class TreeCell(Agent):
    """A tree cell.

    condition:
        Fine        - 正常
        On Fire     - 着火
        Burned Out  - 烧毁
    """

    def __init__(self, model):
        super().__init__(model)
        self.condition = "Fine"

    def step(self):
        """执行一个仿真时间步。"""

        if self.condition == "On Fire":

            # 获取周围 8 个格子的树
            neighbors = self.model.grid.get_neighbors(
                self.pos,
                moore=True,
                include_center=False,
            )

            # 点燃附近正常的树
            for neighbor in neighbors:
                if neighbor.condition == "Fine":
                    neighbor.condition = "On Fire"

            # 当前树烧毁
            self.condition = "Burned Out"
