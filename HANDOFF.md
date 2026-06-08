# 🤝 HANDOFF — 로봇 PC 작업 에이전트용 브리핑

이 문서는 **SO101 로봇이 연결된 PC에서 직접 작업하는 에이전트**에게 넘기는 인수인계서다.
여기까지는 다른 PC(로봇 없음)에서 구현·검증됐고, **실제 하드웨어 brought-up 만 남았다.**
너의 임무: `setup.sh` → `run.sh` 가 이 PC에서 실제로 음성→로봇 동작까지 되게 만드는 것.

---

## 0. 환경 (확인된 사실)

- 호스트: `int@rtx3090`, GPU: RTX 3090
- 경로: `/home/int/amber/PhysVoice-Pipeline`
- **Python 기본이 3.13** (이게 설치 함정의 핵심 — 아래 참고)
- 시스템 패키지 설치됨: `ffmpeg`, `portaudio19-dev`, `libsndfile1`
- 원격 레포 2개 (둘 다 PhysVoice org, 푸시 권한 있음):
  - `PhysVoice/PhysVoice-Pipeline` ← 이 레포
  - `PhysVoice/lerobot` ← 추론 패치 포함 포크 (setup.sh 가 핀 설치)

---

## 1. 이게 뭐냐 (30초 요약)

음성 명령으로 SO101 로봇팔을 제어하는 **자기완결형 파이프라인**.

```
🎤 "피식아, 빨간색 박스 집어서 넣어"
  → voice/  (Silero VAD + faster-whisper STT + Levenshtein 퍼지매칭) → Task ID
  → bridge/ (Task ID → config/task_map.yaml 라우팅 → lerobot-record 명령 구성)
  → lerobot (PhysVoice 포크, 설치형) → SmolVLA 정책 추론 → SO101 동작
  → 결과 피드백 → 다음 명령 대기
```

설계 결정(확정, 바꾸지 말 것): **명령마다 `lerobot-record` 1회 실행**(느슨한 결합) ·
**색별 별도 정책**(red/blue 모델 선택 = 색 라우팅) · **모노레포** ·
lerobot 은 **pip 핀 설치**(전용 venv 격리).

지원 명령: `빨간색/파란색 박스 집어서 넣어` 2개만 (초록·집어만·넣어만은 모델 없음 → "미지원").

---

## 2. 현재 상태

| 구성 | 상태 |
|------|------|
| 레포 구조 / setup.sh / config | ✅ |
| voice 이식 (PhysVoice/Voice 에서) | ✅ |
| bridge (router·dispatcher·feedback·main) | ✅ 적대적 리뷰까지 |
| lerobot 포크 핀 (`PhysVoice/lerobot@19cb4ff`) | ✅ |
| calibration (SO101 follower/leader) | ✅ |
| **이 PC에서 setup.sh + run.sh 실제 동작** | ❌ ← **너의 일** |

코드 측면은 완성. **단, 실제 하드웨어/이 PC 파이썬 환경에서 한 번도 안 돌아갔다.**

---

## 3. 바로 할 일 — 단계별 bring-up (오류는 캡처해서 진단)

### Step 1. 최신화 + 클린 재설치
```bash
cd /home/int/amber/PhysVoice-Pipeline
git pull
rm -rf .venv          # 이전 실패 venv 정리
bash setup.sh 2>&1 | tee /tmp/setup.log
```
- 성공 기준: 마지막에 `=== 설치 완료 ===` + `.venv/` 생성.
- 실패하면 `/tmp/setup.log` 의 **첫 ERROR** 를 찾아 §5 표와 대조.

### Step 2. venv 활성화 + 경량 점검 (torch/로봇 불필요)
```bash
source .venv/bin/activate
python -m bridge.main --print-commands
```
- task_map 2개의 `lerobot-record` 명령이 출력돼야 함.
- 출력의 `--robot.port`, `--robot.cameras` 의 `/dev/video*`, `--robot.calibration_dir` 를 **눈으로 확인** — 이 PC 실제 값과 다르면 §4 로 수정.

### Step 3. 하드웨어 값 확인·정정 (§4)

