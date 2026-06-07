#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# PhysVoice-Pipeline 통합 실행
#   음성 인식(voice) → Task ID → bridge → lerobot 추론 → SO101
#
#   bash run.sh
#
# 전제: bash setup.sh 로 .venv 가 준비되어 있어야 함.
# ─────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[오류] .venv 가 없습니다. 먼저 'bash setup.sh' 를 실행하세요." >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# TODO(구현 단계): bridge 엔트리포인트 연결
#   - voice 파이프라인이 Task ID 출력
#   - bridge 가 수신 → task_map.yaml 라우팅 → lerobot-record 호출
# 예) python -m bridge.main --config config/task_map.yaml --robot config/robot_profile.yaml
echo "[run] 아직 엔트리포인트 미구현 — bridge/ 채운 뒤 이 부분 연결 예정."
