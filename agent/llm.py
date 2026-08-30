from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

import requests

# 短期项目里直接写在这里最方便；以后改 key / 地址 / 模型时只需要改这里。
# DEFAULT_OPENCODE_GO_API_KEY = "your-opencode-go-key"
# DEFAULT_OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go/v1"
DEFAULT_HF_API_KEY = "your-huggingface-token"
DEFAULT_HF_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_MODEL = "deepseek-ai/DeepSeek-V4-Flash"


class SimpleLLM:
    """一个轻量级 LLM 框架骨架，用于模拟对话与任务解析。"""

    @staticmethod
    def _requested_steps(text: str) -> int | None:
        match = re.search(
            r"(?:前进|推进|运行|演化|模拟|执行|向前)\s*(\d+)\s*步",
            text,
        )
        if match:
            return int(match.group(1))
        chinese_digits = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        }
        match = re.search(
            r"(?:前进|推进|运行|演化|模拟|执行|向前)\s*([一二三四五六七八九十]+)\s*步",
            text,
        )
        return chinese_digits.get(match.group(1)) if match else None

    @staticmethod
    def _default_sim_config(
        prompt: str,
        current_config: Dict[str, float | int] | None = None,
    ) -> Dict[str, float | int]:
        text = (prompt or "").lower()
        current = current_config or {}
        density = float(current.get("density", 0.65))
        steps = int(current.get("steps", 20))
        width = int(current.get("width", 20))
        height = int(current.get("height", 20))

        if "高" in text or "大" in text or "密集" in text:
            density = 0.8
        elif "低" in text or "稀疏" in text or "轻" in text:
            density = 0.4

        requested_steps = SimpleLLM._requested_steps(text)
        if requested_steps is not None:
            steps = requested_steps
        elif "30" in text or "很多" in text or "长" in text:
            steps = 30
        elif "10" in text or "短" in text:
            steps = 10

        if "16" in text:
            width = 16
            height = 16
        elif "25" in text:
            width = 25
            height = 25

        config = {
            "width": width,
            "height": height,
            "density": density,
            "steps": steps,
        }
        rewind_match = re.search(r"(?:退回|后退|向后退|回退)\s*(\d+)\s*步", text)
        if rewind_match:
            config["rewind_steps"] = int(rewind_match.group(1))
        if "空地" in text and ("右下" in text or "东南" in text):
            config["clear_area"] = "bottom_right"
        if "向东" in text or "东风" in text or "风向东" in text or "右吹" in text:
            config["wind_direction"] = "east"
        elif "向西" in text or "西风" in text or "风向西" in text or "左吹" in text:
            config["wind_direction"] = "west"
        elif "向北" in text or "北风" in text or "风向北" in text or "上吹" in text:
            config["wind_direction"] = "north"
        elif "向南" in text or "南风" in text or "风向南" in text or "下吹" in text:
            config["wind_direction"] = "south"
        return config

    @staticmethod
    def _extract_json_object(text: str) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in AI response.")

        candidate = match.group(0)
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)

        payload = json.loads(candidate)
        if not isinstance(payload, dict):
            raise ValueError("AI response is not an object.")
        return payload

    def _call_deepseek(
        self,
        user_input: str,
        current_config: Dict[str, float | int] | None = None,
    ) -> Dict[str, Any]:
        api_key = (
            os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACEHUB_API_TOKEN")
            or os.getenv("DEEPSEEK_API_KEY")
            or DEFAULT_HF_API_KEY
        )
        base_url = (
            os.getenv("HF_BASE_URL")
            or DEFAULT_HF_BASE_URL
        )
        model_name = (
            os.getenv("HF_MODEL")
            or os.getenv("DEEPSEEK_MODEL")
            or DEFAULT_MODEL
        )

        if api_key == "your-huggingface-token":
            raise RuntimeError(
                "请先在 agent/llm.py 里替换 DEFAULT_HF_API_KEY，"
                "或者设置 HF_TOKEN 环境变量。"
            )

        url = base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是一个仿真参数编排助手。请严格按照 JSON 格式返回："
                            "{\"reply\": string, \"density\": number, \"steps\": int, \"width\": int, \"height\": int, \"wind_direction\": string}. "
                            "reply 是简短中文说明，density 在 0.2 到 0.9，steps 在 1 到 60，width/height 在 10 到 30。"
                            "只返回 JSON，不要有 Markdown 代码块或额外文本。"
                            f"当前仿真参数是 {current_config or {'density': 0.65, 'steps': 20, 'width': 20, 'height': 20}}。"
                            "用户没有明确要求修改的仿真参数必须保持当前值；只有用户明确提出仿真变化时才修改参数。"
                            "wind_direction 只能是 none、east、west、north、south。"
                        ),
                    },
                    {"role": "user", "content": user_input},
                ],
                "temperature": 0.2,
                "stream": False,
            },
            timeout=40,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"LLM API error: {response.status_code} {response.text[:200]}"
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = self._extract_json_object(content)
        current = current_config or {
            "width": 20,
            "height": 20,
            "density": 0.65,
            "steps": 20,
        }

        sim_cfg = {
            "width": int(parsed.get("width", current["width"])),
            "height": int(parsed.get("height", current["height"])),
            "density": float(parsed.get("density", current["density"])),
            "steps": int(parsed.get("steps", current["steps"])),
        }
        if "空地" in user_input and ("右下" in user_input or "东南" in user_input):
            sim_cfg["clear_area"] = "bottom_right"
            sim_cfg["width"] = current["width"]
            sim_cfg["height"] = current["height"]
            sim_cfg["density"] = current["density"]
            sim_cfg["steps"] = current["steps"]
        direction = parsed.get("wind_direction")
        sim_cfg["wind_direction"] = (
            direction if direction in {"none", "east", "west", "north", "south"}
            else current.get("wind_direction", "none")
        )
        if "向东" in user_input or "东风" in user_input or "风向东" in user_input or "右吹" in user_input:
            sim_cfg["wind_direction"] = "east"
        elif "向西" in user_input or "西风" in user_input or "风向西" in user_input or "左吹" in user_input:
            sim_cfg["wind_direction"] = "west"
        elif "向北" in user_input or "北风" in user_input or "风向北" in user_input or "上吹" in user_input:
            sim_cfg["wind_direction"] = "north"
        elif "向南" in user_input or "南风" in user_input or "风向南" in user_input or "下吹" in user_input:
            sim_cfg["wind_direction"] = "south"
        rewind_match = re.search(r"(?:退回|后退|向后退|回退)\s*(\d+)\s*步", user_input)
        if rewind_match:
            sim_cfg["rewind_steps"] = int(rewind_match.group(1))
        requested_steps = self._requested_steps(user_input)
        if requested_steps is not None:
            sim_cfg["steps"] = requested_steps
        direction = parsed.get("wind_direction")
        if direction in {"none", "east", "west", "north", "south"}:
            sim_cfg["wind_direction"] = direction
        else:
            sim_cfg["wind_direction"] = current.get("wind_direction", "none")

        if not 0.2 <= sim_cfg["density"] <= 0.9:
            sim_cfg["density"] = 0.65
        if not 1 <= sim_cfg["steps"] <= 60:
            sim_cfg["steps"] = int(current["steps"])

        return {"reply": str(parsed.get("reply", "已更新仿真参数。")), **sim_cfg}

    def respond(
        self,
        user_input: str,
        world_state: Any,
        return_metadata: bool = False,
        current_config: Dict[str, float | int] | None = None,
    ):
        text = (user_input or "").strip()
        if not text:
            fallback = "我还没有收到你要执行的任务。"
            sim_cfg = self._default_sim_config(text, current_config)
            return (fallback, sim_cfg) if return_metadata else fallback

        try:
            payload = self._call_deepseek(text, current_config)
            reply = payload.get("reply", "我已更新世界模型。")
            sim_cfg = {
                "width": int(payload.get("width", (current_config or {}).get("width", 20))),
                "height": int(payload.get("height", (current_config or {}).get("height", 20))),
                "density": float(payload.get("density", (current_config or {}).get("density", 0.65))),
                "steps": int(payload.get("steps", (current_config or {}).get("steps", 20))),
                "wind_direction": payload.get("wind_direction", (current_config or {}).get("wind_direction", "none")),
            }
            if payload.get("clear_area"):
                sim_cfg["clear_area"] = payload["clear_area"]
            if payload.get("rewind_steps") is not None:
                sim_cfg["rewind_steps"] = int(payload["rewind_steps"])
        except Exception:
            reply = (
                f"已接收需求：{text}。\n"
                "我会先抽象目标、约束和关键实体，再更新当前的世界状态。"
            )
            sim_cfg = self._default_sim_config(text, current_config)

        return (reply, sim_cfg) if return_metadata else reply