### Step 4. 드라이런 (로봇 안 움직임)
```bash
bash run.sh --dry-run
```
- 마이크에 "피식아" → "빨간색 박스 집어서 넣어" → 올바른 Task ID 잡히고 dispatcher 가 명령만 출력하면 OK.
- 마이크 없으면 파일 테스트: `bash run.sh --file <wav> --skip-kws --dry-run`

### Step 5. 실제 실행
```bash
bash run.sh                       # 로컬 마이크
# 또는 노트북 마이크: bash run.sh --network --port 9876
```

---

## 4. 하드웨어 값 맞추기 (거의 항상 필요)

기본값은 개발 PC 기준이라 이 PC와 다를 가능성 높다.

```bash
# 카메라 노드
v4l2-ctl --list-devices    # 없으면: ls -l /dev/video*
# 로봇 시리얼 포트
ls /dev/serial/by-id/      # 없으면: ls /dev/ttyACM* /dev/ttyUSB*
# 마이크 장치
.venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"
```

수정 위치 — 둘 중 하나:
- **영구**: `config/robot_profile.yaml` 의 `robot.port`, `cameras.wrist/top.index_or_path`,
  `inference.device`(cuda/cpu/""), `inference.episode_time_s`(단일 동작 시간, 기본 60).
- **일시(env, config 안 건드림)**:
  ```bash
  export ROBOT_PORT=/dev/ttyACM0 WRIST_CAM=/dev/video0 TOP_CAM=/dev/video2 INFERENCE_DEVICE=cuda
  ```

⚠️ `calibration/robots/so101_follower/my_follower.json` 은 **특정 로봇 개체 전용**.
이 PC의 로봇이 다른 개체면 값이 안 맞아 위험 → lerobot 으로 재캘리 후 교체.

---

## 5. 알려진 이슈 & 해결 (Python 3.13 가 핵심)

| 증상 / 에러 | 원인 | 해결 |
|---|---|---|
| `setup.sh` 가 `tflite-runtime`/`openwakeword` 에서 ERROR | openWakeWord 가 Python 3.13 미지원 | **이미 수정됨**(git pull). KWS 는 선택(`requirements-optional.txt`)으로 분리, 기본은 Whisper 웨이크워드 |
| `run.sh` → `ModuleNotFoundError: yaml`(또는 torch/faster_whisper) | setup.sh 가 실패해 venv 비어있음 | setup.sh 의 첫 ERROR 를 먼저 해결. venv 활성화(`source .venv/bin/activate`) 확인 |
| `lerobot-record: command not found` | venv 미활성화 또는 lerobot 미설치 | `source .venv/bin/activate`; `pip show lerobot` 확인; 없으면 setup.sh 3단계 로그 확인 |
| lerobot/torch 설치 실패 | torch 3.13 휠 또는 numpy 충돌 | 로그의 정확한 패키지 확인. torch 따로 설치 시도: `pip install torch torchaudio` (CUDA 자동). numpy 충돌이면 `pip install "numpy<2.3"` 후 재시도 |
| 정책 로딩 `DecodingError`/`use_peft` 류 | pristine huggingface lerobot 이 설치됨 | lerobot 이 **PhysVoice 포크**(`19cb4ff`)인지: `pip show lerobot` 의 location/소스 확인. 아니면 `pip install "lerobot[smolvla] @ git+https://github.com/PhysVoice/lerobot.git@19cb4ff5636b1c4f782e9315f565050c1cee3d5a"` |
| `RuntimeError: 마이크 입력 장치를 찾을 수 없습니다` | 이 PC에 입력 장치 없음/권한 | 마이크 연결 확인, 또는 노트북 마이크: `bash run.sh --network` + 노트북에서 `voice/realtime/mic_client.py` |
| Silero VAD 로딩 멈춤/에러 | `torch.hub` 가 `snakers4/silero-vad` 다운로드(최초 1회 인터넷) | 인터넷 확인. 캐시 후엔 오프라인 OK |
| 카메라 안 열림/멈춤 | `index_or_path` 불일치, USB 대역폭 | §4 로 노드 재확인. 두 캠 MJPG 필수(`fourcc: MJPG`) |
| 로봇이 `episode_time_s` 내내 안 멈춤 | 정상 — 키 입력 없으면 그 시간만큼 실행 | `config/robot_profile.yaml` 에서 시간 조정 |
| Whisper 느림 | 모델 큼 | `voice/Whisper/config.py` 의 `MODEL_SIZE = "small"` |

