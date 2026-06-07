# PhysVoice-Pipeline

음성 명령으로 **SO101 로봇팔**을 제어하는 자기완결형 파이프라인.
음성 인식 → Task 라우팅 → lerobot 추론을 한 레포에서 처리한다.

> **"피식아, 빨간색 박스 집어서 넣어"** → 빨강 큐브를 집어 왼쪽 박스에 넣음

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

## 상태
🚧 **골격 단계** — 폴더 구조 + setup.sh 완료. voice/bridge 구현은 다음 단계.

| 구성 | 상태 |
|------|------|
| 폴더 구조 / setup.sh / config | ✅ |
| voice (Voice 에서 이식) | ⬜ |
| bridge (router·dispatcher) | ⬜ |
| calibration 복사 | ⬜ |
| run.sh 엔트리포인트 연결 | ⬜ |
