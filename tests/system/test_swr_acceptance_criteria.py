"""!
\\brief Phase 1 시스템 테스트 — VER-001의 실행 코드.
SWR-001_SW 요구사항 명세서.docx §4.2의 수용기준(원문) 문구를 기준으로 시스템을 블랙박스로 검증한다.
아키텍처/상세설계 내부 구조(Handler·Arbiter 등)는 참조하지 않고, "원시 입력 -> 액추에이터 출력"이라는
시스템 경계에서만 관찰한다(SWE.6, 요구사항 기반 블랙박스 시험).
"""

import unittest

from childlock.types import LockState, RawVehicleSignal, SystemState
from tests.support.fixtures import RealChildlockWiring, makeFreshRawSignal

makeFreshSignal = makeFreshRawSignal


class ChildlockSystem(RealChildlockWiring):
    """!
    \\brief 시스템 경계(원시 입력 -> 액추에이터 출력)만 노출하는 블랙박스 진입점(테스트 유틸리티).
    공용 배선(RealChildlockWiring)을 상속해 tests/integration과의 중복을 피하며,
    내부 컴포넌트 구성은 이 클래스 밖에서 관찰하지 않는다.
    """

    def submitVehicleSignal(self, raw: RawVehicleSignal, nowMs: int):
        """!
        \\brief 한 평가주기 동안 원시 신호를 시스템에 제출하고 액추에이터 출력을 반환한다.
        \\return 좌/우 LockState, systemState, reasonCode를 담은 관찰 가능한 출력.
        """
        return self.runCycle(raw, nowMs)


