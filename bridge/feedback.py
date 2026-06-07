"""
feedback — 사용자 피드백 (서버 + 노트북 동시 출력)

notify 는 RealtimePipeline._notify (print + stream.send) 가 주입된다.
"""


def supported(notify, res):
    notify(f"[ 실행 ] {res.task_id} → 정책 {res.policy}")
    notify("[ 실행 ] 로봇 동작 중... (완료까지 대기)")


def unsupported(notify, res):
    notify(f"[미지원] {res.reason}")


def done(notify, res, code: int):
    if code == 0:
        notify(f"[ 완료 ] {res.task_id} 동작 완료")
    else:
        notify(f"[ 실패 ] 로봇 실행 오류 (exit {code})")
