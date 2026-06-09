"""speech — 시연용 TTS 음성 피드백 (선택적, 실패해도 파이프라인 안 깨짐).

미리 렌더된 wav(voice_lines/*.wav)를 시스템 default 출력으로 재생한다.
런타임 의존성은 sounddevice + scipy(이미 설치됨)뿐 — 네트워크/gTTS 불필요.
wav 가 없거나 재생 실패하면 조용히 패스한다(핵심 흐름 영향 없음).

끄기:  환경변수 PHYSVOICE_TTS=0  (또는 run.sh --no-tts)
문구 수정/재생성:  voice_lines/generate.py 참고 (gTTS 필요)
"""
import os
import threading

_LINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_lines")

# key → 한국어 문구. generate.py 가 이 사전을 그대로 읽어 wav 를 만든다.
# (key 가 Task ID 면 해당 명령 인식 시 그 멘트를 말한다)
PHRASES = {
    "ready":                  "안녕하세요, 피식이예요. 시키실 게 있으면 피식아라고 불러주세요.",
    "wake":                   "네! 피식이 여기 있어요.",
    "TASK_PICK_PUT_RED_BOX":  "빨간색 박스, 넣어 드릴게요!",
    "TASK_PICK_PUT_BLUE_BOX": "파란색 박스, 넣어 드릴게요!",
    "TASK_STACK":             "차곡차곡 쌓아 드릴게요!",
    "done":                   "다 했어요!",
    "unsupported":            "음, 그건 아직 못 해요.",
    "fail":                   "잘 못 들었어요. 다시 말씀해 주세요.",
}


def _enabled() -> bool:
    return os.environ.get("PHYSVOICE_TTS", "1") != "0"


def _wav_path(key: str) -> str:
    return os.path.join(_LINES_DIR, f"{key}.wav")


def _play_file(path: str) -> None:
    try:
        import numpy as np
        import sounddevice as sd
        from scipy.io import wavfile

        sr, data = wavfile.read(path)
        if np.issubdtype(data.dtype, np.integer):
            data = data.astype(np.float32) / np.iinfo(data.dtype).max
        else:
            data = data.astype(np.float32)
        sd.play(data, sr)
        sd.wait()
    except Exception:
        pass  # TTS 는 부가기능 — 어떤 이유로든 실패해도 무시


def speak(key: str, block: bool = True) -> None:
    """key 에 해당하는 미리 렌더된 멘트를 재생. wav 없거나 비활성/실패면 조용히 패스.

    block=True 면 재생이 끝날 때까지 대기(말한 뒤 다음 동작 — 자연스러운 순서).
    """
    if not _enabled():
        return
    path = _wav_path(key)
    if not os.path.isfile(path):
        return
    if block:
        _play_file(path)
    else:
        threading.Thread(target=_play_file, args=(path,), daemon=True).start()
