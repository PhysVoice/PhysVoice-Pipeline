# calibration/ — SO101 캘리브레이션

이 **물리 로봇 개체 전용** 모터 영점값 (다른 로봇이면 새로 캘리 필요).

**구현 단계에 가져올 것** (smolvla-red-blue-training/robot/calibration 에서 복사):
```
calibration/robots/so101_follower/my_follower.json
```

`config/robot_profile.yaml` 의 `robot.calibration_dir` 가 이 폴더를 가리킨다.

> ⚠️ GPU 학습 머신(로봇 미연결)에는 불필요. 추론(로봇 연결) PC 에만 있으면 됨.
