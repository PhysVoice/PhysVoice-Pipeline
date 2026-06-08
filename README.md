# PhysVoice-Pipeline

음성 명령으로 **SO101 로봇팔**을 제어하는 자기완결형 파이프라인.
음성 인식 → Task 라우팅 → lerobot 추론을 한 레포에서 처리한다.

> **"피식아, 빨간색 박스 집어서 넣어"** → 빨강 큐브를 집어 왼쪽 박스에 넣음

### 음성 명령 (유연 매핑)
이 로봇은 **색별 pick&place** 만 한다 → 발화에 **색**만 잡히면 그 색 동작으로 보낸다.
- "빨간색", "빨강 거 넣어줘", "빨간색 박스 집어서 넣어" → **빨강** pick&place
- "파란색", "파랑", "파란 큐브 넣어" → **파랑** pick&place
- 초록/그 외 → "미지원" (모델 없음)

웨이크워드 **"피식아"** 는 STT 오인식(피시카·피식하 등)도 폭넓게 인식한다.
로봇이 **TTS 로 응답**한다(시연용): 호명 시 "네! 피식이 여기 있어요", 동작 전 "빨간색 박스, 넣어 드릴게요!", 완료 시 "다 했어요!". 끄려면 `run.sh --no-tts` (또는 `PHYSVOICE_TTS=0`).

## 빠른 시작
```bash
git clone https://github.com/PhysVoice/PhysVoice-Pipeline.git
cd PhysVoice-Pipeline

# 시스템 패키지 (최초 1회)
sudo apt install ffmpeg portaudio19-dev libsndfile1

bash setup.sh     # 전용 venv 생성 + 의존성 + lerobot(핀) 설치
bash run.sh       # 통합 실행 (구현 단계 후)
```

PC 에 이미 다른 lerobot 이 있어도 **전용 `.venv`** 로 격리되어 충돌하지 않는다.

## 구조
```
PhysVoice-Pipeline/
├── voice/         음성 인식 (VAD·STT·퍼지매칭) → Task ID
├── bridge/        다리 (Task ID → 정책·task → lerobot 호출)
├── config/
│   ├── task_map.yaml       Task ID → (정책, 영어 task)
│   └── robot_profile.yaml  로봇 포트·카메라·캘리 경로
├── calibration/   SO101 캘리 (이 로봇 전용)
├── setup.sh       환경 설치
├── run.sh         통합 실행
└── requirements.txt
   + lerobot (setup.sh 가 핀 커밋으로 설치, 외부 엔진)
```

자세한 설계는 [docs/architecture.md](docs/architecture.md).
**로봇 PC에서 처음 띄우는 작업자/에이전트는 → [HANDOFF.md](HANDOFF.md) 부터.**

## 상태
🤖 **로봇 PC bring-up 단계** — rtx3090(SO101 연결)에서 환경/하드웨어 검증 완료.

| 구성 | 상태 |
|------|------|
| 폴더 구조 / setup.sh / config | ✅ |
| voice (Voice 에서 이식) | ✅ |
| bridge (router·dispatcher·feedback·main) | ✅ |
| run.sh 엔트리포인트 연결 | ✅ |
| lerobot 설치 (PhysVoice 포크 핀, smolvla+feetech) | ✅ |
| calibration 복사 (SO101 follower/leader) | ✅ |
| 하드웨어 값 정정 (카메라 video0/2, 포트 검증) | ✅ |
| 로봇 단독 동작 (빨강 정책 → 팔 동작) | ✅ |
| 마이크·STT (라이브 음성 인식) | ✅ |
| 음성→로봇 라이브 통합 (full `run.sh`) | 🔄 확인 중 |
| 시연용 TTS 음성 피드백 + 유연한 명령 매핑 | ✅ |

### 테스트 (로봇/torch 없이)
```bash
python -m bridge.main --print-commands   # task_map → lerobot-record 명령 미리보기
```

### 운영 참고 (알려진 고려사항)
- **GPU 메모리**: voice(Whisper)가 상주한 채 lerobot(SmolVLA)이 별도 로드됨 → 넉넉한 VRAM 권장(분리 GPU 가능).
- **최초 1회 네트워크**: 정책(공개 HF 모델)을 처음 실행 시 다운로드/캐시함(로그인 불필요).
- **에피소드 시간**: `lerobot-record` 는 키 입력이 없으면 `episode_time_s` 동안 끝까지 동작 → `config/robot_profile.yaml` 에서 단일 동작에 맞게 조정.
- **하드웨어 덮어쓰기**: `ROBOT_PORT / WRIST_CAM / TOP_CAM / INFERENCE_DEVICE` 환경변수로 PC별 차이 흡수.
