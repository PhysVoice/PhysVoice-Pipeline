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
#   4) torchaudio 설치 (Silero VAD 의존성, lerobot 의 torch 버전·CUDA 에 매칭)
# ─────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")"

# lerobot 고정 버전 — PhysVoice/lerobot 포크 (huggingface@60efd875 + 추론 패치)
#   패치: SmolVLA forward-compat config(정책 로딩 필수) + SO101 카메라 read 타임아웃
#   pristine huggingface 로는 학습 체크포인트 로딩이 DecodingError 로 깨지므로 포크 사용.
LEROBOT_REPO="https://github.com/PhysVoice/lerobot.git"
LEROBOT_COMMIT="19cb4ff5636b1c4f782e9315f565050c1cee3d5a"
PY="${PYTHON:-python3}"

echo "=== [1/4] 가상환경 생성 (.venv) ==="
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
echo "  Python: $(python --version)"
# 참고: 선택 의존성 openWakeWord(KWS) 는 Python 3.13 미지원.
#       KWS 가 꼭 필요하면:  PYTHON=python3.11 bash setup.sh

echo "=== [2/4] 음성/bridge 의존성 설치 ==="
pip install -r requirements.txt

echo "=== [3/4] lerobot 설치 (PhysVoice 포크 핀: ${LEROBOT_COMMIT:0:8}, smolvla) ==="
pip install "lerobot[smolvla] @ git+${LEROBOT_REPO}@${LEROBOT_COMMIT}"

echo "=== [4/4] torchaudio 설치 (Silero VAD 의존성, torch 버전·CUDA 매칭) ==="
# Silero VAD(음성 VAD)가 torchaudio 를 import 하는데, lerobot[smolvla] 는
# torch/torchvision/torchcodec 만 끌어오고 torchaudio 는 안 가져온다.
# requirements.txt 에 두면 torch 보다 먼저 설치돼 CUDA 빌드가 어긋나므로
# lerobot 설치 후, 방금 깔린 torch 와 "정확히 같은 버전+CUDA 빌드" 로 설치한다.
TORCH_FULL="$(python -c 'import torch; print(torch.__version__)')"   # 예: 2.7.1+cu126
TORCH_VER="${TORCH_FULL%%+*}"                                        # 2.7.1
TORCH_TAG="${TORCH_FULL#*+}"                                         # cu126 (로컬 태그 없으면 == TORCH_FULL)
if [ "$TORCH_TAG" = "$TORCH_FULL" ]; then
  pip install "torchaudio==${TORCH_VER}"                             # CPU/기본 빌드
else
  pip install "torchaudio==${TORCH_VER}" --index-url "https://download.pytorch.org/whl/${TORCH_TAG}"
fi

echo
echo "=== 설치 완료 ==="
echo "  - 가상환경:   source .venv/bin/activate"
echo "  - 실행:       bash run.sh"
echo "  - 선택기능:   pip install -r requirements-optional.txt  (KWS/노이즈제거, 3.13 주의)"
echo
echo "  ※ 시스템 패키지가 없으면 먼저 설치:"
echo "      sudo apt install ffmpeg portaudio19-dev libsndfile1"
echo "  ※ GPU(CUDA) 환경이면 torch가 자동으로 맞춰지지만,"
echo "      특정 CUDA 버전이 필요하면 그때 torch를 수동 재설치하세요."
