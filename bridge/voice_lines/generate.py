"""voice_lines/generate.py — TTS 멘트 wav 재생성 (gTTS).

bridge/speech.py 의 PHRASES 를 읽어 각 멘트를 한국어 TTS 로 합성하고
이 폴더에 <key>.wav (24kHz mono) 로 저장한다. 렌더된 wav 는 레포에 커밋돼
런타임엔 gTTS/네트워크 없이 재생되므로, 문구를 바꿀 때만 이 스크립트를 돌리면 된다.

사용:
    pip install gtts            # 일회성 (런타임엔 불필요)
    python bridge/voice_lines/generate.py
    # (gtts 가 click<8.2 를 끌어와 typer 와 충돌하면, 생성 후 pip install "click>=8.2.1")
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from speech import PHRASES  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    try:
        from gtts import gTTS
    except ImportError:
        sys.exit("gTTS 미설치:  pip install gtts")

    for key, text in PHRASES.items():
        mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        wav = os.path.join(OUT_DIR, f"{key}.wav")
        try:
            gTTS(text, lang="ko").save(mp3)
            subprocess.run(
                ["ffmpeg", "-y", "-i", mp3, "-ar", "24000", "-ac", "1", wav],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print(f"[렌더] {key:24s} ← '{text}'")
        finally:
            os.unlink(mp3)

    print(f"\n총 {len(PHRASES)}개 → {OUT_DIR}/")


if __name__ == "__main__":
    main()
