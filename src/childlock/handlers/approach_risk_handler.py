"""!
\\brief UNIT-005 ApproachRiskHandler — SWR-005, SWR-006, SWR-009 구현.
\\implements UNIT-005
"""

from childlock.interfaces import IPriorityHandler
from childlock.types import HandlerResult, LockDecision, LockState

SUPPRESSED_APPROACH_RISK_REASON = "SUPPRESSED_APPROACH_RISK"
"""!\\brief SWR-005/006 접근위험 잠금 사유코드."""


class ApproachRiskHandler(IPriorityHandler):
    """!
    \\brief 우선순위 3 — 접근위험 도어를 LOCK하고 해제요청을 억제(SWR-005/006), 좌/우 독립 처리(SWR-009).
    """

    def tryHandle(self, signal, previous) -> HandlerResult:
        """!
        \\brief 좌/우 접근위험을 각각 판단해 해당 도어만 LOCK으로 확정한다.
        \\param signal 검증된 신호.
        \\param previous 직전 확정 LockDecision — 위험이 없는 쪽 도어를 유지하는 데 사용한다.
        \\return 양쪽 모두 위험 아님이면 handled=False, 하나라도 위험이면 handled=True.
        """
        leftRiskActive = signal.approachRiskLeftValid and signal.approachRiskLeft
        rightRiskActive = signal.approachRiskRightValid and signal.approachRiskRight
        if not leftRiskActive and not rightRiskActive:
            return HandlerResult(handled=False, decision=None, reasonCode="")
        newLeftState = LockState.LOCKED if leftRiskActive else previous.leftState
        newRightState = LockState.LOCKED if rightRiskActive else previous.rightState
        lockDecision = LockDecision(
            leftState=newLeftState,
            rightState=newRightState,
            systemState=signal.systemStateHint,
            reasonCode=SUPPRESSED_APPROACH_RISK_REASON,
        )
        return HandlerResult(
            handled=True, decision=lockDecision, reasonCode=SUPPRESSED_APPROACH_RISK_REASON
        )
