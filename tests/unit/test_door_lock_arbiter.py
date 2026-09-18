"""!
\\brief UNIT-002 DoorLockArbiter 단위시험 — 우선순위 체인 오케스트레이션.
"""

import unittest

from childlock.door_lock_arbiter import DoorLockArbiter, INITIAL_LOCK_DECISION
from childlock.handlers.approach_risk_handler import ApproachRiskHandler
from childlock.handlers.crash_release_handler import CrashReleaseHandler
from childlock.handlers.default_handler import DefaultHandler
from childlock.handlers.sensor_fault_handler import SensorFaultHandler
from childlock.interfaces import IPriorityHandler
from childlock.types import (
    CrashStatus,
    HandlerResult,
    LockState,
    SystemState,
    ValidatedSignalSnapshot,
)


def makeSignal(crashStatus=CrashStatus.NONE, sensorFault=False, leftRisk=False, rightRisk=False):
    """!\\brief 테스트용 ValidatedSignalSnapshot 생성 헬퍼(테스트 유틸리티)."""
    return ValidatedSignalSnapshot(
        crashStatus=crashStatus, crashStatusValid=True,
        approachRiskLeft=leftRisk, approachRiskLeftValid=True,
        approachRiskRight=rightRisk, approachRiskRightValid=True,
        sensorFault=sensorFault, sensorFaultValid=True,
        systemStateHint=SystemState.NORMAL,
    )


class RaisingHandler(IPriorityHandler):
    """!\\brief 예외 폴백 경로를 검증하기 위한 테스트 전용 IPriorityHandler 구현(테스트 유틸리티)."""

    def tryHandle(self, signal, previous):
        """!\\brief 항상 내부 오류를 발생시킨다."""
        raise RuntimeError("simulated handler failure")


class ContractViolatingDefaultHandler(IPriorityHandler):
    """!
    \\brief §4 계약(defaultHandler는 항상 handled=True)을 어기는 테스트 전용 스텁 — 방어적
    AssertionError 경로 검증 전용(테스트 유틸리티).
    """

    def tryHandle(self, signal, previous):
        """!\\brief 계약을 위반해 항상 handled=False를 반환한다."""
        return HandlerResult(handled=False, decision=None, reasonCode="")


def makeArbiter():
    """!\\brief 실제 4개 Handler로 구성된 DoorLockArbiter를 생성하는 헬퍼."""
    return DoorLockArbiter(
        crashHandler=CrashReleaseHandler(),
        sensorFaultHandler=SensorFaultHandler(),
        approachRiskHandler=ApproachRiskHandler(),
        defaultHandler=DefaultHandler(),
    )


class TestDoorLockArbiter(unittest.TestCase):
    def testEvaluateGivesCrashReleaseTopPriorityOverSensorFault(self):
        """!
        \\brief crash_status=CONFIRMED와 sensor_fault=TRUE가 동시에 성립해도 RELEASE가 이기는지 검증한다.
        \\technique 결정테이블(§7 정책 의사결정표 1행)
        \\case 긍정(Positive)
        """
        arbiter = makeArbiter()
        signal = makeSignal(crashStatus=CrashStatus.CONFIRMED, sensorFault=True)
        decision = arbiter.evaluate(signal)
        self.assertEqual(decision.leftState, LockState.RELEASED)
        self.assertEqual(decision.rightState, LockState.RELEASED)

    def testEvaluateGivesSensorFaultPriorityOverApproachRisk(self):
        """!
        \\brief sensor_fault=TRUE와 접근위험=TRUE가 동시에 성립하면 센서고장 홀드가 이기는지 검증한다.
        \\technique 결정테이블(§7 정책 의사결정표 2행)
        \\case 긍정(Positive)
        """
        arbiter = makeArbiter()
        arbiter.previousDecision = INITIAL_LOCK_DECISION
        signal = makeSignal(sensorFault=True, leftRisk=True)
        decision = arbiter.evaluate(signal)
        self.assertEqual(decision.systemState, SystemState.FAULT)
        self.assertEqual(decision.leftState, INITIAL_LOCK_DECISION.leftState)

    def testEvaluateFallsBackToDefaultWhenNoConditionMatches(self):
        """!
        \\brief 아무 조건도 매칭되지 않으면 DefaultHandler가 처리하는지 검증한다(§7 정책 의사결정표 4행).
        \\technique 결정테이블
        \\case 부정(Negative)
        """
        arbiter = makeArbiter()
        decision = arbiter.evaluate(makeSignal())
        self.assertEqual(decision.reasonCode, "NO_CONDITION_MATCHED")

    def testEvaluateTreatsHandlerExceptionAsNotHandled(self):
        """!
        \\brief 체인 중간 Handler가 예외를 던져도 다음 Handler로 안전하게 넘어가는지 검증한다(SWD-001 §9).
        \\technique 오류추정
        \\case 부정(Negative)
        """
        arbiter = DoorLockArbiter(
            crashHandler=RaisingHandler(),
            sensorFaultHandler=RaisingHandler(),
            approachRiskHandler=RaisingHandler(),
            defaultHandler=DefaultHandler(),
        )
        decision = arbiter.evaluate(makeSignal())
        self.assertEqual(decision.reasonCode, "NO_CONDITION_MATCHED")

    def testEvaluateRaisesAssertionErrorWhenDefaultHandlerContractViolated(self):
        """!
        \\brief defaultHandler가 계약(항상 handled=True)을 어기면 방어적 AssertionError가 발생하는지 검증한다.
        \\technique 오류추정 + 결정테이블(도달 불가 경로)
        \\case 부정(Negative)
        """
        arbiter = DoorLockArbiter(
            crashHandler=RaisingHandler(),
            sensorFaultHandler=RaisingHandler(),
            approachRiskHandler=RaisingHandler(),
            defaultHandler=ContractViolatingDefaultHandler(),
        )
        with self.assertRaises(AssertionError):
            arbiter.evaluate(makeSignal())

    def testEvaluatePersistsDecisionAcrossSuccessiveCalls(self):
        """!
        \\brief 한 사이클에서 확정된 결정이 previousDecision으로 다음 사이클에 전달되는지 검증한다.
        \\technique 상태전이
        \\case 긍정(Positive)
        """
        arbiter = makeArbiter()
        arbiter.evaluate(makeSignal(leftRisk=True))
        secondDecision = arbiter.evaluate(makeSignal())
        self.assertEqual(secondDecision.leftState, LockState.LOCKED)


if __name__ == "__main__":
    unittest.main()
