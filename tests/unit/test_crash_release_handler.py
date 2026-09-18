"""!
\\brief UNIT-003 CrashReleaseHandler 단위시험 — SWR-007, SWR-008.
"""

import unittest

from childlock.handlers.crash_release_handler import CrashReleaseHandler
from childlock.types import (
    CrashStatus,
    LockDecision,
    LockState,
    SystemState,
    ValidatedSignalSnapshot,
)


def makeSignal(crashStatus=CrashStatus.NONE, crashStatusValid=True):
    """!\\brief 테스트용 ValidatedSignalSnapshot 생성 헬퍼(테스트 유틸리티)."""
    return ValidatedSignalSnapshot(
        crashStatus=crashStatus,
        crashStatusValid=crashStatusValid,
        approachRiskLeft=False,
        approachRiskLeftValid=True,
        approachRiskRight=False,
        approachRiskRightValid=True,
        sensorFault=False,
        sensorFaultValid=True,
        systemStateHint=SystemState.NORMAL,
    )


PREVIOUS_LOCKED = LockDecision(
    leftState=LockState.LOCKED, rightState=LockState.LOCKED,
    systemState=SystemState.NORMAL, reasonCode="PREV",
)


class TestCrashReleaseHandler(unittest.TestCase):
    def setUp(self):
        """!\\brief 매 테스트마다 새 CrashReleaseHandler 인스턴스를 준비한다."""
        self.handler = CrashReleaseHandler()

    def testTryHandleReleasesBothDoorsWhenCrashConfirmed(self):
        """!
        \\brief crash_status=CONFIRMED이면 좌/우 모두 RELEASE로 확정하는지 검증한다.
        \\technique 동등분할
        \\case 긍정(Positive)
        """
        signal = makeSignal(crashStatus=CrashStatus.CONFIRMED)
        result = self.handler.tryHandle(signal, PREVIOUS_LOCKED)
        self.assertTrue(result.handled)
        self.assertEqual(result.decision.leftState, LockState.RELEASED)
        self.assertEqual(result.decision.rightState, LockState.RELEASED)

    def testTryHandleDoesNotHandlePendingCrashStatus(self):
        """!
        \\brief crash_status=PENDING이면 이 Handler가 처리하지 않는지 검증한다(SWR-008).
        \\technique 동등분할
        \\case 부정(Negative)
        """
        signal = makeSignal(crashStatus=CrashStatus.PENDING)
        result = self.handler.tryHandle(signal, PREVIOUS_LOCKED)
        self.assertFalse(result.handled)
        self.assertIsNone(result.decision)

    def testTryHandleDoesNotHandleNoneCrashStatus(self):
        """!
        \\brief crash_status=NONE이면 이 Handler가 처리하지 않는지 검증한다(SWR-008).
        \\technique 동등분할
        \\case 부정(Negative)
        """
        signal = makeSignal(crashStatus=CrashStatus.NONE)
        result = self.handler.tryHandle(signal, PREVIOUS_LOCKED)
        self.assertFalse(result.handled)

    def testTryHandleDoesNotHandleInvalidCrashStatus(self):
        """!
        \\brief crashStatusValid=False이면 CONFIRMED 값이라도 처리하지 않는지 검증한다.
        \\technique 오류추정
        \\case 부정(Negative)
        """
        signal = makeSignal(crashStatus=CrashStatus.CONFIRMED, crashStatusValid=False)
        result = self.handler.tryHandle(signal, PREVIOUS_LOCKED)
        self.assertFalse(result.handled)


if __name__ == "__main__":
    unittest.main()
