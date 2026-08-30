from __future__ import annotations

from typing import Any, Dict, List


class Planner:
    """把用户需求转成世界模型更新的计划。"""

    def plan(self, user_input: str, world_state: Any) -> Dict[str, List]:
        text = user_input.strip()
        updates = {"entities": [], "relations": []}

        if not text:
            return updates

        entity_name = "Task"
        if "开发" in text or "代码" in text or "写" in text:
            entity_name = "CodingTask"
        elif "分析" in text or "研究" in text or "调研" in text:
            entity_name = "ResearchTask"
        elif "计划" in text or "安排" in text:
            entity_name = "PlanTask"

        updates["entities"].append({
            "name": entity_name,
            "type": "task",
            "status": "active",
            "description": text,
        })

        updates["relations"].append(("Agent", entity_name))
        updates["relations"].append((entity_name, "World"))

        return updates
