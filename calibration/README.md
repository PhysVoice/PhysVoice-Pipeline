# calibration/ — SO101 캘리브레이션

이 **물리 로봇 개체 전용** 모터 영점값 (다른 로봇이면 새로 캘리 필요).
(출처: smolvla-red-blue-training/robot/calibration)

```
calibration/
├── robots/so101_follower/my_follower.json       ← 추론 필수 (robot_profile.yaml 가 참조)
└── teleoperators/so101_leader/my_leader.json     ← 텔레옵/데이터수집용
```

`config/robot_profile.yaml` 의 `robot.calibration_dir` → `calibration/robots/so101_follower`
(dispatcher 가 절대경로로 변환해 lerobot-record 에 전달).

> ⚠️ **다른 로봇 개체**에 연결하면 이 값은 안 맞습니다. 새 로봇이면 lerobot 으로 재캘리 후 교체하세요.
> GPU 학습 머신(로봇 미연결)에는 불필요.
