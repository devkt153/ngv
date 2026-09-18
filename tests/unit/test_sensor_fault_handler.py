"""!
\\brief UNIT-004 SensorFaultHandler 단위시험 — SWR-021a, SWR-021b.
"""

import unittest

from childlock.handlers.sensor_fault_handler import SensorFaultHandler
from childlock.types import (
    CrashStatus,
    LockDecision,
    LockState,
    SystemState,
    ValidatedSignalSnapshot,
)


def makeSignal(sensorFault=False, sensorFaultValid=True):
    """!\\brief 테스트용 ValidatedSignalSnapshot 생성 헬퍼(테스트 유틸리티)."""
    return ValidatedSignalSnapshot(
        crashStatus=CrashStatus.NONE,
        crashStatusValid=True,
        approachRiskLeft=False,
        approachRiskLeftValid=True,
        approachRiskRight=False,
        approachRiskRightValid=True,
        sensorFault=sensorFault,
        sensorFaultValid=sensorFaultValid,
        systemStateHint=SystemState.NORMAL,
    )


PREVIOUS_MIXED = LockDecision(
    leftState=LockState.LOCKED, rightState=LockState.RELEASED,
    systemState=SystemState.NORMAL, reasonCode="PREV",
)


class TestSensorFaultHandler(unittest.TestCase):
    def setUp(self):
        """!\\brief 매 테스트마다 새 SensorFaultHandler 인스턴스를 준비한다."""
        self.handler = SensorFaultHandler()

    def testTryHandleHoldsPreviousOutputWhenSensorFaultTrue(self):
        """!
        \\brief sensor_fault=TRUE이면 직전 좌/우 출력을 그대로 유지하는지 검증한다(SWR-021a).
        \\technique 동등분할
        \\case 긍정(Positive)
        """
        signal = makeSignal(sensorFault=True)
        result = self.handler.tryHandle(signal, PREVIOUS_MIXED)
        self.assertTrue(result.handled)
        self.assertEqual(result.decision.leftState, PREVIOUS_MIXED.leftState)
        self.assertEqual(result.decision.rightState, PREVIOUS_MIXED.rightState)

    def testTryHandleSetsFaultSystemStateWhenSensorFaultTrue(self):
        """!
        \\brief sensor_fault=TRUE이면 시스템 상태가 FAULT로 설정되는지 검증한다(SWR-021b).
        \\technique 동등분할
        \\case 긍정(Positive)
        """
        signal = makeSignal(sensorFault=True)
        result = self.handler.tryHandle(signal, PREVIOUS_MIXED)
        self.assertEqual(result.decision.systemState, SystemState.FAULT)

    def testTryHandleDoesNotHandleWhenSensorFaultFalse(self):
        """!
        \\brief sensor_fault=FALSE이면 이 Handler가 처리하지 않는지 검증한다.
        \\technique 동등분할
        \\case 부정(Negative)
        """
        signal = makeSignal(sensorFault=False)
        result = self.handler.tryHandle(signal, PREVIOUS_MIXED)
        self.assertFalse(result.handled)

    def testTryHandleDoesNotHandleWhenSensorFaultInvalid(self):
        """!
        \\brief sensorFaultValid=False이면 TRUE 값이라도 처리하지 않는지 검증한다.
        \\technique 오류추정
        \\case 부정(Negative)
        """
        signal = makeSignal(sensorFault=True, sensorFaultValid=False)
        result = self.handler.tryHandle(signal, PREVIOUS_MIXED)
        self.assertFalse(result.handled)


if __name__ == "__main__":
    unittest.main()