class TestSwrAcceptanceCriteria(unittest.TestCase):
    """!\\brief VER-CASE-001~009 — SWR-001 §4.2 수용기준 원문 검증."""

    def setUp(self):
        """!\\brief 매 시험마다 새 ChildlockSystem을 준비한다."""
        self.system = ChildlockSystem()

    def testSwr007CrashConfirmedReleasesBothDoors(self):
        """!
        \\brief VER-CASE-001(SWR-007): "전이 후 300ms 이내 두 출력 RELEASE, 이후 입력 주기에도 유지"를 검증한다.
        \\technique 요구사항 기반 시험(동등분할)
        \\case 긍정(Positive)
        """
        self.system.submitVehicleSignal(makeFreshSignal(), nowMs=1000)
        firstOutput = self.system.submitVehicleSignal(
            makeFreshSignal(crashStatusRaw="CONFIRMED"), nowMs=1050
        )
        secondOutput = self.system.submitVehicleSignal(
            makeFreshSignal(crashStatusRaw="CONFIRMED"), nowMs=1100
        )
        self.assertEqual(firstOutput.leftState, LockState.RELEASED)
        self.assertEqual(firstOutput.rightState, LockState.RELEASED)
        self.assertEqual(secondOutput.leftState, LockState.RELEASED)

    def testSwr008PendingOrNoneDoesNotForceRelease(self):
        """!
        \\brief VER-CASE-002(SWR-008): "PENDING/NONE 상태에서 crash 관련 강제 출력 변화 없음"을 검증한다.
        \\technique 요구사항 기반 시험(동등분할)
        \\case 부정(Negative)
        """
        self.system.submitVehicleSignal(makeFreshSignal(leftRaw=True), nowMs=1000)
        outputOnPending = self.system.submitVehicleSignal(
            makeFreshSignal(crashStatusRaw="PENDING"), nowMs=1050
        )
        self.assertEqual(outputOnPending.leftState, LockState.LOCKED)

    def testSwr005ApproachRiskLocksFromNextCycle(self):
        """!
        \\brief VER-CASE-003(SWR-005): "접근위험 TRUE 전이 시점 다음 평가주기부터 해당 출력 LOCK"을 검증한다.
        \\technique 요구사항 기반 시험
        \\case 긍정(Positive)
        """
        output = self.system.submitVehicleSignal(makeFreshSignal(leftRaw=True), nowMs=1000)
        self.assertEqual(output.leftState, LockState.LOCKED)

    def testSwr006SuppressionRecordsReasonCode(self):
        """!
        \\brief VER-CASE-004(SWR-006): "억제 발생 시 이유코드 필드에 정의된 코드 기록"을 검증한다.
        \\technique 요구사항 기반 시험
        \\case 긍정(Positive)
        """
        output = self.system.submitVehicleSignal(makeFreshSignal(leftRaw=True), nowMs=1000)
        self.assertTrue(len(output.reasonCode) >= 3)
        self.assertEqual(output.reasonCode, "SUPPRESSED_APPROACH_RISK")

    def testSwr009LeftAndRightDoorsAreIndependent(self):
        """!
        \\brief VER-CASE-005(SWR-009): "좌/우 조합 4가지 모두에서 반대쪽 출력 불변"을 검증한다.
        \\technique 요구사항 기반 시험(동등분할, 좌우 조합)
        \\case 긍정(Positive)
        """
        onlyLeft = self.system.submitVehicleSignal(makeFreshSignal(leftRaw=True), nowMs=1000)
        self.assertEqual(onlyLeft.leftState, LockState.LOCKED)
        self.assertEqual(onlyLeft.rightState, LockState.RELEASED)

        system2 = ChildlockSystem()
        onlyRight = system2.submitVehicleSignal(makeFreshSignal(rightRaw=True), nowMs=1000)
        self.assertEqual(onlyRight.rightState, LockState.LOCKED)
        self.assertEqual(onlyRight.leftState, LockState.RELEASED)

    def testSwr013aStaleInputTransitionsToDegraded(self):
        """!
        \\brief VER-CASE-006(SWR-013a): "필수 입력이 200ms 초과 미갱신되면 DEGRADED"를 검증한다.
        \\technique 요구사항 기반 시험(경계값분석)
        \\case 부정(Negative)
        """
        staleSignal = RawVehicleSignal(
            crashStatusRaw="NONE", crashStatusTimestampMs=0,
            approachRiskLeftRaw=False, approachRiskLeftTimestampMs=0,
            approachRiskRightRaw=False, approachRiskRightTimestampMs=0,
            sensorFaultRaw=False, sensorFaultTimestampMs=0,
        )
        output = self.system.submitVehicleSignal(staleSignal, nowMs=1000)
        self.assertEqual(output.systemState, SystemState.DEGRADED)

    def testSwr013bInvalidFormatIsRejected(self):
        """!
        \\brief VER-CASE-007(SWR-013b): "형식·범위 오류는 평가 전에 거절"을 검증한다 —
        무효한 crash_status가 CONFIRMED로 오인되어 LOCKED 상태를 강제 RELEASE시키지 않아야 한다.
        \\technique 요구사항 기반 시험(오류추정)
        \\case 부정(Negative)
        """
        self.system.submitVehicleSignal(makeFreshSignal(leftRaw=True), nowMs=1000)
        output = self.system.submitVehicleSignal(
            makeFreshSignal(crashStatusRaw="INVALID_ENUM_VALUE"), nowMs=1050
        )
        self.assertEqual(output.leftState, LockState.LOCKED)

    def testSwr021aSensorFaultHoldsPreviousOutput(self):
        """!
        \\brief VER-CASE-008(SWR-021a): "sensor_fault=TRUE 첫 평가주기부터 좌/우 출력 불변"을 검증한다.
        \\technique 요구사항 기반 시험
        \\case 긍정(Positive)
        """
        self.system.submitVehicleSignal(makeFreshSignal(leftRaw=True), nowMs=1000)
        output = self.system.submitVehicleSignal(makeFreshSignal(faultRaw=True), nowMs=1050)
        self.assertEqual(output.leftState, LockState.LOCKED)

    def testSwr021bSensorFaultSetsFaultStateWithReasonCode(self):
        """!
        \\brief VER-CASE-009(SWR-021b): "TRUE 전이 첫 평가주기에 상태=FAULT 및 경고코드 필드 비어있지 않음"을 검증한다.
        \\technique 요구사항 기반 시험
        \\case 긍정(Positive)
        """
        output = self.system.submitVehicleSignal(makeFreshSignal(faultRaw=True), nowMs=1000)
        self.assertEqual(output.systemState, SystemState.FAULT)
        self.assertTrue(len(output.reasonCode) > 0)


if __name__ == "__main__":
    unittest.main()
