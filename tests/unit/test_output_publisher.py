"""!
\\brief UNIT-007 OutputPublisher 단위시험.
"""

import unittest

from childlock.output_publisher import ActuatorPort, InMemoryActuatorPort, OutputPublisher
from childlock.types import LockDecision, LockState, SystemState

SAMPLE_DECISION = LockDecision(
    leftState=LockState.RELEASED, rightState=LockState.LOCKED,
    systemState=SystemState.NORMAL, reasonCode="TEST",
)


class RaisingActuatorPort(ActuatorPort):
    """!\\brief 발행 실패 경로를 검증하기 위한 테스트 전용 ActuatorPort(테스트 유틸리티)."""

    def applyLockDecision(self, decision):
        """!\\brief 항상 발행 실패를 발생시킨다."""
        raise RuntimeError("simulated actuator failure")


class PassthroughActuatorPort(ActuatorPort):
    """!\\brief 추상 메서드의 기본 구현을 직접 호출하기 위한 테스트 전용 서브클래스(테스트 유틸리티)."""

    def applyLockDecision(self, decision):
        """!\\brief 부모(추상)의 applyLockDecision을 그대로 호출한다."""
        return super().applyLockDecision(decision)


class TestOutputPublisher(unittest.TestCase):
    def testPublishForwardsDecisionToActuatorPort(self):
        """!
        \\brief publish()가 decision을 실제 ActuatorPort로 전달하는지 검증한다.
        \\technique 동등분할
        \\case 긍정(Positive)
        """
        actuatorPort = InMemoryActuatorPort()
        publisher = OutputPublisher(actuatorPort)
        publisher.publish(SAMPLE_DECISION)
        self.assertEqual(actuatorPort.lastApplied, SAMPLE_DECISION)

    def testPublishDoesNotRaiseWhenActuatorPortFails(self):
        """!
        \\brief 발행이 실패해도 publish()가 예외를 호출자에 전파하지 않는지 검증한다(SWD-001 §10).
        \\technique 오류추정
        \\case 부정(Negative)
        """
        publisher = OutputPublisher(RaisingActuatorPort())
        try:
            publisher.publish(SAMPLE_DECISION)
        except Exception as unexpectedError:  # noqa: BLE001
            self.fail(f"publish raised unexpectedly: {unexpectedError}")


    def testAbstractApplyLockDecisionRaisesNotImplementedError(self):
        """!
        \\brief 구현되지 않은 추상 applyLockDecision을 직접 호출하면 NotImplementedError가 발생하는지 검증한다.
        \\technique 오류추정
        \\case 부정(Negative)
        """
        port = PassthroughActuatorPort()
        with self.assertRaises(NotImplementedError):
            port.applyLockDecision(SAMPLE_DECISION)


if __name__ == "__main__":
    unittest.main()
