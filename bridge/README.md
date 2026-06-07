# bridge/ — 음성 ↔ 로봇 다리

voice 가 뽑은 Task ID 를 받아 lerobot 추론을 구동하는 중간 계층.

**구현 단계에 작성할 것:**
- `listener.py` — voice 출력(Task ID) 수신
- `router.py` — `config/task_map.yaml` 조회 → (정책, 영어 task). 없으면 "미지원"
- `dispatcher.py` — `config/robot_profile.yaml` + 라우팅 결과로
  `lerobot-record` subprocess 구성·실행 (명령마다 1회)
- `feedback.py` — 성공/실패/미지원 음성·로그 피드백
- `main.py` — 엔트리포인트 (run.sh 가 호출)

**흐름**: Task ID → router → dispatcher → `lerobot-record` → SO101 → 결과 피드백 → 대기 복귀
