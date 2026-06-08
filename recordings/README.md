# recordings/ — 시연용 텔레옵 골든 에피소드 (리플레이 소스)

`bash run.sh --replay` 데모에서 음성 명령마다 재생되는 **녹화 데이터셋**들이 여기 있다.
정책 추론 대신 잘 된 텔레옵 1회를 그대로 재생한다 (성공률 낮은 동작·정책 없는 stacking 시연용).

> ⚠️ **데이터(영상/parquet)는 git 에 안 올라간다** (`.gitignore`: `recordings/*`, 이 README만 추적).
> 로컬 전용이라 다른 PC 에서 clone 하면 아래 "재생성" 으로 다시 녹화해야 리플레이가 된다.

## 데이터셋 ↔ 음성 명령 매핑

| 로컬 경로 | repo_id | episode | 음성 명령(예) | Task ID | 길이 |
|---|---|---|---|---|---|
| `recordings/golden_red`   | `physvoice/golden_red`   | 0 | "빨간색" / "빨간 거 넣어줘"  | `TASK_PICK_PUT_RED_BOX`  | 1599f ≈ 53s |
| `recordings/golden_blue`  | `physvoice/golden_blue`  | 0 | "파란색" / "파랑 넣어"      | `TASK_PICK_PUT_BLUE_BOX` | 925f ≈ 31s |
| `recordings/golden_stack` | `physvoice/golden_stack` | 0 | "큐브 쌓아줘" / "스택"      | `TASK_STACK`             | 1188f ≈ 40s |

- 모두 `so101_follower`, 30fps, 카메라 `observation.images.{wrist,top}` (480×640), action/state 6D.
- 이 매핑의 출처(정책·replay 블록): [`config/task_map.yaml`](../config/task_map.yaml).
- 배선: `bridge/dispatcher.py` 의 `build_replay_command` (→ `lerobot-replay`). **리플레이엔 `--robot.cameras` 를 넣지 않는다**(lerobot-replay 가 opencv 플러그인 미등록 → 파싱 에러, 또 카메라는 재생에 불필요).

## 데모 실행
```bash
bash run.sh --replay              # 피식아 → 명령 → 해당 골든 에피소드 재생 + TTS
bash run.sh --replay --skip-kws   # 웨이크워드 생략(바로 명령)
```

## 재생성 (텔레옵 재녹화)
리더 팔(`so101_leader`, 포트 `...5A68012267`)로 텔레옵. 동작 완료 후 **→(오른쪽 화살표)** 로 저장.
공통 인자는 팔로워(`...5AE6085270`) + 카메라(`/dev/video0` wrist, `/dev/video2` top) + 리더.

```bash
cd <repo>; source .venv/bin/activate
rm -rf recordings/golden_red      # (blue/stack 동일, 경로만 교체)
lerobot-record \
  --robot.type=so101_follower --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6085270-if00 \
  --robot.id=my_follower --robot.calibration_dir=$PWD/calibration/robots/so101_follower \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30, fourcc: MJPG}, top: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30, fourcc: MJPG} }" \
  --teleop.type=so101_leader --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A68012267-if00 \
  --teleop.id=my_leader --teleop.calibration_dir=$PWD/calibration/teleoperators/so101_leader \
  --dataset.repo_id=physvoice/golden_red --dataset.root=$PWD/recordings/golden_red \
  --dataset.single_task="put the red cube in the left white box" \
  --dataset.num_episodes=1 --dataset.episode_time_s=60 --dataset.reset_time_s=10 --dataset.fps=30 \
  --dataset.video=true --dataset.push_to_hub=false --display_data=false --play_sounds=false \
  --dataset.num_image_writer_processes=0 --dataset.num_image_writer_threads_per_camera=4
```
- blue: `golden_blue` / `"put the blue cube in the right white box"`
- stack: `golden_stack` / `"stack the cubes into a tower"`

> 데이터셋은 `--dataset.root` 에 **직접** 저장된다(`recordings/golden_red/{meta,data,videos}`). task_map 의 `root` 와 동일하게 유지할 것.
> 공유가 필요하면 lerobot 의 HF Hub 푸시를 쓰고 task_map 의 `repo_id` 를 그 HF id 로 바꾸면 된다(이 경우 `root` 생략 가능).
