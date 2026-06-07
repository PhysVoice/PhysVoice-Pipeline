"""
dispatcher — 라우팅 결과 → lerobot-record 실행

config/robot_profile.yaml 로 로봇/카메라 인자를 구성하고,
명령마다 lerobot-record subprocess 를 1회 실행한다 (느슨한 결합).

검증된 주의사항 반영:
- 카메라 dict 에 type: opencv 주입 (lerobot 필수, profile 에 없으면 보강)
- calibration_dir 상대경로 → 절대경로, subprocess cwd=레포루트
- inference.device 가 빈 값이면 --policy.device 플래그 생략 (auto-detect)
- dataset 누적 방지: 매 실행 전 dataset.root 삭제, push_to_hub=false
- 하드웨어 값은 환경변수(ROBOT_PORT/WRIST_CAM/TOP_CAM/INFERENCE_DEVICE)로 덮어쓰기
"""

import os
import shlex
import shutil
import signal
import subprocess

import yaml

# bridge/dispatcher.py → 레포 루트
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 카메라 dict 필드 출력 순서 (type 먼저)
_CAM_FIELDS = ("index_or_path", "width", "height", "fps", "fourcc")
_CAM_ENV = {"wrist": "WRIST_CAM", "top": "TOP_CAM"}


class Dispatcher:
    def __init__(self, profile_path: str, dry_run: bool = False):
        with open(profile_path, encoding="utf-8") as f:
            self.profile = yaml.safe_load(f) or {}
        self.dry_run = dry_run
        # 추론 결과 데이터셋(불필요)은 임시 위치에 쓰고 매번 삭제 → 누적/HF 오염 방지
        self.dataset_root = os.environ.get("PHYSVOICE_DATASET_ROOT",
                                           os.path.join(REPO_ROOT, ".cache", "eval_tmp"))
        self.dataset_repo_id = os.environ.get("PHYSVOICE_DATASET_REPO", "physvoice/eval_tmp")

    # ── 캘리브레이션 절대경로 ──
    def _calib_dir(self) -> str:
        d = (self.profile.get("robot", {}) or {}).get("calibration_dir", "")
        if not d:
            return ""
        if not os.path.isabs(d):
            d = os.path.join(REPO_ROOT, d)
        return os.path.abspath(d)

    # ── --robot.cameras 문자열 구성 ──
    def _cameras_arg(self) -> str:
        cams = self.profile.get("cameras", {}) or {}
        parts = []
        for name, raw in cams.items():
            cam = dict(raw)
            env = _CAM_ENV.get(name)
            if env and os.environ.get(env):
                cam["index_or_path"] = os.environ[env]
            cam.setdefault("type", "opencv")  # lerobot 필수
            fields = [f"type: {cam['type']}"]
            for k in _CAM_FIELDS:
                if k in cam:
                    fields.append(f"{k}: {cam[k]}")
            parts.append(f"{name}: {{{', '.join(fields)}}}")
        return "{ " + ", ".join(parts) + " }"

    # ── lerobot-record 명령 구성 ──
    def build_command(self, policy: str, task: str) -> list[str]:
        robot = self.profile.get("robot", {}) or {}
        inf = self.profile.get("inference", {}) or {}

        port = os.environ.get("ROBOT_PORT", robot.get("port", ""))
        device = os.environ.get("INFERENCE_DEVICE", inf.get("device", "") or "")

        cmd = [
            "lerobot-record",
            f"--robot.type={robot.get('type', 'so101_follower')}",
            f"--robot.port={port}",
            f"--robot.id={robot.get('id', 'my_follower')}",
        ]
        calib = self._calib_dir()
        if calib:
            cmd.append(f"--robot.calibration_dir={calib}")
        cmd.append(f"--robot.cameras={self._cameras_arg()}")

        cmd.append(f"--policy.path={policy}")
        if device.strip():  # 빈 값이면 생략 → lerobot auto-detect
            cmd.append(f"--policy.device={device.strip()}")

        cmd += [
            f"--dataset.repo_id={self.dataset_repo_id}",
            f"--dataset.root={self.dataset_root}",
            f"--dataset.single_task={task}",
            "--dataset.num_episodes=1",
            f"--dataset.fps={inf.get('fps', 30)}",
            f"--dataset.episode_time_s={inf.get('episode_time_s', 60)}",
            "--dataset.reset_time_s=5",
            "--dataset.push_to_hub=false",
            "--display_data=false",
        ]
        return cmd

    # ── 실행 ──
    def run(self, policy: str, task: str) -> int:
        cmd = self.build_command(policy, task)
        printable = " ".join(shlex.quote(c) for c in cmd)

        if self.dry_run:
            print(f"[dispatcher][dry-run] cwd={REPO_ROOT}")
            print(f"[dispatcher][dry-run] {printable}")
            return 0

        calib = self._calib_dir()
        if calib and not os.path.isdir(calib):
            print(f"[dispatcher][경고] 캘리브레이션 폴더 없음: {calib}")

        # 데이터셋 누적 방지: 실행 전 임시 캐시 삭제
        shutil.rmtree(self.dataset_root, ignore_errors=True)

        # 정책 로딩 + 에피소드 실행 시간 + 여유(모델 다운로드/로드)
        inf = self.profile.get("inference", {}) or {}
        timeout = float(inf.get("episode_time_s", 60)) + 120.0

        print(f"[dispatcher] 실행 (cwd={REPO_ROOT}, timeout={timeout:.0f}s):\n  {printable}")
        try:
            # 자식을 별도 프로세스 그룹으로 → 타임아웃/Ctrl+C 시 그룹 통째 종료 가능
            proc = subprocess.Popen(cmd, cwd=REPO_ROOT, start_new_session=True)
        except FileNotFoundError:
            print("[dispatcher][오류] 'lerobot-record' 미발견 — setup.sh 로 lerobot 설치 여부 확인.")
            return 127

        try:
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"[dispatcher][경고] {timeout:.0f}s 초과 — 로봇 프로세스 강제 종료")
            self._terminate(proc)
            return 124
        except KeyboardInterrupt:
            print("[dispatcher] 중단 요청 — 로봇 프로세스 종료")
            self._terminate(proc)
            raise   # 파이프라인 상위로 전파해 전체 정리/종료

    @staticmethod
    def _terminate(proc: subprocess.Popen):
        """자식 프로세스 그룹을 SIGINT→(대기)→SIGKILL 순으로 정리 (좀비 방지)."""
        try:
            pgid = os.getpgid(proc.pid)
        except ProcessLookupError:
            return
        try:
            os.killpg(pgid, signal.SIGINT)
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError, PermissionError):
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
