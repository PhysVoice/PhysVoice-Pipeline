#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# PhysVoice-Pipeline 환경 설치 (PC마다 1회)
#
#   git clone https://github.com/PhysVoice/PhysVoice-Pipeline.git
#   cd PhysVoice-Pipeline
#   bash setup.sh
#
# 하는 일:
#   1) 전용 가상환경(.venv) 생성  ← PC에 이미 lerobot 있어도 격리됨
#   2) 음성/bridge 의존성 설치 (requirements.txt)
#   3) lerobot 핀 커밋 + smolvla extra 설치
# ─────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")"

# lerobot 고정 버전 — PhysVoice/lerobot 포크 (huggingface@60efd875 + 추론 패치)
#   패치: SmolVLA forward-compat config(정책 로딩 필수) + SO101 카메라 read 타임아웃
#   pristine huggingface 로는 학습 체크포인트 로딩이 DecodingError 로 깨지므로 포크 사용.
LEROBOT_REPO="https://github.com/PhysVoice/lerobot.git"
LEROBOT_COMMIT="19cb4ff5636b1c4f782e9315f565050c1cee3d5a"
PY="${PYTHON:-python3}"

echo "=== [1/3] 가상환경 생성 (.venv) ==="
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip

echo "=== [2/3] 음성/bridge 의존성 설치 ==="
pip install -r requirements.txt

echo "=== [3/3] lerobot 설치 (PhysVoice 포크 핀: ${LEROBOT_COMMIT:0:8}, smolvla) ==="
pip install "lerobot[smolvla] @ git+${LEROBOT_REPO}@${LEROBOT_COMMIT}"

echo
echo "=== 설치 완료 ==="
echo "  - 가상환경:   source .venv/bin/activate"
echo "  - 실행:       bash run.sh"
echo
echo "  ※ 시스템 패키지가 없으면 먼저 설치:"
echo "      sudo apt install ffmpeg portaudio19-dev libsndfile1"
echo "  ※ GPU(CUDA) 환경이면 torch가 자동으로 맞춰지지만,"
echo "      특정 CUDA 버전이 필요하면 그때 torch를 수동 재설치하세요."
