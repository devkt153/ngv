"""!
\\brief UNIT-003 CrashReleaseHandler — SWR-007, SWR-008 구현.
\\implements UNIT-003
"""

from childlock.interfaces import IPriorityHandler
from childlock.types import CrashStatus, HandlerResult, LockDecision, LockState

CRASH_CONFIRMED_RELEASE_REASON = "CRASH_CONFIRMED_RELEASE"
"""!\\brief SWR-007 충돌 긴급해제 사유코드."""


class CrashReleaseHandler(IPriorityHandler):
    """!
    \\brief 우선순위 1 — crash_status=CONFIRMED 시 좌/우 모두 RELEASE(SWR-007), 그 외 미해당(SWR-008).
    """

    def tryHandle(self, signal, previous) -> HandlerResult:
        """!
        \\brief crash_status가 CONFIRMED(valid)인지 판단해 긴급 해제를 결정한다.
        \\param signal 검증된 신호.
        \\param previous 직전 확정 LockDecision(이 Handler는 사용하지 않음, 계약 유지를 위해 인자만 받음).
        \\return CONFIRMED가 아니면 handled=False(SWR-008), CONFIRMED면 handled=True + 양쪽 RELEASE.
        """
        if not signal.crashStatusValid:
            return HandlerResult(handled=False, decision=None, reasonCode="")
        if signal.crashStatus != CrashStatus.CONFIRMED:
            return HandlerResult(handled=False, decision=None, reasonCode="")
        releaseDecision = LockDecision(
            leftState=LockState.RELEASED,
            rightState=LockState.RELEASED,
            systemState=signal.systemStateHint,
            reasonCode=CRASH_CONFIRMED_RELEASE_REASON,
        )
        return HandlerResult(
            handled=True, decision=releaseDecision, reasonCode=CRASH_CONFIRMED_RELEASE_REASON
        )
