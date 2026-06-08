"""feedback — 사용자 피드백 (서버 + 노트북 동시 출력 + 시연용 TTS).

notify 는 RealtimePipeline._notify (print + stream.send) 가 주입된다.
TTS(speech.speak)는 부가기능 — wav 없거나 PHYSVOICE_TTS=0 이면 조용히 패스한다.
"""

from bridge import speech


def supported(notify, res):
    if res.policy:
        src = f"정책 {res.policy}"
    elif res.replay:
        src = f"리플레이 {res.replay.get('repo_id')} ep{res.replay.get('episode', 0)}"
    else:
        src = "?"
    notify(f"[ 실행 ] {res.task_id} → {src}")
    speech.speak(res.task_id, block=True)   # 예: "빨간색 박스, 넣어 드릴게요!" (없으면 패스)
    notify("[ 실행 ] 로봇 동작 중... (완료까지 대기)")


def unsupported(notify, res):
    notify(f"[미지원] {res.reason}")
    speech.speak("unsupported", block=True)


def done(notify, res, code: int):
    if code == 0:
        notify(f"[ 완료 ] {res.task_id} 동작 완료")
        speech.speak("done", block=False)
    else:
        notify(f"[ 실패 ] 로봇 실행 오류 (exit {code})")