선택 기능 설치(필요 시):
```bash
pip install -r requirements-optional.txt   # KWS+노이즈제거. 3.13에선 openwakeword 실패 가능
# 노이즈제거(deepfilternet) 실패해도 파이프라인은 자동으로 원본 오디오 사용
# KWS 가 꼭 필요하면 venv 를 3.11 로: rm -rf .venv && PYTHON=python3.11 bash setup.sh
```

---

## 6. 파일 지도 + 디자인 불변식

```
PhysVoice-Pipeline/
├── setup.sh              venv + 의존성 + lerobot 포크(19cb4ff) 설치
├── run.sh                exec python -m bridge.main "$@"
├── requirements.txt      핵심(3.13 OK): faster-whisper, ctranslate2, sounddevice, scipy, numpy, PyYAML
├── requirements-optional.txt  KWS(openwakeword/onnxruntime) + denoise(deepfilternet)
├── config/
│   ├── task_map.yaml         Task ID → (정책 HF id, 영어 task 문자열)  ← 명령 추가는 여기만
│   └── robot_profile.yaml    로봇 포트/카메라/캘리/episode_time_s/device
├── calibration/robots/so101_follower/my_follower.json   추론 필수(이 로봇 전용)
├── voice/                음성 (PhysVoice/Voice 이식)
│   ├── realtime/rt_pipeline.py   RealtimePipeline. result_callback 훅으로 bridge 연결.
│   │                             denoise 는 지연 import. _drain_all 은 큐 snapshot 만 비움.
│   ├── realtime/audio_stream.py  AudioStream(maxsize=512, put_nowait 드롭)/File/Network
│   └── Whisper/{stt,vad,command_parser,config}.py
└── bridge/
    ├── router.py        Task ID → Resolution(supported/policy/task)  미지원/UNKNOWN 거름
    ├── dispatcher.py    robot_profile → lerobot-record subprocess(timeout+프로세스그룹 Ctrl+C)
    ├── feedback.py      notify 로 서버+노트북 동시 피드백
    └── main.py          엔트리포인트 + on_command 콜백, --print-commands(경량) / --dry-run
```

**건드리지 말 것(불변식):**
- lerobot 은 `PhysVoice/lerobot@19cb4ff` (pristine huggingface 면 정책 로딩 깨짐). setup.sh 의 `LEROBOT_COMMIT` 유지.
- dispatcher 의 `--robot.cameras` 에는 `type: opencv` 가 들어가야 함(없으면 lerobot 파싱 실패). 이미 주입됨.
- `--dataset.push_to_hub=false` 유지(HF 오염 방지). dataset 은 매 실행 `.cache/eval_tmp` 삭제 후 재생성.
- calibration_dir 는 dispatcher 가 절대경로로 변환 + subprocess `cwd=레포루트`.
- voice 수정은 backward-compatible 하게(standalone 실행 안 깨지게).

**고치면 커밋·푸시까지:**
```bash
git add -A && git commit -m "..." && git push origin main
# 커밋 메시지 끝에:  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```
lerobot 포크를 고쳐야 하면 `/home/.../lerobot` 클론에서 `physvoice-pin` 브랜치에 커밋 후
`git push physvoice physvoice-pin`, 새 SHA 로 setup.sh `LEROBOT_COMMIT` 갱신.

---

## 7. 더 깊은 맥락
- 전체 설계도/결정 근거: [docs/architecture.md](docs/architecture.md)
- 단계별 체크리스트(사람용): README 의 "운영 참고"

## 8. 완료 보고에 포함할 것
- `setup.sh` 성공 로그(또는 막힌 첫 ERROR)
- `python -m bridge.main --print-commands` 출력
- 이 PC에 맞게 바꾼 `robot_profile.yaml` diff (port/camera/device)
- 실제 음성→로봇 1회 동작 결과(성공/실패 + lerobot 로그)
