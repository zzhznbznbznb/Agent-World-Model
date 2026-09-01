import mesa

from .agent import TreeCell


class ForestFire(mesa.Model):
    """Mesa Forest Fire World Model."""

    def __init__(
        self,
        width=20,
        height=20,
        density=0.65,
        seed=None,
    ):
        super().__init__(seed=seed)

        self.width = width
        self.height = height
        self.density = density

        self.grid = mesa.space.MultiGrid(
            width,
            height,
            torus=False,
        )

        # ==================================================
        # 初始化森林
        # ==================================================

        for x in range(width):
            for y in range(height):

                if self.random.random() < density:

                    tree = TreeCell(self)

                    self.grid.place_agent(
                        tree,
                        (x, y),
                    )

        # ==================================================
        # 第一列树着火
        # ==================================================

        for y in range(height):

            agents = self.grid.get_cell_list_contents(
                [(0, y)]
            )

            for agent in agents:

                agent.condition = "On Fire"

        self.running = True

    # ==================================================
    # 推进一个时间步
    # ==================================================

    def step(self):
        """推进一个仿真时间步。"""

        if not self.running:
            return

        self.agents.shuffle_do("step")

        burning = self.agents.select(
            lambda agent:
            agent.condition == "On Fire"
        )

        if len(burning) == 0:

            self.running = False

    # ==================================================
    # 修改当前森林密度
    # ==================================================

    def set_density(self, new_density):
        """
        在当前 World Model 状态上修改森林密度。

        注意：
        这里不会重新创建 ForestFire，
        也不会重新随机生成整个森林。

        例如：

            当前 Step = 10
            当前 density = 0.65

            用户要求：
            "把森林密度提高到 0.80"

        那么会在当前森林基础上增加树木，
        Step 仍然保持为 10。
        """

        # --------------------------------------------------
        # 限制范围
        # --------------------------------------------------

        new_density = max(
            0.0,
            min(1.0, float(new_density))
        )

        # --------------------------------------------------
        # 当前总格子数量
        # --------------------------------------------------

        total_cells = (
            self.width *
            self.height
        )

        # --------------------------------------------------
        # 当前树木数量
        # --------------------------------------------------

        current_trees = len(
            self.agents
        )

        # --------------------------------------------------
        # 目标树木数量
        # --------------------------------------------------

        target_trees = int(
            total_cells *
            new_density
        )

        difference = (
            target_trees -
            current_trees
        )

        # ==================================================
        # 情况 1：增加森林密度
        # ==================================================

        if difference > 0:

            # 找到当前空的格子
            empty_cells = []

            for x in range(self.width):

                for y in range(self.height):

                    cell_agents = (
                        self.grid
                        .get_cell_list_contents(
                            [(x, y)]
                        )
                    )

                    if len(cell_agents) == 0:

                        empty_cells.append(
                            (x, y)
                        )

            # 随机打乱空地
            self.random.shuffle(
                empty_cells
            )

            # 实际增加数量
            add_count = min(
                difference,
                len(empty_cells)
            )

            for pos in empty_cells[
                :add_count
            ]:

                tree = TreeCell(self)

                self.grid.place_agent(
                    tree,
                    pos,
                )

        # ==================================================
        # 情况 2：降低森林密度
        # ==================================================

        elif difference < 0:

            remove_count = -difference

            # 优先删除 Fine 状态的树
            fine_agents = [
                agent
                for agent in self.agents
                if agent.condition == "Fine"
            ]

            self.random.shuffle(
                fine_agents
            )

            remove_count = min(
                remove_count,
                len(fine_agents)
            )

            for agent in fine_agents[
                :remove_count
            ]:

                agent.remove()

        # ==================================================
        # 更新 density
        # ==================================================

        self.density = new_density

        # ==================================================
        # 如果修改后仍然存在着火的树
        # 那么世界继续运行
        # ==================================================

        burning = self.agents.select(
            lambda agent:
            agent.condition == "On Fire"
        )

        self.running = (
            len(burning) > 0
        )
