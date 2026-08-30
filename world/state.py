from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class WorldState:
    entities: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            "Agent": {"type": "agent", "status": "ready"},
            "Goal": {"type": "objective", "status": "pending"},
            "World": {"type": "environment", "status": "stable"},
        }
    )
    relations: List[Tuple[str, str]] = field(
        default_factory=lambda: [("Agent", "Goal"), ("Goal", "World")]
    )

    def summary_markdown(self) -> str:
        return (
            "- **状态**: 初始世界模型已创建\n"
            f"- **实体数**: {len(self.entities)}\n"
            f"- **关系数**: {len(self.relations)}\n"
            "- **说明**: 这里可以扩展为更真实的任务状态、资源分配和环境变化。"
        )

    def apply_updates(self, updates: Dict[str, List]) -> None:
        for entity in updates.get("entities", []):
            name = entity.get("name")
            if not name:
                continue
            self.entities[name] = {
                "type": entity.get("type", "task"),
                "status": entity.get("status", "active"),
                "description": entity.get("description", ""),
            }

        for src, dst in updates.get("relations", []):
            if (src, dst) not in self.relations:
                self.relations.append((src, dst))
