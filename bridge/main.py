"""
main — 통합 엔트리포인트

voice 파이프라인을 실행하고, 명령 인식 시 router→dispatcher 로 lerobot 추론을 구동한다.

실행:
    python -m bridge.main                 # 로컬 마이크
    python -m bridge.main --network       # 노트북 마이크(TCP) 수신
    python -m bridge.main --dry-run       # lerobot 호출 대신 명령만 출력 (로봇 없이 테스트)
    python -m bridge.main --file a.wav --skip-kws   # 파일 입력 테스트
"""

import argparse
import os
import sys

from bridge.router import Router
from bridge.dispatcher import Dispatcher
from bridge import feedback
from bridge import speech

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _add_voice_to_path():
    """voice 모듈들이 flat import 구조라 경로를 등록한다 (rt_pipeline 과 동일 방식)."""
    for sub in ("voice/realtime", "voice/Whisper", "voice/KWS", "voice/DeepFilterNet"):
        p = os.path.join(REPO_ROOT, sub)
        if p not in sys.path:        # 중복 삽입 방지 (rt_pipeline 도 동일 경로 추가)
            sys.path.insert(0, p)


def main():
    ap = argparse.ArgumentParser(description="PhysVoice-Pipeline 통합 실행")
    ap.add_argument("--task-map", default=os.path.join(REPO_ROOT, "config", "task_map.yaml"))
    ap.add_argument("--robot-profile", default=os.path.join(REPO_ROOT, "config", "robot_profile.yaml"))
    ap.add_argument("--network", action="store_true", help="노트북 마이크를 TCP로 수신")
    ap.add_argument("--port", type=int, default=9876, help="--network 포트")
    ap.add_argument("--file", default=None, help="마이크 대신 오디오 파일")
    ap.add_argument("--skip-kws", action="store_true", help="웨이크워드 생략")
    ap.add_argument("--no-denoise", action="store_true", help="노이즈 제거 비활성화")
    ap.add_argument("--no-tts", action="store_true", help="시연용 음성 피드백(TTS) 비활성화")
    ap.add_argument("--replay", action="store_true",
                    help="정책 추론 대신 녹화 재생(lerobot-replay). task_map 의 replay 블록 사용 (시연용)")
    ap.add_argument("--dry-run", action="store_true", help="lerobot 호출 대신 명령만 출력")
    ap.add_argument("--print-commands", action="store_true",
                    help="task_map 의 모든 명령에 대한 lerobot 명령을 출력하고 종료 (voice/torch 불필요)")
    args = ap.parse_args()

    if args.no_tts:
        os.environ["PHYSVOICE_TTS"] = "0"
    replay_mode = args.replay or os.environ.get("PHYSVOICE_REPLAY") == "1"

    router = Router(args.task_map)
    dispatcher = Dispatcher(args.robot_profile, dry_run=args.dry_run)

    # 경량 점검 모드: voice(torch) import 없이 config→명령 변환만 확인
    if args.print_commands:
        for task_id in router.tasks:
            res = router.resolve(task_id)
            if replay_mode:
                if res.has_replay:
                    print(f"\n# {task_id}  →  [replay] {res.replay.get('repo_id')} ep{res.replay.get('episode', 0)}")
                    print("  " + " ".join(dispatcher.build_replay_command(res.replay)))
                else:
                    print(f"\n# {task_id}  →  [replay] 미지원 (replay 블록 없음)")
            elif res.has_policy:
                print(f"\n# {task_id}  →  {res.policy}")
                print("  " + " ".join(dispatcher.build_command(res.policy, res.task)))
            elif res.has_replay:
                # 정책은 없고 replay 만 있는 태스크(예: stacking) — 정책 모드에선 미지원
                print(f"\n# {task_id}  →  미지원 (정책 없음 — replay 전용, --replay 로 실행)")
            else:
                print(f"\n# {task_id}  →  미지원 ({res.reason})")
        return

    # 명령 인식 시 호출되는 콜백 (로봇 실행 동안 블로킹 → 음성 자연 일시정지)
    def on_command(result, notify):
        res = router.resolve(result["task_id"])
        # 현재 모드에서 실제로 돌릴 소스가 있는지: replay 모드=녹화, 정책 모드=정책
        runnable = res.has_replay if replay_mode else res.has_policy
        if not runnable:
            if res.supported:   # 태스크는 있으나 이 모드의 실행 소스가 없음(예: 정책 모드의 stacking)
                res.reason = (f"{result['task_id']}: "
                              f"{'replay 블록' if replay_mode else '정책'} 없음 — 이 모드에서 미지원")
            feedback.unsupported(notify, res)
            return
        feedback.supported(notify, res)
        code = dispatcher.run(replay=res.replay) if replay_mode else dispatcher.run(res.policy, res.task)
        feedback.done(notify, res, code)

    # voice 는 무거운 의존성(torch 등)을 끌어오므로 여기서 지연 import
    _add_voice_to_path()
    from rt_pipeline import RealtimePipeline
    from audio_stream import AudioStream, NetworkStream, FileStream

    # 이벤트(웨이크워드 인식·명령 미인식) → 시연용 TTS
    def on_event(name):
        speech.speak(name, block=True)

    pipeline = RealtimePipeline(use_denoise=not args.no_denoise,
                                result_callback=on_command, event_callback=on_event)

    # Whisper 모델을 미리 로드한다. 안 하면 첫 발화("피식아") 인식 도중 모델 로딩으로
    # 멈춘 듯 보이고(최초엔 ~1.5GB 다운로드), 네트워크 실패가 대화 중에 터진다.
    from stt import _get_model  # _add_voice_to_path() 로 voice/Whisper 가 sys.path 에 있음
    try:
        _get_model()
    except Exception as e:
        print(f"[오류] Whisper 모델 로드 실패: {e}", file=sys.stderr)
        print("  인터넷 연결을 확인하고 다시 실행하세요 (최초 1회 모델 다운로드 필요).", file=sys.stderr)
        sys.exit(1)
    print("[초기화] Whisper 모델 준비 완료\n")

    if args.network:
        stream = NetworkStream(port=args.port)
    elif args.file:
        print(f"[ 파일 ] {args.file}\n")
        stream = FileStream(args.file)
    else:
        stream = AudioStream()

    pipeline.run(stream, skip_kws=args.skip_kws)


if __name__ == "__main__":
    main()
