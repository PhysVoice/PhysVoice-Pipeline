"""
router — Task ID → (정책, 영어 task) 라우팅

voice 가 뽑은 Task ID 를 config/task_map.yaml 로 조회해
실행 가능한 명령인지 판정하고, 정책 경로와 영어 task 문자열로 변환한다.
매핑에 없거나 미인식(TASK_UNKNOWN)이면 "미지원"으로 처리.
"""

from dataclasses import dataclass

import yaml


@dataclass
class Resolution:
    """라우팅 결과."""
    supported: bool
    task_id: str
    policy: str | None = None
    task: str | None = None
    reason: str = ""


class Router:
    def __init__(self, task_map_path: str):
        try:
            with open(task_map_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"task_map 파일을 찾을 수 없습니다: {task_map_path}\n"
                f"  --task-map 경로를 확인하거나 config/task_map.yaml 을 생성하세요."
            ) from e
        self.tasks: dict = data.get("tasks", {}) or {}
        if not self.tasks:
            print(f"[router][경고] task_map 에 정의된 task 가 없습니다: {task_map_path}")

    def resolve(self, task_id: str) -> Resolution:
        if not task_id or task_id == "TASK_UNKNOWN":
            return Resolution(False, task_id or "TASK_UNKNOWN",
                              reason="명령 미인식 (TASK_UNKNOWN)")

        entry = self.tasks.get(task_id)
        if not entry:
            return Resolution(False, task_id,
                              reason=f"매핑된 정책 없음 — 미지원 명령 ({task_id})")

        policy = entry.get("policy")
        task = entry.get("task")
        if not policy or not task:
            return Resolution(False, task_id,
                              reason=f"task_map 항목 불완전 ({task_id}): policy/task 누락")

        return Resolution(True, task_id, policy=policy, task=task, reason="ok")
