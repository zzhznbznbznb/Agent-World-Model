import streamlit as st

from world.state import WorldState
from controller.simulation_controller import SimulationController


# =========================================================
# Page Config
# =========================================================

st.set_page_config(
    page_title="Agent × World Model",
    page_icon="🧠",
    layout="wide",
)


# =========================================================
# Session State
# =========================================================

def init_session_state():

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "你好，我是 Agent 助手。\n\n"
                    "你可以直接告诉我想调整的世界模型和仿真参数。\n\n"
                    "例如：把森林火灾密度调高一点，并运行 30 步。"
                ),
            }
        ]

    if "world" not in st.session_state:
        st.session_state.world = WorldState()

    if "custom_world_text" not in st.session_state:
        st.session_state.custom_world_text = ""

    if "simulation_controller" not in st.session_state:
        st.session_state.simulation_controller = (
            SimulationController()
        )

    controller = st.session_state.simulation_controller

    # 第一次启动时生成初始图片
    if "last_simulation_fig" not in st.session_state:
        st.session_state.last_simulation_fig = (
            controller.adapter.render_png(
                advance=False
            )
        )

    if "last_simulation_config" not in st.session_state:
        st.session_state.last_simulation_config = (
            controller.get_config()
        )


# =========================================================
# Initialize
# =========================================================

init_session_state()

controller = st.session_state.simulation_controller


# =========================================================
# Main Layout
# =========================================================

left_col, right_col = st.columns(
    [1.0, 1.8]
)


# =========================================================
# LEFT : AGENT
# =========================================================

with left_col:

    st.subheader("Agent Console")

    st.caption("World Model Controller · Ready")

    st.divider()

    # -----------------------------------------------------
    # Chat History
    # -----------------------------------------------------

    for message in st.session_state.messages:

        if message["role"] == "user":

            left, right = st.columns(
                [1, 4]
            )

            with right:

                st.caption("You")

                with st.container(
                    border=True
                ):
                    st.write(
                        message["content"]
                    )

        else:

            left, right = st.columns(
                [4,1]
            )

            with left:

                st.caption("Agent")

                with st.container(
                    border=True
                ):
                    st.write(
                        message["content"]
                    )


    # -----------------------------------------------------
    # Chat Input
    # -----------------------------------------------------

    prompt = st.chat_input(
        "输入你的任务，例如：把森林火灾密度调高，并运行 30 步"
    )


    if prompt and prompt.strip():

        user_text = prompt.strip()

        # -------------------------------------------------
        # 保存用户消息
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        try:

            # -------------------------------------------------
            # Controller 统一处理
            # -------------------------------------------------

            result = controller.process(
                user_text
            )

            response_text = result.get(
                "reply",
                "任务已执行。",
            )

            # -------------------------------------------------
            # 保存 Agent 回复
            # -------------------------------------------------

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response_text,
                }
            )

            # -------------------------------------------------
            # 更新仿真图片
            # -------------------------------------------------

            st.session_state.last_simulation_fig = (
                controller.adapter.render_png(
                    advance=False
                )
            )

            # -------------------------------------------------
            # 更新配置
            # -------------------------------------------------

            st.session_state.last_simulation_config = (
                controller.get_config()
            )

        except Exception as e:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "执行任务时发生错误：\n\n"
                        f"{str(e)}"
                    ),
                }
            )

        st.rerun()


# =========================================================
# RIGHT : WORLD MODEL
# =========================================================

with right_col:

    st.title("Simulation")


    # =====================================================
    # Forest Fire
    # =====================================================

    st.subheader(
        "Forest Fire 仿真"
    )


    # =====================================================
    # Current Config
    # =====================================================

    active_cfg = controller.get_config()


    st.caption(
        f"当前参数："
        f"密度 {active_cfg['density']:.2f} | "
        f"Step {active_cfg['steps']} | "
        f"网格 "
        f"{active_cfg['width']}×"
        f"{active_cfg['height']}"
    )


    # =====================================================
    # Regenerate Button
    # =====================================================

    if st.button(
        "重新生成仿真图",
        use_container_width=True,
    ):

        try:

            st.session_state.last_simulation_fig = (
                controller.adapter.render_png(
                    advance=False
                )
            )

            st.session_state.last_simulation_config = (
                controller.get_config()
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"重新生成仿真图失败：{str(e)}"
            )


    # =====================================================
    # Simulation + World State
    # =====================================================

    simulation_col, state_col = st.columns(
        [5, 1]
    )


    # =====================================================
    # LEFT : Simulation Image
    # =====================================================

    with simulation_col:

        if st.session_state.last_simulation_fig is not None:

            st.image(
                st.session_state.last_simulation_fig,
                caption=None,
                use_container_width=True,
            )

        else:

            st.info(
                "输入需求后，这里会显示 Forest Fire 仿真结果。"
            )


    # =====================================================
    # RIGHT : World State
    # =====================================================

    with state_col:

        st.markdown(
            "### World State"
        )

        state = controller.get_state()

        st.caption(
            f"Step  {state['step']}"
        )

        st.caption(
            f"Density  {state['density']:.2f}"
        )

        st.caption(
            f"Fine  {state['fine']}"
        )

        st.caption(
            f"On Fire  {state['on_fire']}"
        )

        st.caption(
            f"Burned Out  {state['burned_out']}"
        )

        st.caption(
            f"Grid  {state['width']} × {state['height']}"
        )
