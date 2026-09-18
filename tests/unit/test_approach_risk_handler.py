"""!
\\brief UNIT-005 ApproachRiskHandler 단위시험 — SWR-005, SWR-006, SWR-009.
"""

import unittest

from childlock.handlers.approach_risk_handler import ApproachRiskHandler
from childlock.types import (
    CrashStatus,
    LockDecision,
    LockState,
    SystemState,
    ValidatedSignalSnapshot,
)


def makeSignal(leftRisk=False, rightRisk=False):
    """!\\brief 테스트용 ValidatedSignalSnapshot 생성 헬퍼(테스트 유틸리티)."""
    return ValidatedSignalSnapshot(
        crashStatus=CrashStatus.NONE,
        crashStatusValid=True,
        approachRiskLeft=leftRisk,
        approachRiskLeftValid=True,
        approachRiskRight=rightRisk,
        approachRiskRightValid=True,
        sensorFault=False,
        sensorFaultValid=True,
        systemStateHint=SystemState.NORMAL,
    )


PREVIOUS_BOTH_RELEASED = LockDecision(
    leftState=LockState.RELEASED, rightState=LockState.RELEASED,
    systemState=SystemState.NORMAL, reasonCode="PREV",
)


class TestApproachRiskHandler(unittest.TestCase):
    def setUp(self):
        """!\\brief 매 테스트마다 새 ApproachRiskHandler 인스턴스를 준비한다."""
        self.handler = ApproachRiskHandler()

    def testTryHandleLocksLeftDoorOnlyWhenOnlyLeftRiskActive(self):
        """!
        \\brief 좌측만 접근위험이면 좌측만 LOCK되고 우측은 영향받지 않는지 검증한다(SWR-005, SWR-009).
        \\technique 동등분할(좌우 조합)
        \\case 긍정(Positive)
        """
        signal = makeSignal(leftRisk=True, rightRisk=False)
        result = self.handler.tryHandle(signal, PREVIOUS_BOTH_RELEASED)
        self.assertTrue(result.handled)
        self.assertEqual(result.decision.leftState, LockState.LOCKED)
        self.assertEqual(result.decision.rightState, PREVIOUS_BOTH_RELEASED.rightState)

    def testTryHandleLocksRightDoorOnlyWhenOnlyRightRiskActive(self):
        """!
        \\brief 우측만 접근위험이면 우측만 LOCK되고 좌측은 영향받지 않는지 검증한다(SWR-009).
        \\technique 동등분할(좌우 조합)
        \\case 긍정(Positive)
        """
        signal = makeSignal(leftRisk=False, rightRisk=True)
        result = self.handler.tryHandle(signal, PREVIOUS_BOTH_RELEASED)
        self.assertEqual(result.decision.rightState, LockState.LOCKED)
        self.assertEqual(result.decision.leftState, PREVIOUS_BOTH_RELEASED.leftState)

    def testTryHandleLocksBothDoorsWhenBothRiskActive(self):
        """!
        \\brief 양쪽 모두 접근위험이면 양쪽 모두 LOCK되는지 검증한다.
        \\technique 동등분할(좌우 조합)
        \\case 긍정(Positive)
        """
        signal = makeSignal(leftRisk=True, rightRisk=True)
        result = self.handler.tryHandle(signal, PREVIOUS_BOTH_RELEASED)
        self.assertEqual(result.decision.leftState, LockState.LOCKED)
        self.assertEqual(result.decision.rightState, LockState.LOCKED)

    def testTryHandleDoesNotHandleWhenNeitherDoorAtRisk(self):
        """!
        \\brief 양쪽 모두 접근위험이 아니면 이 Handler가 처리하지 않는지 검증한다.
        \\technique 동등분할(좌우 조합)
        \\case 부정(Negative)
        """
        signal = makeSignal(leftRisk=False, rightRisk=False)
        result = self.handler.tryHandle(signal, PREVIOUS_BOTH_RELEASED)
        self.assertFalse(result.handled)

    def testTryHandleIgnoresInvalidRiskFlag(self):
        """!
        \\brief approachRiskLeftValid=False이면 True 값이라도 위험으로 간주하지 않는지 검증한다.
        \\technique 오류추정
        \\case 부정(Negative)
        """
        signal = ValidatedSignalSnapshot(
            crashStatus=CrashStatus.NONE, crashStatusValid=True,
            approachRiskLeft=True, approachRiskLeftValid=False,
            approachRiskRight=False, approachRiskRightValid=True,
            sensorFault=False, sensorFaultValid=True,
            systemStateHint=SystemState.NORMAL,
        )
        result = self.handler.tryHandle(signal, PREVIOUS_BOTH_RELEASED)
        self.assertFalse(result.handled)


if __name__ == "__main__":
    unittest.main()
