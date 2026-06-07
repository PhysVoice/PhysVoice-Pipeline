# voice/ — 음성 인식

PhysVoice/Voice 의 음성 파이프라인이 들어갈 자리.

**구현 단계에 가져올 것** (Voice 레포에서):
- `rt_pipeline.py` — 실시간 파이프라인 (VAD → STT → 명령 파싱)
- `stt.py` / `vad.py` / `command_parser.py` — STT, Silero VAD, Task ID 매핑
- `audio_stream.py` / `mic_client.py` — 오디오 입력
- `kws.py` (KWS) / `denoise.py` (DeepFilterNet)
- `config.py` — 설정값

**출력**: Task ID 문자열 (예: `TASK_PICK_PUT_RED_BOX`) → bridge 로 전달.
