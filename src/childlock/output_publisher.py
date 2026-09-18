"""!
\\brief UNIT-007 OutputPublisher — OEM-IF-005(Actuator model) 발행.
\\implements UNIT-007
"""

import logging
from abc import ABC, abstractmethod

from childlock.types import LockDecision

childlockLogger = logging.getLogger("childlock")


class ActuatorPort(ABC):
    """!
    \\brief OEM-IF-005(Actuator model)로의 발행 포트. 실제 HW/CAN 계층은 범위 밖(SWD-001 §13).
    """

    @abstractmethod
    def applyLockDecision(self, decision: LockDecision) -> None:
        """!
        \\brief 좌/우 LockState를 액추에이터 모델에 반영한다.
        """
        raise NotImplementedError


class InMemoryActuatorPort(ActuatorPort):
    """!
    \\brief PC/SIL용 인메모리 액추에이터 모델(테스트/시뮬레이션 기본 구현).
    """

    def __init__(self) -> None:
        """!\\brief 마지막으로 적용된 결정을 None으로 초기화한다."""
        self.lastApplied = None

    def applyLockDecision(self, decision: LockDecision) -> None:
        """!\\brief 결정을 인메모리에 저장한다(부수효과 없음, 예외 없음)."""
        self.lastApplied = decision


class OutputPublisher:
    """!
    \\brief UNIT-007 — 확정 LockDecision을 ActuatorPort로 발행한다(CMP-003).
    """

    def __init__(self, actuatorPort: ActuatorPort) -> None:
        """!
        \\brief 발행 대상 포트를 주입받는다(DIP — 구체 액추에이터가 아니라 추상 포트에 의존).
        \\param actuatorPort OEM-IF-005 발행 대상.
        """
        self.actuatorPort = actuatorPort

    def publish(self, decision: LockDecision) -> None:
        """!
        \\brief decision을 액추에이터 포트로 발행한다.
        \\param decision 좌/우·시스템상태가 모두 확정된 LockDecision.
        \\post 발행 실패는 로깅만 하고 예외를 호출자에 전파하지 않는다(SWD-001 §10).
        """
        try:
            self.actuatorPort.applyLockDecision(decision)
        except Exception as publishError:  # noqa: BLE001 - 의도적 방어 처리(SWD-001 §10)
            childlockLogger.error("OutputPublisher publish failed: %s", publishError)
