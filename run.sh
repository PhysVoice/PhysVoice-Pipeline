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

# voice 파이프라인 → Task ID → bridge 라우팅 → lerobot-record 추론
#   인자는 그대로 bridge.main 으로 전달됨:
#     bash run.sh                 로컬 마이크
#     bash run.sh --network       노트북 마이크(TCP)
#     bash run.sh --dry-run       로봇 없이 명령만 출력(테스트)
exec python -m bridge.main "$@"
