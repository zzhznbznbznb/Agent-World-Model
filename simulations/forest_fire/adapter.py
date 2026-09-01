import copy
import io

import matplotlib.pyplot as plt
from .model import ForestFire


class ForestFireAdapter:
    """
    Adapter between Agent system and Mesa ForestFire World Model.

    负责：
    1. 创建 ForestFire World Model
    2. 推进仿真
    3. 保存历史状态
    4. 恢复历史状态
    5. 在当前 World Model 上修改参数
    6. 向 Controller 提供当前世界状态

    核心原则：

        修改参数 != 重新创建 World Model

    用户修改 density 时，
    直接修改当前 World Model，
    不重新生成整个森林。
    """

    def __init__(
        self,
        width=20,
        height=20,
        density=0.65,
        seed=None,
    ):

        self.width = width
        self.height = height
        self.density = density
        self.seed = seed

        # ==================================================
        # 创建 World Model
        # ==================================================

        self.model = ForestFire(
            width=width,
            height=height,
            density=density,
            seed=seed,
        )

        # ==================================================
        # 历史快照
        #
        # history[0] = 初始状态
        # history[1] = Step 1
        # history[2] = Step 2
        # ...
        #
        # 修改 density 后，也会保存一个快照。
        # ==================================================

        self.history = []

        self._save_snapshot()

    # ==================================================
    # 保存当前 World Model
    # ==================================================

    def _save_snapshot(self):
        """
        保存当前 World Model 的完整快照。
        """

        snapshot = copy.deepcopy(
            self.model
        )

        self.history.append(
            snapshot
        )

    # ==================================================
    # 推进仿真
    # ==================================================

    def step(self, steps=1):
        """
        推进仿真若干步。

        每运行一步，就保存一次快照。

        例如：

            Step 0
              ↓
            step(10)
              ↓
            Step 1
              ↓
            ...
              ↓
            Step 10
        """

        actual_steps = 0

        for _ in range(steps):

            # 如果火灾已经结束
            # 就停止推进
            if not self.model.running:
                break

            # 推进一个时间步
            self.model.step()

            # 保存当前状态
            self._save_snapshot()

            actual_steps += 1

        return actual_steps

    # ==================================================
    # 修改当前森林密度
    # ==================================================

    def set_density(self, new_density):
        """
        在当前 World Model 状态下修改森林密度。

        不重新创建 ForestFire。

        例如：

            当前：
                Step = 10
                density = 0.65

            用户：
                "把森林密度提高到 0.80"

            执行：

                model.set_density(0.80)

            结果：

                Step = 10
                density = 0.80

            当前森林会增加树木，
            而不是重新生成整个森林。
        """

        # --------------------------------------------------
        # 限制 density 范围
        # --------------------------------------------------

        new_density = max(
            0.0,
            min(
                1.0,
                float(new_density)
            )
        )

        # --------------------------------------------------
        # 修改当前 World Model
        # --------------------------------------------------

        self.model.set_density(
            new_density
        )

        # --------------------------------------------------
        # 同步 Adapter 参数
        # --------------------------------------------------

        self.density = (
            self.model.density
        )

        # --------------------------------------------------
        # 重要：
        # 保存“修改密度之后”的状态
        # --------------------------------------------------

        self._save_snapshot()

        return self.density

    # ==================================================
    # 回退仿真
    # ==================================================

    def rewind(self, steps=1):
        """
        将 World Model 回退指定步数。

        例如：

            Step 10
              ↓
            rewind(3)
              ↓
            Step 7

        注意：

        回退后，
        density 也会恢复到对应历史状态。
        """

        if steps <= 0:
            return 0

        # --------------------------------------------------
        # 当前快照索引
        # --------------------------------------------------

        current_index = (
            len(self.history) - 1
        )

        # --------------------------------------------------
        # 目标快照索引
        # --------------------------------------------------

        target_index = (
            current_index - steps
        )

        # --------------------------------------------------
        # 不能回退到初始状态之前
        # --------------------------------------------------

        if target_index < 0:
            target_index = 0

        # --------------------------------------------------
        # 实际回退步数
        # --------------------------------------------------

        actual_rewind = (
            current_index -
            target_index
        )

        # --------------------------------------------------
        # 恢复 World Model
        # --------------------------------------------------

        self.model = copy.deepcopy(
            self.history[target_index]
        )

        # --------------------------------------------------
        # 同步 Adapter 参数
        # --------------------------------------------------

        self.width = (
            self.model.width
        )

        self.height = (
            self.model.height
        )

        self.density = (
            self.model.density
        )

        # --------------------------------------------------
        # 删除目标状态之后的历史
        # --------------------------------------------------

        self.history = (
            self.history[
                :target_index + 1
            ]
        )

        return actual_rewind

    # ==================================================
    # 获取当前 World State
    # ==================================================

    def get_state(self):
        """
        获取当前森林状态。
        """

        fine = 0
        on_fire = 0
        burned_out = 0

        for agent in self.model.agents:

            if agent.condition == "Fine":

                fine += 1

            elif agent.condition == "On Fire":

                on_fire += 1

            elif agent.condition == "Burned Out":

                burned_out += 1

        return {
            "step": self.model.steps,

            "width": self.model.width,

            "height": self.model.height,

            "density": self.model.density,

            "fine": fine,

            "on_fire": on_fire,

            "burned_out": burned_out,

            "running": self.model.running,
        }
        # ==================================================
    # 渲染当前仿真
    # ==================================================

    def render_png(self, advance=False):
        """
        将当前 Forest Fire World Model 渲染成 PNG。

        advance=False:
            只显示当前状态，不推进仿真。

        advance=True:
            先推进一步，再显示。
        """

        # --------------------------------------------------
        # 是否先推进一步
        # --------------------------------------------------

        if advance:
            self.step(1)

        # --------------------------------------------------
        # 创建画布
        # --------------------------------------------------

        fig, ax = plt.subplots(
            figsize=(7, 7)
        )

        # --------------------------------------------------
        # 网格范围
        # --------------------------------------------------

        ax.set_xlim(
            -0.5,
            self.width - 0.5
        )

        ax.set_ylim(
            -0.5,
            self.height - 0.5
        )

        # --------------------------------------------------
        # 坐标轴
        # --------------------------------------------------

        ax.set_xticks(
            range(self.width)
        )

        ax.set_yticks(
            range(self.height)
        )

        # --------------------------------------------------
        # 网格
        # --------------------------------------------------

        ax.grid(
            True,
            linewidth=0.5,
            alpha=0.25
        )

        # --------------------------------------------------
        # 绘制森林
        # --------------------------------------------------

        for agent in self.model.agents:

            x, y = agent.pos

            # ==================================================
            # 正常树木
            # ==================================================

            if agent.condition == "Fine":

                ax.scatter(
                    x,
                    y,
                    marker="s",
                    s=250,
                    color="green",
                )

            # ==================================================
            # 正在燃烧
            # ==================================================

            elif agent.condition == "On Fire":

                ax.scatter(
                    x,
                    y,
                    marker="s",
                    s=250,
                    color="red",
                )

            # ==================================================
            # 已烧毁
            # ==================================================

            elif agent.condition == "Burned Out":

                ax.scatter(
                    x,
                    y,
                    marker="s",
                    s=250,
                    color="black",
                )

        # --------------------------------------------------
        # 图像比例
        # --------------------------------------------------

        ax.set_aspect(
            "equal"
        )

        # --------------------------------------------------
        # 坐标轴
        # --------------------------------------------------

        ax.set_xlabel(
            "X"
        )

        ax.set_ylabel(
            "Y"
        )

        # --------------------------------------------------
        # 标题
        # --------------------------------------------------

        ax.set_title(
            f"Forest Fire Simulation\n"
            f"Step: {self.model.steps} | "
            f"Density: {self.density:.2f}"
        )

        # --------------------------------------------------
        # 保存为 PNG
        # --------------------------------------------------

        buffer = io.BytesIO()

        fig.savefig(
            buffer,
            format="png",
            bbox_inches="tight",
            dpi=120,
        )

        # --------------------------------------------------
        # 关闭 Matplotlib Figure
        # --------------------------------------------------

        plt.close(fig)

        buffer.seek(0)

        return buffer.getvalue()