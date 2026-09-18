"""!
\\brief UNIT-006 DefaultHandler 단위시험 — 설계 가정(폴백).
"""

import unittest

from childlock.handlers.default_handler import DefaultHandler
from childlock.types import (
    CrashStatus,
    LockDecision,
    LockState,
    SystemState,
    ValidatedSignalSnapshot,
)


class TestDefaultHandler(unittest.TestCase):
    def setUp(self):
        """!\\brief 매 테스트마다 새 DefaultHandler 인스턴스를 준비한다."""
        self.handler = DefaultHandler()

    def testTryHandleAlwaysHandlesRegardlessOfSignal(self):
        """!
        \\brief 어떤 신호가 와도 항상 handled=True를 반환하는지 검증한다(§4 계약).
        \\technique 동등분할
        \\case 긍정(Positive)
        """
        signal = ValidatedSignalSnapshot(
            crashStatus=CrashStatus.NONE, crashStatusValid=True,
            approachRiskLeft=False, approachRiskLeftValid=True,
            approachRiskRight=False, approachRiskRightValid=True,
            sensorFault=False, sensorFaultValid=True,
            systemStateHint=SystemState.DEGRADED,
        )
        previous = LockDecision(
            leftState=LockState.LOCKED, rightState=LockState.RELEASED,
            systemState=SystemState.NORMAL, reasonCode="PREV",
        )
        result = self.handler.tryHandle(signal, previous)
        self.assertTrue(result.handled)
        self.assertEqual(result.decision.leftState, previous.leftState)
        self.assertEqual(result.decision.rightState, previous.rightState)
        self.assertEqual(result.decision.systemState, SystemState.DEGRADED)

    def testTryHandlePreservesPreviousLockStatesUnchanged(self):
        """!
        \\brief 좌/우 출력이 직전 상태와 정확히 동일하게 유지되는지 검증한다(변화 없음).
        \\technique 경계값분석(변화 0건이라는 경계)
        \\case 부정(Negative) — "아무 조건도 매칭되지 않음"이라는 예외적 흐름을 다룸
        """
        signal = ValidatedSignalSnapshot(
            crashStatus=CrashStatus.NONE, crashStatusValid=True,
            approachRiskLeft=False, approachRiskLeftValid=True,
            approachRiskRight=False, approachRiskRightValid=True,
            sensorFault=False, sensorFaultValid=True,
            systemStateHint=SystemState.NORMAL,
        )
        previous = LockDecision(
            leftState=LockState.RELEASED, rightState=LockState.LOCKED,
            systemState=SystemState.NORMAL, reasonCode="PREV",
        )
        result = self.handler.tryHandle(signal, previous)
        self.assertEqual(result.decision.leftState, LockState.RELEASED)
        self.assertEqual(result.decision.rightState, LockState.LOCKED)


if __name__ == "__main__":
    unittest.main()
