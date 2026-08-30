import base64
import streamlit as st
from html import escape

from agent.llm import SimpleLLM
from agent.planner import Planner
from world.state import WorldState
from simulations.forset_fire import ForestFireAdapter


# =========================================================
# Page Config
# =========================================================

st.set_page_config(
    page_title="Agent × World Model",
    page_icon="🧠",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       Global
       ===================================================== */

    html,
    body,
    [data-testid="stAppViewContainer"],
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
        background: #0b1020 !important;
    }

    header[data-testid="stHeader"] {
        display: none !important;
    }

    div[data-testid="stDecoration"] {
        display: none !important;
    }

    .block-container {
        width: 100% !important;
        max-width: 100% !important;

        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;

        margin: 0 !important;
    }


    /* =====================================================
       Main Columns
       ===================================================== */

    div[data-testid="stHorizontalBlock"] {
        gap: 1.2rem !important;
        align-items: flex-start !important;
        width: 100% !important;
    }

    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
    }


    /* =====================================================
       Titles
       ===================================================== */

    .section-title {
        color: #e5edf8 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;

        margin: 0 0 0.7rem 0 !important;
        padding: 0 !important;
    }

    .subsection-title {
        color: #e5edf8 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;

        margin-top: 0.8rem !important;
        margin-bottom: 0.5rem !important;
    }


    /* =====================================================
       CHAT WINDOW
       ===================================================== */

    .agent-shell {
        height: 77vh !important;
        min-height: 640px !important;
        display: flex !important;
        flex-direction: column !important;
        background: linear-gradient(180deg, #0f172a 0%, #101827 100%) !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        border-radius: 20px !important;
        overflow: hidden !important;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.28) !important;
    }

    .agent-header {
        padding: 0.9rem 1rem !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.14) !important;
        background: rgba(15, 23, 42, 0.96) !important;
    }

    .agent-title-row {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }

    .agent-avatar {
        width: 36px !important;
        height: 36px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: linear-gradient(135deg, #60a5fa, #2563eb) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    .agent-name {
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        color: #e5edf8 !important;
    }

    .agent-status {
        color: #94f0c5 !important;
        font-size: 0.72rem !important;
        margin-top: 0.15rem !important;
    }

    .agent-body {
        flex: 1 1 auto !important;
        overflow-y: auto !important;
        padding: 1rem 0.9rem !important;
        background: rgba(15, 23, 42, 0.38) !important;
    }

    .message-row {
        display: flex !important;
        align-items: flex-start !important;
        gap: 0.7rem !important;
        margin-bottom: 0.9rem !important;
    }

    .message-row.user {
        justify-content: flex-end !important;
    }

    .message-avatar {
        width: 28px !important;
        height: 28px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 0.75rem !important;
        flex-shrink: 0 !important;
    }

    .message-avatar.assistant {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important;
    }

    .message-avatar.user {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
        color: white !important;
    }

    .message-content {
        max-width: 82% !important;
    }

    .message-row.user .message-content {
        max-width: 78% !important;
    }

    .message-label {
        color: #cbd5e1 !important;
        font-size: 0.72rem !important;
        margin: 0 0 0.35rem 0.1rem !important;
    }

    .message-bubble {
        padding: 0.8rem 0.95rem !important;
        border-radius: 16px !important;
        line-height: 1.65 !important;
        font-size: 0.96rem !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12) !important;
    }

    .message-bubble.assistant {
        background: rgba(17, 24, 39, 0.98) !important;
        color: #e5edf8 !important;
        border: 1px solid rgba(148, 163, 184, 0.16) !important;
        border-radius: 16px 16px 16px 6px !important;
    }

    .message-bubble.user {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.32), rgba(59, 130, 246, 0.18)) !important;
        color: #e5edf8 !important;
        border: 1px solid rgba(96, 165, 250, 0.28) !important;
        border-radius: 16px 16px 6px 16px !important;
    }

    .chat-input-wrap {
        border-top: 1px solid rgba(148, 163, 184, 0.15) !important;
        background: rgba(15, 23, 42, 0.9) !important;
        padding: 0.75rem !important;
    }

    .chat-input-wrap .stChatInput {
        margin-top: 0 !important;
    }


    /* =====================================================
       File Uploader
       ===================================================== */

    div[data-testid="stFileUploaderDropzone"] {
        background: #111a2e !important;

        border: 1px solid rgba(148, 163, 184, 0.3) !important;

        border-radius: 12px !important;

        color: #e5edf8 !important;
    }


    /* =====================================================
       Button
       ===================================================== */

    .stButton > button {
        width: 100% !important;

        background: #131d34 !important;

        color: #e5edf8 !important;

        border: 1px solid rgba(148, 163, 184, 0.3) !important;

        border-radius: 10px !important;

        min-height: 42px !important;
    }

    .stButton > button:hover {
        border-color: rgba(96, 165, 250, 0.7) !important;

        background: #18243d !important;
    }


    /* =====================================================
       Success
       ===================================================== */

    .stSuccess {
        background: rgba(21, 128, 61, 0.18) !important;

        border: 1px solid rgba(34, 197, 94, 0.35) !important;

        color: #dcfce7 !important;
    }


    /* =====================================================
       Code
       ===================================================== */

    .stCode {
        background: #111827 !important;

        border: 1px solid rgba(148, 163, 184, 0.2) !important;

        color: #dbeafe !important;

        max-height: 300px !important;

        overflow: auto !important;
    }


    /* =====================================================
       Simulation Image
       ===================================================== */

    .simulation-image-wrap {
        width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        overflow: hidden !important;
        border-radius: 12px !important;
    }

    .simulation-image-wrap img {
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18) !important;
    }


    /* =====================================================
       Text Color
       ===================================================== */

    h1,
    h2,
    h3,
    h4,
    p,
    label,
    span {
        color: #e5edf8 !important;
    }


    /* =====================================================
       Responsive
       ===================================================== */

    @media (max-width: 900px) {

        .block-container {
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.7rem !important;
            flex-direction: column !important;
        }

        div[data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }

        .section-title {
            font-size: 1.35rem !important;
        }

    }

    @media (min-width: 1400px) {
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            flex: 1.8 1 0 !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Prompt → Simulation Config
# =========================================================

def parse_prompt_to_sim_config(prompt: str):

    prompt = (prompt or "").lower()

    density = 0.65
    steps = 20

    width = 20
    height = 20

    # Density
    if (
        "高" in prompt
        or "大" in prompt
        or "密集" in prompt
    ):
        density = 0.8

    elif (
        "低" in prompt
        or "稀疏" in prompt
        or "轻" in prompt
    ):
        density = 0.4

    # Steps
    if (
        "30" in prompt
        or "很多" in prompt
        or "长" in prompt
    ):
        steps = 30

    elif (
        "10" in prompt
        or "短" in prompt
    ):
        steps = 10

    return {
        "width": width,
        "height": height,
        "density": density,
        "steps": steps,
    }


def update_simulation(adapter, sim_cfg):
    next_config = {
        "width": int(sim_cfg.get("width", adapter.width)),
        "height": int(sim_cfg.get("height", adapter.height)),
        "density": float(sim_cfg.get("density", adapter.density)),
        "steps": int(sim_cfg.get("steps", adapter.steps)),
        "wind_direction": sim_cfg.get("wind_direction", adapter.wind_direction),
    }
    current_config = {
        "width": adapter.width,
        "height": adapter.height,
        "density": adapter.density,
        "steps": adapter.steps,
        "wind_direction": adapter.wind_direction,
    }

    if next_config == current_config:
        return False

    adapter.apply_config(
        width=next_config["width"],
        height=next_config["height"],
        density=next_config["density"],
        steps=next_config["steps"],
        wind_direction=next_config["wind_direction"],
    )
    return True


# =========================================================
# Session State
# =========================================================

def init_session_state():

    # -----------------------------------------------------
    # Chat
    # -----------------------------------------------------

    if "messages" not in st.session_state:

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "你好，我是 Agent 助手。\n\n"
                    "你可以直接告诉我想调整的世界模型和仿真参数，"
                    "例如：\"把森林火灾密度调高一点，并运行 30 步\"。"
                ),
            }
        ]

    # -----------------------------------------------------
    # World
    # -----------------------------------------------------

    if "world" not in st.session_state:

        st.session_state.world = WorldState()

    # -----------------------------------------------------
    # Custom World Model
    # -----------------------------------------------------

    if "custom_world_text" not in st.session_state:

        st.session_state.custom_world_text = ""

    # -----------------------------------------------------
    # Simulation
    # -----------------------------------------------------

    if "forest_adapter" not in st.session_state:

        st.session_state.forest_adapter = ForestFireAdapter(
            width=20,
            height=20,
            density=0.65,
            steps=20,
            seed=42,
            wind_direction="none",
        )

    if "last_simulation_fig" not in st.session_state:

        st.session_state.last_simulation_fig = (
            st.session_state.forest_adapter.render_png(advance=False)
        )

    if "last_simulation_config" not in st.session_state:
        adapter = st.session_state.forest_adapter
        st.session_state.last_simulation_config = {
            "width": adapter.width,
            "height": adapter.height,
            "density": adapter.density,
            "steps": adapter.steps,
            "wind_direction": adapter.wind_direction,
        }


