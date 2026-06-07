# 아키텍처

## 개요
음성 명령으로 SO101 로봇팔을 제어하는 자기완결형 파이프라인.
`git clone` → `bash setup.sh` → `bash run.sh` 로 끝나도록 설계.

```
🎤 "피식아, 빨간색 박스 집어서 넣어"
        │ 마이크
        ▼
┌──────────── voice/ (음성 두뇌) ────────────┐
│ VAD → STT① 웨이크워드 → STT② 명령           │
│ → 퍼지매칭 → Task ID (TASK_PICK_PUT_RED_BOX)│
└───────────────────┬────────────────────────┘
                    │ Task ID
                    ▼
┌──────────── bridge/ (다리) ────────────────┐
│ router  : task_map.yaml 조회                │
│           → (정책, 영어 task)               │
│           없으면 "미지원" → 대기복귀         │
│ dispatcher: robot_profile.yaml + 라우팅 →   │
│           lerobot-record subprocess 1회 실행 │
└───────────────────┬────────────────────────┘
                    │ (policy, task) + 로봇인자
                    ▼
┌──────── lerobot (설치형, 외부 엔진) ────────┐
│ 정책 로드(HF 자동 다운로드) → 관측 → 추론   │
│ → 모터 액션                                  │
└───────────────────┬────────────────────────┘
                    ▼
              🦾 SO101 (빨강→왼쪽 / 파랑→오른쪽)
                    │ 종료코드
                    ▼
              성공/실패 피드백 → 대기 복귀
```

## 확정된 설계 결정
| 항목 | 선택 | 비고 |
|------|------|------|
| 추론 구동 | 명령마다 `lerobot-record` 재실행 | 느슨한 결합, 크래시 격리 |
| 정책 구조 | 색별 별도 모델 (Phase 2) | 정책 선택 = 색 라우팅 |
| 레포 형태 | 단일 모노레포 (자기완결형) | clone 하나로 작업 가능 |
| lerobot | pip 핀 설치 (커밋 60efd875) + 전용 venv | 레포 가볍게, venv 로 격리 |
| 음성 두뇌 | PhysVoice/Voice 재사용 | voice/ 로 가져옴 |

## 폴더
```
PhysVoice-Pipeline/
├── voice/         음성 인식 (Voice 에서 가져옴)
├── bridge/        다리 (router·dispatcher·feedback)
├── config/        task_map.yaml, robot_profile.yaml
├── calibration/   SO101 캘리 (이 로봇 전용)
├── setup.sh       venv + 의존성 + lerobot 설치
├── run.sh         통합 실행
└── requirements.txt
```

## lerobot 격리 (왜 venv?)
`lerobot` 은 패키지명이 하나라 한 환경에 한 버전만 가능.
PC 에 이미 다른 lerobot 이 있어도 **전용 .venv** 안에 핀 버전을 설치하므로
서로 간섭하지 않는다. 그래서 PC 마다 `bash setup.sh` 한 번이면 동일하게 동작.

## 명령 커버리지 (현재 모델 기준)
| 음성 명령 | 상태 |
|-----------|------|
| 빨강/파랑 "집어서 넣어" | ✅ 정책 있음 |
| 초록 / 집어만 / 넣어만 | ❌ 모델 없음 → "미지원" |
