"""
STT 결과 → 가장 가까운 유효 명령어 매핑 → Task ID

흐름:
  raw STT text
    → normalize_korean_command()  (공백 정리 등 경량 전처리)
    → fuzzy_match()               (Levenshtein으로 정답 명령어 중 최근접)
    → parse_command()             (매핑된 정답 문자열에서 Task ID 추출)
"""

# =============================================================================
# 정답 명령어 목록 (이것만 관리하면 됨)
# =============================================================================

VALID_COMMANDS = [
    "빨간색 박스 집어",
    "파란색 박스 집어",
    "초록색 박스 집어",
    "빨간색 박스 넣어",
    "파란색 박스 넣어",
    "초록색 박스 넣어",
    "빨간색 박스 집어서 넣어",
    "파란색 박스 집어서 넣어",
    "초록색 박스 집어서 넣어",
]

# 명령어 → Task ID 직접 매핑
COMMAND_TO_TASK = {
    "빨간색 박스 집어":         "TASK_PICK_RED_BOX",
    "파란색 박스 집어":         "TASK_PICK_BLUE_BOX",
    "초록색 박스 집어":         "TASK_PICK_GREEN_BOX",
    "빨간색 박스 넣어":         "TASK_PUT_RED_BOX",
    "파란색 박스 넣어":         "TASK_PUT_BLUE_BOX",
    "초록색 박스 넣어":         "TASK_PUT_GREEN_BOX",
    "빨간색 박스 집어서 넣어":  "TASK_PICK_PUT_RED_BOX",
    "파란색 박스 집어서 넣어":  "TASK_PICK_PUT_BLUE_BOX",
    "초록색 박스 집어서 넣어":  "TASK_PICK_PUT_GREEN_BOX",
}

FUZZY_THRESHOLD = 0.5  # 유사도 이 미만이면 매핑 실패로 처리

# =============================================================================
# 전처리
# =============================================================================

# "피식아"의 STT 오인식 패턴 — 텍스트 앞에 붙으면 제거.
# Whisper 가 "피식아"를 다양하게 흘려듣기 때문에 넉넉히 둔다(시연 안정성).
_WAKE_WORD_PATTERNS = [
    "피식아", "피식하", "피식야", "피식가", "피식카", "피식",
    "피시가", "피시카", "피시각", "피싯아", "피싯", "피슥아", "피슥",
    "피석아", "피섹아", "피씩아", "피씨카", "피지카", "피직아", "피칙아",
    "피싱이야", "피싱아", "피쉬카", "피쉬아", "비식아", "비싯아", "비싸",
    "이시각", "시각", "PC가", "pc가", "pc야", "삐식아", "삐식",
]

def _strip_wake_word(text: str) -> str:
    """텍스트 앞에 붙은 웨이크 워드 오인식 패턴 제거."""
    t = text.strip()
    for pat in _WAKE_WORD_PATTERNS:
        if t.lower().startswith(pat.lower()):
            t = t[len(pat):].lstrip(" ,?!.")
            break
    return t

def normalize_korean_command(text: str) -> str:
    text = _strip_wake_word(text)
    return " ".join(text.strip().split())

# =============================================================================
# Levenshtein 편집거리
# =============================================================================

def _levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            dp[j] = prev[j - 1] if a[i - 1] == b[j - 1] else 1 + min(prev[j], dp[j - 1], prev[j - 1])
    return dp[n]

# =============================================================================
# 퍼지 매칭: STT 결과 → 가장 가까운 정답 명령어
# =============================================================================

def fuzzy_match(text: str) -> tuple[str | None, float]:
    """
    VALID_COMMANDS 중 편집거리가 가장 짧은 명령어를 반환.
    공백 제거 후 비교하므로 띄어쓰기 차이에 강건함.
    반환: (matched_command or None, similarity_score)
    """
    text_c = text.replace(" ", "")
    best_cmd, best_score = None, -1.0

    for cmd in VALID_COMMANDS:
        cmd_c = cmd.replace(" ", "")
        dist  = _levenshtein(text_c, cmd_c)
        score = 1.0 - dist / max(len(text_c), len(cmd_c), 1)
        if score > best_score:
            best_score = score
            best_cmd   = cmd

    if best_score >= FUZZY_THRESHOLD:
        return best_cmd, best_score
    return None, best_score

