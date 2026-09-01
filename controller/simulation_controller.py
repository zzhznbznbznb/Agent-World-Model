from agent.llm import SimpleLLM
from simulations.forest_fire.adapter import ForestFireAdapter


class SimulationController:
    """
    Simulation Controller

    负责：
    1. 接收用户需求
    2. 调用 LLM 理解需求
    3. 控制当前 World Model
    4. 保持 World Model 持续存在
    5. 支持推进和回退
    6. 支持在当前世界状态上修改参数

    核心原则：

        修改参数 != 重新创建 World Model

    例如：

        Step 10
          ↓
        用户：增加森林密度
          ↓
        当前 Step 10 的森林直接增加树木
          ↓
        仍然是 Step 10
    """

    def __init__(self):

        self.llm = SimpleLLM()

        self.config = {
            "width": 30,
            "height": 30,
            "density": 0.65,
            "steps": 0,
            "wind_direction": "none",
        }

        # ==================================================
        # 只创建一次 World Model
        # ==================================================

        self.adapter = ForestFireAdapter(
            width=self.config["width"],
            height=self.config["height"],
            density=self.config["density"],
        )

    # ==================================================
    # 获取当前世界状态
    # ==================================================

    def get_state(self):

        return self.adapter.get_state()

    # ==================================================
    # 获取当前配置
    # ==================================================

    def get_config(self):

        return {
            "width": self.adapter.width,
            "height": self.adapter.height,
            "density": self.adapter.density,
            "steps": self.adapter.model.steps,
            "wind_direction": getattr(
                self.adapter,
                "wind_direction",
                "none",
            ),
        }

    # ==================================================
    # 处理用户需求
    # ==================================================

    def process(self, user_input):

        # --------------------------------------------------
        # 1. 获取当前世界状态
        # --------------------------------------------------

        current_state = self.adapter.get_state()

        # --------------------------------------------------
        # 2. 获取当前配置
        # --------------------------------------------------

        current_config = self.get_config()

        # --------------------------------------------------
        # 3. LLM 理解用户需求
        # --------------------------------------------------

        reply, sim_cfg = self.llm.respond(
            user_input,
            current_state,
            return_metadata=True,
            current_config=current_config,
        )

        # ==================================================
        # 4. 回退
        # ==================================================

        rewind_steps = int(
            sim_cfg.get("rewind_steps", 0)
        )

        if rewind_steps > 0:

            actual_rewind = self.adapter.rewind(
                rewind_steps
            )

            state = self.adapter.get_state()

            return {
                "reply": reply,
                "config": self.get_config(),
                "state": state,
                "actual_steps": 0,
                "rewind_steps": actual_rewind,
            }

        # ==================================================
        # 5. 修改当前世界参数
        # ==================================================

        # --------------------------------------------------
        # Density
        # --------------------------------------------------

        if "density" in sim_cfg:

            new_density = float(
                sim_cfg["density"]
            )

            current_density = float(
                self.adapter.density
            )

            if abs(new_density - current_density) > 1e-6:

                self.adapter.set_density(
                    new_density
                )

        # --------------------------------------------------
        # Wind
        # --------------------------------------------------

        if "wind_direction" in sim_cfg:

            wind_direction = sim_cfg[
                "wind_direction"
            ]

            if hasattr(
                self.adapter,
                "set_wind_direction",
            ):

                self.adapter.set_wind_direction(
                    wind_direction
                )

        # --------------------------------------------------
        # Clear Area
        # --------------------------------------------------

        if sim_cfg.get("clear_area"):

            if hasattr(
                self.adapter,
                "clear_area",
            ):

                self.adapter.clear_area(
                    sim_cfg["clear_area"]
                )

        # ==================================================
        # 6. 推进仿真
        # ==================================================

        requested_steps = int(
            sim_cfg.get("steps", 0)
        )

        actual_steps = 0

        if requested_steps > 0:

            actual_steps = self.adapter.step(
                requested_steps
            )

        # ==================================================
        # 7. 更新 Controller 配置
        # ==================================================

        self.config["width"] = (
            self.adapter.width
        )

        self.config["height"] = (
            self.adapter.height
        )

        self.config["density"] = (
            self.adapter.density
        )

        self.config["steps"] = (
            self.adapter.model.steps
        )

        self.config["wind_direction"] = (
            getattr(
                self.adapter,
                "wind_direction",
                "none",
            )
        )

        # ==================================================
        # 8. 获取最终状态
        # ==================================================

        state = self.adapter.get_state()

        # ==================================================
        # 9. 返回
        # ==================================================

        return {
            "reply": reply,
            "config": self.config.copy(),
            "state": state,
            "actual_steps": actual_steps,
            "rewind_steps": 0,
        }
