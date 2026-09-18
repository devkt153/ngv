"""!
\\brief SWA-001 IF-INT-002 / SWD-001 §4에 대응하는 IPriorityHandler 인터페이스.
\\implements UNIT-003, UNIT-004, UNIT-005, UNIT-006
"""

from abc import ABC, abstractmethod

from childlock.types import HandlerResult, LockDecision, ValidatedSignalSnapshot


class IPriorityHandler(ABC):
    """!
    \\brief 우선순위 체인의 각 Handler가 구현하는 좁은 인터페이스(ISP).
    """

    @abstractmethod
    def tryHandle(
        self, signal: ValidatedSignalSnapshot, previous: LockDecision
    ) -> HandlerResult:
        """!
        \\brief 이 Handler가 현재 신호를 처리할지 판단하고, 처리하면 결정을 반환한다.
        \\param signal InputValidator가 검증한 신호.
        \\param previous 직전 평가주기의 확정 LockDecision.
        \\return handled=True면 decision이 완전히 채워짐, False면 decision=None.
        """
        raise NotImplementedError  # pragma: no cover - 추상 계약, 구현체가 항상 override함
