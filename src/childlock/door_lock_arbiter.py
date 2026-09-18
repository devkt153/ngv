"""!
\\brief UNIT-002 DoorLockArbiter — 우선순위 체인 오케스트레이션(CMP-002).
\\implements UNIT-002
"""

import logging

from childlock.types import HandlerResult, LockDecision, LockState, SystemState

childlockLogger = logging.getLogger("childlock")

INITIAL_LOCK_DECISION = LockDecision(
    leftState=LockState.RELEASED,
    rightState=LockState.RELEASED,
    systemState=SystemState.NORMAL,
    reasonCode="INITIAL_STATE",
)
"""!
\\brief 시동 시 초기 상태(설계 가정 — OEM 미명시, SWD-001 §8 재확인 필요).
"""


def trySingleHandler(targetHandler, signal, previous):
    """!
    \\brief targetHandler.tryHandle()을 안전하게 호출한다(예외를 not-handled로 치환).
    \\param targetHandler IPriorityHandler 구현체.
    \\param signal 검증된 신호.
    \\param previous 직전 확정 LockDecision.
    \\return targetHandler의 결과, 또는 예외 시 handled=False.
    \\post 예외를 호출자(evaluate)에 전파하지 않는다(SWD-001 §9 안전 폴백).
    """
    try:
        return targetHandler.tryHandle(signal, previous)
    except Exception as internalError:  # noqa: BLE001 - 의도적 방어 처리(SWD-001 §9)
        childlockLogger.error(
            "Handler %s raised %s", type(targetHandler).__name__, internalError
        )
        return HandlerResult(handled=False, decision=None, reasonCode="HANDLER_INTERNAL_ERROR")


class DoorLockArbiter:
    """!
    \\brief UNIT-002 — Handler 체인을 우선순위 순서(충돌>센서고장>접근위험>기본)로 호출한다.
    """

    def __init__(self, crashHandler, sensorFaultHandler, approachRiskHandler, defaultHandler):
        """!
        \\brief 4개 Handler를 우선순위 순서로 주입받는다(DIP — 구체 클래스가 아닌 IPriorityHandler에 의존).
        """
        self.handlerChain = [
            crashHandler,
            sensorFaultHandler,
            approachRiskHandler,
            defaultHandler,
        ]
        self.previousDecision = INITIAL_LOCK_DECISION

    def evaluate(self, signal) -> LockDecision:
        """!
        \\brief 우선순위 체인을 순서대로 호출해 첫 handled=True 결과를 확정 결정으로 삼는다.
        \\param signal InputValidator가 검증한 신호.
        \\return 확정 LockDecision.
        \\pre defaultHandler는 항상 handled=True를 반환해야 한다(§4 계약, UNIT-006).
        """
        for currentHandler in self.handlerChain:
            handlerResult = trySingleHandler(currentHandler, signal, self.previousDecision)
            if handlerResult.handled:
                self.previousDecision = handlerResult.decision
                return self.previousDecision
        raise AssertionError("unreachable: defaultHandler must always handle")
