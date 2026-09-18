"""!
\\brief Phase 1 통합시험 — INT-002 시험 케이스의 실행 코드.
전체 파이프라인(실제 InputValidator → 실제 DoorLockArbiter+4 Handler → 실제 OutputPublisher)을
RawVehicleSignal(OEM-IF-002/003/009 대응)부터 ActuatorPort(OEM-IF-005 대응)까지 실제 객체로 연결해
검증한다(모의객체 미사용).
"""

import unittest

from childlock.door_lock_arbiter import DoorLockArbiter
from childlock.handlers.approach_risk_handler import ApproachRiskHandler
from childlock.handlers.crash_release_handler import CrashReleaseHandler
from childlock.handlers.default_handler import DefaultHandler
from childlock.handlers.sensor_fault_handler import SensorFaultHandler
from childlock.input_validator import InputValidator
from childlock.interfaces import IPriorityHandler
from childlock.output_publisher import ActuatorPort, InMemoryActuatorPort, OutputPublisher
from childlock.types import LockState, RawVehicleSignal, SystemState


class RaisingHandler(IPriorityHandler):
    """!\\brief 통합 레벨 결함주입용 — 항상 예외를 던지는 실제 IPriorityHandler 구현(테스트 유틸리티)."""

    def tryHandle(self, signal, previous):
        """!\\brief 항상 내부 오류를 발생시킨다."""
        raise RuntimeError("simulated integration-level handler failure")


class RaisingActuatorPort(ActuatorPort):
    """!\\brief 통합 레벨 결함주입용 — 항상 발행 실패하는 실제 ActuatorPort 구현(테스트 유틸리티)."""

    def applyLockDecision(self, decision):
        """!\\brief 항상 발행 실패를 발생시킨다."""
        raise RuntimeError("simulated integration-level actuator failure")


class ChildlockPipeline:
    """!
    \\brief 통합시험용 조립 헬퍼 — 실제 7개 유닛을 SWA-001 통합 순서대로 배선한다(테스트 유틸리티).
    """

    def __init__(self):
        """!\\brief InputValidator·Arbiter(4 Handler 포함)·OutputPublisher를 실제 객체로 배선한다."""
        self.inputValidator = InputValidator()
        self.arbiter = DoorLockArbiter(
            crashHandler=CrashReleaseHandler(),
            sensorFaultHandler=SensorFaultHandler(),
            approachRiskHandler=ApproachRiskHandler(),
            defaultHandler=DefaultHandler(),
        )
        self.actuatorPort = InMemoryActuatorPort()
        self.outputPublisher = OutputPublisher(self.actuatorPort)

    def runOneCycle(self, raw: RawVehicleSignal, nowMs: int):
        """!
        \\brief 한 평가주기 전체(IF-INT-001 -> IF-INT-002 -> IF-INT-003)를 실행한다.
        \\return 액추에이터 포트에 실제로 적용된 LockDecision.
        """
        validatedSignal = self.inputValidator.getValidatedSignal(raw, nowMs)
        decision = self.arbiter.evaluate(validatedSignal)
        self.outputPublisher.publish(decision)
        return self.actuatorPort.lastApplied


def makeFreshRawSignal(
    crashStatusRaw="NONE", leftRaw=False, rightRaw=False, faultRaw=False, nowMs=1000
):
    """!\\brief 전 필드가 신선한(age=0) RawVehicleSignal을 만드는 헬퍼(테스트 유틸리티)."""
    return RawVehicleSignal(
        crashStatusRaw=crashStatusRaw, crashStatusTimestampMs=nowMs,
        approachRiskLeftRaw=leftRaw, approachRiskLeftTimestampMs=nowMs,
        approachRiskRightRaw=rightRaw, approachRiskRightTimestampMs=nowMs,
        sensorFaultRaw=faultRaw, sensorFaultTimestampMs=nowMs,
    )