# =============================================================================
# 색상 폴백 — 풀 문장 매칭이 실패해도 "색"만 잡히면 pick&place 로 라우팅
#   ("빨간색", "빨강색", "빨간 거 넣어줘" 등 자유로운 발화 대응 — 시연 안정성)
#   이 로봇이 할 수 있는 건 색별 pick&place 뿐이므로 색=의도로 본다.
# =============================================================================

_COLOR_TO_PICKPUT = {
    "red":   ("빨간색 박스 집어서 넣어", "TASK_PICK_PUT_RED_BOX"),
    "blue":  ("파란색 박스 집어서 넣어", "TASK_PICK_PUT_BLUE_BOX"),
    "green": ("초록색 박스 집어서 넣어", "TASK_PICK_PUT_GREEN_BOX"),  # 모델 없음 → router 가 미지원 처리
}

# 색 토큰(공백 제거·소문자 후 부분일치). "빨간색"⊃"빨간", "빨강색"⊃"빨강" 등.
_COLOR_TOKENS = {
    "red":   ["빨간", "빨강", "빨갠", "red", "레드"],
    "blue":  ["파란", "파랑", "파람", "blue", "블루"],
    "green": ["초록", "녹색", "초로", "green", "그린"],
}

def detect_color(text: str) -> "str | None":
    """발화에서 색 의도를 추출 (없으면 None). red/blue/green 순으로 첫 매치."""
    t = text.replace(" ", "").lower()
    for color, toks in _COLOR_TOKENS.items():
        if any(tok in t for tok in toks):
            return color
    return None

# stacking(쌓기) 키워드 — 색상보다 먼저 본다(쌓기는 색과 무관한 별도 동작).
_STACK_TOKENS = ["쌓", "스택", "stack", "포개", "쌓아", "쌓기"]

def detect_stack(text: str) -> bool:
    t = text.replace(" ", "").lower()
    return any(tok.lower() in t for tok in _STACK_TOKENS)

# =============================================================================
# 파싱 (fuzzy match → Task ID)
# =============================================================================

def parse_command(text: str) -> dict:
    # stacking(쌓기) 우선 — 색과 무관한 별도 동작이라 색상 매핑보다 먼저 본다.
    if detect_stack(text):
        return {
            "raw": text,
            "matched": "쌓기",
            "similarity": 1.0,
            "task_id": "TASK_STACK",
            "status": "SUCCESS",
            "reason": "stacking 키워드",
        }

    # 색상 우선(color-dominant): 이 로봇이 하는 일은 "색별 pick&place" 뿐이라
    # 발화에 색이 잡히면 표현이 어떻든 그 색 pick&place 로 보낸다(시연 안정성).
    #   "빨간색", "빨강 거 넣어줘", "파란색 큐브 집어" 등 모두 대응.
    #   색이 없을 때만 기존 퍼지매칭으로 폴백.
    color = detect_color(text)
    if color is not None:
        cmd, task_id = _COLOR_TO_PICKPUT[color]
        _, score = fuzzy_match(text)
        return {
            "raw": text,
            "matched": cmd,
            "similarity": round(score, 2),
            "task_id": task_id,
            "status": "SUCCESS",
            "reason": f"색상 매핑 ({color})",
        }

    matched_cmd, score = fuzzy_match(text)
    if matched_cmd is None:
        return {
            "raw": text,
            "matched": None,
            "similarity": round(score, 2),
            "task_id": "TASK_UNKNOWN",
            "status": "FAIL",
            "reason": f"유사 명령어 없음 (최고 유사도 {score:.2f})",
        }

    task_id = COMMAND_TO_TASK[matched_cmd]
    return {
        "raw": text,
        "matched": matched_cmd,
        "similarity": round(score, 2),
        "task_id": task_id,
        "status": "SUCCESS",
        "reason": "success",
    }
