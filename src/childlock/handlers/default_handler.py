"""!
\\brief UNIT-006 DefaultHandler — 설계 가정(명시적 OEM 요구 없음), 항상 처리하는 폴백.
\\implements UNIT-006
"""

from childlock.interfaces import IPriorityHandler
from childlock.types import HandlerResult, LockDecision

NO_CONDITION_MATCHED_REASON = "NO_CONDITION_MATCHED"
"""!\\brief 다른 어떤 Handler도 해당하지 않을 때의 사유코드."""


class DefaultHandler(IPriorityHandler):
    """!
    \\brief 우선순위 4(최종) — 앞의 3개 Handler가 모두 미해당일 때 직전 출력을 그대로 유지한다.
    """

    def tryHandle(self, signal, previous) -> HandlerResult:
        """!
        \\brief 직전 확정 좌/우 출력을 그대로 유지하고 시스템 상태만 최신화한다.
        \\param signal 검증된 신호 — systemStateHint만 사용한다.
        \\param previous 직전 확정 LockDecision — 좌/우를 그대로 반환한다.
        \\return 항상 handled=True.
        """
        unchangedDecision = LockDecision(
            leftState=previous.leftState,
            rightState=previous.rightState,
            systemState=signal.systemStateHint,
            reasonCode=NO_CONDITION_MATCHED_REASON,
        )
        return HandlerResult(
            handled=True, decision=unchangedDecision, reasonCode=NO_CONDITION_MATCHED_REASON
        )