class TestFullPipelineIntegration(unittest.TestCase):
    """!\\brief INT-002 케이스 그룹 1~8 — 요구사항 기반·인터페이스·결함주입 시험."""

    def setUp(self):
        """!\\brief 매 시험마다 새 파이프라인(3개 유닛 실제 배선)을 조립한다."""
        self.pipeline = ChildlockPipeline()

    def testCrashConfirmedReleasesBothDoorsEndToEnd(self):
        """!
        \\brief INT-CASE-001: crash_status=CONFIRMED 원시 입력이 실제 출력 RELEASE로 이어지는지 검증한다.
        \\technique 요구사항 기반 시험(SWR-007) + 인터페이스 시험(IF-INT-001~003)
        \\case 긍정(Positive)
        """
        raw = makeFreshRawSignal(crashStatusRaw="CONFIRMED")
        applied = self.pipeline.runOneCycle(raw, nowMs=1000)
        self.assertEqual(applied.leftState, LockState.RELEASED)
        self.assertEqual(applied.rightState, LockState.RELEASED)

    def testApproachRiskLeftLocksOnlyLeftDoorEndToEnd(self):
        """!
        \\brief INT-CASE-002: 좌측 접근위험 원시 입력이 좌측만 LOCK으로 이어지는지 검증한다.
        \\technique 요구사항 기반 시험(SWR-005, SWR-009)
        \\case 긍정(Positive)
        """
        raw = makeFreshRawSignal(leftRaw=True)
        applied = self.pipeline.runOneCycle(raw, nowMs=1000)
        self.assertEqual(applied.leftState, LockState.LOCKED)
        self.assertEqual(applied.rightState, LockState.RELEASED)

    def testSensorFaultHoldsLastOutputEndToEnd(self):
        """!
        \\brief INT-CASE-003: 센서고장 발생 시 직전 출력이 그대로 유지되며 FAULT가 발행되는지 검증한다.
        \\technique 요구사항 기반 시험(SWR-021a/021b)
        \\case 긍정(Positive)
        """
        firstApplied = self.pipeline.runOneCycle(makeFreshRawSignal(leftRaw=True), nowMs=1000)
        self.assertEqual(firstApplied.leftState, LockState.LOCKED)
        secondApplied = self.pipeline.runOneCycle(
            makeFreshRawSignal(faultRaw=True), nowMs=1100
        )
        self.assertEqual(secondApplied.leftState, LockState.LOCKED)
        self.assertEqual(secondApplied.systemState, SystemState.FAULT)

    def testNoActiveConditionKeepsPreviousOutputEndToEnd(self):
        """!
        \\brief INT-CASE-004: 아무 조건도 없으면 직전 출력이 그대로 유지되는지 검증한다(기본 폴백).
        \\technique 요구사항 기반 시험(§7 정책표 4행)
        \\case 긍정(Positive)
        """
        applied = self.pipeline.runOneCycle(makeFreshRawSignal(), nowMs=1000)
        self.assertEqual(applied.reasonCode, "NO_CONDITION_MATCHED")

    def testStaleInputPropagatesDegradedStateEndToEnd(self):
        """!
        \\brief INT-CASE-005: freshness 초과 입력이 실제 출력의 시스템상태 DEGRADED로 전파되는지 검증한다(SWR-013a).
        \\technique 결함주입 시험
        \\case 부정(Negative)
        """
        staleRaw = RawVehicleSignal(
            crashStatusRaw="NONE", crashStatusTimestampMs=0,
            approachRiskLeftRaw=False, approachRiskLeftTimestampMs=0,
            approachRiskRightRaw=False, approachRiskRightTimestampMs=0,
            sensorFaultRaw=False, sensorFaultTimestampMs=0,
        )
        applied = self.pipeline.runOneCycle(staleRaw, nowMs=1000)
        self.assertEqual(applied.systemState, SystemState.DEGRADED)

    def testMalformedCrashStatusIsRejectedWithoutCrashingPipelineEndToEnd(self):
        """!
        \\brief INT-CASE-006: 잘못된 crash_status 값이 파이프라인을 중단시키지 않고 안전하게 무시되는지 검증한다(SWR-013b).
        \\technique 결함주입 시험 + 오류추정
        \\case 부정(Negative)
        """
        raw = makeFreshRawSignal(crashStatusRaw="NOT_A_REAL_STATUS")
        try:
            applied = self.pipeline.runOneCycle(raw, nowMs=1000)
        except Exception as unexpectedError:  # noqa: BLE001
            self.fail(f"pipeline raised unexpectedly: {unexpectedError}")
        self.assertEqual(applied.reasonCode, "NO_CONDITION_MATCHED")

    def testCrashConfirmedOutranksSensorFaultEndToEnd(self):
        """!
        \\brief INT-CASE-007: 충돌과 센서고장이 동시 발생해도 충돌 해제가 이기는지 전체 배선으로 검증한다(§7 1행).
        \\technique 결정테이블 + 요구사항 기반 시험
        \\case 긍정(Positive)
        """
        raw = makeFreshRawSignal(crashStatusRaw="CONFIRMED", faultRaw=True)
        applied = self.pipeline.runOneCycle(raw, nowMs=1000)
        self.assertEqual(applied.leftState, LockState.RELEASED)
        self.assertNotEqual(applied.systemState, SystemState.FAULT)

    def testSensorFaultOutranksApproachRiskEndToEnd(self):
        """!
        \\brief INT-CASE-008: 센서고장과 접근위험이 동시 발생하면 센서고장 홀드가 이기는지 검증한다(§7 2행).
        \\technique 결정테이블 + 요구사항 기반 시험
        \\case 긍정(Positive)
        """
        self.pipeline.runOneCycle(makeFreshRawSignal(), nowMs=1000)
        raw = makeFreshRawSignal(leftRaw=True, faultRaw=True)
        applied = self.pipeline.runOneCycle(raw, nowMs=1100)
        self.assertEqual(applied.systemState, SystemState.FAULT)
        self.assertEqual(applied.leftState, LockState.RELEASED)

    def testHandlerInternalErrorFallsThroughToDefaultEndToEnd(self):
        """!
        \\brief INT-CASE-009: 체인 앞단 Handler가 실제 배선에서 예외를 던져도 전체 파이프라인이
        안전하게 DefaultHandler까지 폴백하는지 검증한다(SWD-001 §9).
        \\technique 결함주입 시험
        \\case 부정(Negative)
        """
        pipeline = ChildlockPipeline()
        pipeline.arbiter = DoorLockArbiter(
            crashHandler=RaisingHandler(),
            sensorFaultHandler=RaisingHandler(),
            approachRiskHandler=RaisingHandler(),
            defaultHandler=DefaultHandler(),
        )
        applied = pipeline.runOneCycle(makeFreshRawSignal(), nowMs=1000)
        self.assertEqual(applied.reasonCode, "NO_CONDITION_MATCHED")

    def testActuatorPublishFailureDoesNotRaiseEndToEnd(self):
        """!
        \\brief INT-CASE-010: 액추에이터 발행이 실제 배선에서 실패해도 파이프라인 전체가 예외를
        전파하지 않는지 검증한다(SWD-001 §10).
        \\technique 결함주입 시험
        \\case 부정(Negative)
        """
        pipeline = ChildlockPipeline()
        pipeline.outputPublisher = OutputPublisher(RaisingActuatorPort())
        try:
            pipeline.runOneCycle(makeFreshRawSignal(crashStatusRaw="CONFIRMED"), nowMs=1000)
        except Exception as unexpectedError:  # noqa: BLE001
            self.fail(f"pipeline raised unexpectedly: {unexpectedError}")


if __name__ == "__main__":
    unittest.main()