# =========================================================
# Initialize
# =========================================================

init_session_state()


# =========================================================
# Agent / Planner
# =========================================================

llm = SimpleLLM()

planner = Planner()


# =========================================================
# Main Layout
# =========================================================

left_col, right_col = st.columns(
    [1.0, 1.8],
    vertical_alignment="top",
)


# =========================================================
# LEFT : AGENT
# =========================================================

with left_col:
    chat_box = st.container(border=True)

    with chat_box:
        st.markdown(
            '''
            <div class="agent-header">
                <div class="agent-title-row">
                    <div class="agent-avatar">AI</div>
                    <div>
                        <div class="agent-name">Agent</div>
                        <div class="agent-status">在线</div>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="agent-body">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            role = message["role"]
            content = escape((message["content"] or "")).replace("\n", "<br>")

            if role == "user":
                st.markdown(
                    f'''
                    <div class="message-row user">
                        <div class="message-content">
                            <div class="message-label">You</div>
                            <div class="message-bubble user">{content}</div>
                        </div>
                        <div class="message-avatar user">U</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'''
                    <div class="message-row assistant">
                        <div class="message-avatar assistant">AI</div>
                        <div class="message-content">
                            <div class="message-label">Agent</div>
                            <div class="message-bubble assistant">{content}</div>
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)

        prompt = st.chat_input("输入你的任务，例如：把森林火灾密度调高，并运行 30 步")

        if prompt and prompt.strip():
            user_text = prompt.strip()
            st.session_state.messages.append({"role": "user", "content": user_text})
            adapter = st.session_state.forest_adapter
            current_config = {
                "width": adapter.width,
                "height": adapter.height,
                "density": adapter.density,
                "steps": adapter.steps,
                "wind_direction": adapter.wind_direction,
            }
            response_text, sim_cfg = llm.respond(
                user_text,
                st.session_state.world,
                return_metadata=True,
                current_config=current_config,
            )
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            updates = planner.plan(user_text, st.session_state.world)
            st.session_state.world.apply_updates(updates)

            rewind_steps = int(sim_cfg.get("rewind_steps", 0))
            rewound = adapter.rewind(rewind_steps) if rewind_steps else False
            simulation_changed = False if rewound else update_simulation(adapter, sim_cfg)
            area_cleared = False if rewound else adapter.clear_area(sim_cfg.get("clear_area"))
            st.session_state.last_simulation_config = {
                "width": adapter.width,
                "height": adapter.height,
                "density": adapter.density,
                "steps": adapter.steps,
                "wind_direction": adapter.wind_direction,
            }

            if simulation_changed or area_cleared or rewound:
                st.session_state.last_simulation_fig = adapter.render_png(
                    advance=simulation_changed
                )
            st.rerun()


# =========================================================
# RIGHT : WORLD MODEL
# =========================================================

with right_col:

    st.markdown(
        '<div class="section-title">仿真模型</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Upload World Model
    # -----------------------------------------------------

    uploaded = st.file_uploader(
        "上传你的世界模型文件（可选）",

        type=[
            "json",
            "yaml",
            "yml",
            "txt",
        ],

        help=(
            "如果你还没下载世界模型，可以先用默认示例；"
            "之后可以直接替换成你的真实模型。"
        ),
    )

    # -----------------------------------------------------
    # Uploaded File
    # -----------------------------------------------------

    if uploaded is not None:

        st.session_state.custom_world_text = (
            uploaded
            .read()
            .decode(
                "utf-8",
                errors="ignore",
            )
        )

        st.success(
            "已加载自定义世界模型文件。"
        )

        st.code(
            st.session_state.custom_world_text[:2000],
            language="text",
        )

    # -----------------------------------------------------
    # Forest Fire
    # -----------------------------------------------------

    st.markdown(
        '<div class="subsection-title">Forest Fire 仿真</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Regenerate
    # -----------------------------------------------------

    if st.button(
        "重新生成仿真图"
    ):

        sim_cfg = parse_prompt_to_sim_config(
            "森林火灾密度高一点"
        )

        adapter = st.session_state.forest_adapter
        update_simulation(adapter, sim_cfg)
        st.session_state.last_simulation_config = {
            "width": adapter.width,
            "height": adapter.height,
            "density": adapter.density,
            "steps": adapter.steps,
        }
        st.session_state.last_simulation_fig = adapter.render_png()

    # -----------------------------------------------------
    # Simulation Image
    # -----------------------------------------------------

    if (
        st.session_state.last_simulation_fig
        is not None
    ):

        active_cfg = st.session_state.last_simulation_config
        st.caption(
            f"当前参数：密度 {active_cfg['density']:.2f}，"
            f"步数 {active_cfg['steps']}，"
            f"网格 {active_cfg['width']}×{active_cfg['height']}"
        )

        encoded = base64.b64encode(st.session_state.last_simulation_fig).decode("utf-8")
        st.markdown(
            f'''
            <div class="simulation-image-wrap">
                <img src="data:image/png;base64,{encoded}" alt="Forest Fire Simulation" />
            </div>
            ''',
            unsafe_allow_html=True,
        )

    else:

        st.caption(
            "输入需求后，右侧这里会展示 Forest Fire 仿真结果。"
        )
