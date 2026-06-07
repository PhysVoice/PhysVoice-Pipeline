# voice/ — 음성 인식

PhysVoice/Voice 에서 이식한 음성 파이프라인. 출력은 Task ID 문자열.

## 구조
```
voice/
├── realtime/
│   ├── rt_pipeline.py      메인 파이프라인 (VAD → STT → 파싱 → Task ID)
│   ├── audio_stream.py     오디오 입력 (마이크/파일/네트워크)
│   ├── mic_client.py       노트북 마이크 → 서버 TCP 클라이언트
│   ├── record_samples.py   KWS 학습 샘플 녹음
│   └── start.sh            파이프라인 + bore 터널 실행
├── Whisper/
│   ├── command_parser.py   Task ID 매핑 (퍼지매칭)  ← bridge 가 쓰는 핵심
│   ├── stt.py / vad.py     faster-whisper STT, Silero VAD
│   ├── audio_loader.py / config.py
├── KWS/                    openWakeWord 웨이크워드 (kws.py + 학습 스크립트)
├── DeepFilterNet/denoise.py  노이즈 제거
└── evaluation/            STT/명령 인식률 평가
```

## 출력 → bridge
`command_parser.parse_command()` 가 `{"task_id": "TASK_PICK_PUT_RED_BOX", "status": "SUCCESS", ...}` 반환.
bridge 가 이 `task_id` 를 받아 `config/task_map.yaml` 로 라우팅한다.

## 이식 시 제외한 것
- `KWS/recordings/` — 웨이크워드 학습용 WAV (재학습 시에만 필요, 원본 Voice 레포에 있음)
- KWS ONNX 모델(`oww_model/피식아.onnx`) — git 미포함, 별도 전달 필요

## 의존성
루트 `requirements.txt` 에 통합됨 (faster-whisper, openwakeword, deepfilternet, sounddevice 등).
설정값은 `Whisper/config.py` 참고 (`MODEL_SIZE`, `DEVICE`, `VAD_THRESHOLD` 등).
