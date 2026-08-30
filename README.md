# Agent × World Model

基于 LLM Agent 的自然语言仿真控制系统。

本项目将大语言模型（LLM）、Agent 和 World Model 相结合，使用户可以通过自然语言指令与仿真环境进行交互，并对仿真状态进行控制。

## Demo

用户可以直接使用自然语言控制仿真，例如：

> 让火灾模拟退回 5 步

Agent 会理解用户意图，并将自然语言转换为对应的结构化操作，最终修改仿真环境状态。

## System Architecture

```text
User
  ↓
LLM
  ↓
Intent Understanding
  ↓
Agent / Planner
  ↓
Tool Calling
  ↓
World State
  ↓
Forest Fire Simulation
  ↓
Visualization

Core Features
自然语言理解
LLM Agent
仿真状态管理
仿真步骤控制
Simulation Rollback
Tool Calling
火灾扩散仿真
Streamlit 可视化
Technology Stack
Python
LLM
Agent
LangGraph
Mesa
Streamlit
Project Structure
agent_worldmodel/
├── agent/
│   ├── llm.py
│   ├── planner.py
│   └── tools.py
│
├── simulations/
│   ├── forset_fire.py
│   └── init.py
│
├── tests/
│   └── test_llm.py
│
├── world/
│   ├── graph.py
│   ├── models.py
│   └── state.py
│
├── app.py
├── .gitignore
└── README.md
How to Run
1. Install dependencies
pip install -r requirements.txt
2. Configure API Key

Set your API key through environment variables.

# Windows PowerShell
$env:API_KEY="your_api_key"
3. Run
streamlit run app.py