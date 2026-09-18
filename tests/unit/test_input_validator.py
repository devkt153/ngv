"""!
\\brief UNIT-001 InputValidator 단위시험 — SWR-013a, SWR-013b.
"""

import unittest

from childlock.input_validator import InputValidator, isFreshEnough
from childlock.types import CrashStatus, RawVehicleSignal, SystemState


def makeRawSignal(
    crashStatusRaw="NONE",
    crashStatusAgeMs=0,
    leftRaw=False,
    leftAgeMs=0,
    rightRaw=False,
    rightAgeMs=0,
    faultRaw=False,
    faultAgeMs=0,
    nowMs=1000,
):
    """!\\brief 테스트용 RawVehicleSignal을 age(ms) 기준으로 조립하는 헬퍼(테스트 유틸리티)."""
    return RawVehicleSignal(
        crashStatusRaw=crashStatusRaw,
        crashStatusTimestampMs=nowMs - crashStatusAgeMs,
        approachRiskLeftRaw=leftRaw,
        approachRiskLeftTimestampMs=nowMs - leftAgeMs,
        approachRiskRightRaw=rightRaw,
        approachRiskRightTimestampMs=nowMs - rightAgeMs,
        sensorFaultRaw=faultRaw,
        sensorFaultTimestampMs=nowMs - faultAgeMs,
    ), nowMs


class TestIsFreshEnough(unittest.TestCase):
    def testIsFreshEnoughAtExactlyTwoHundredMsIsValid(self):
        """!
        \\brief freshness 경계값 200ms 정확히는 유효로 판정되는지 검증한다.
        \\technique 경계값분석 (FRESHNESS_LIMIT_MS=200 경계)
        \\case 긍정(Positive)
        """
        self.assertTrue(isFreshEnough(fieldTimestampMs=800, nowMs=1000))

    def testIsFreshEnoughAtTwoHundredOneMsIsInvalid(self):
        """!
        \\brief freshness 경계값을 1ms 초과하면 무효로 판정되는지 검증한다.
        \\technique 경계값분석 (FRESHNESS_LIMIT_MS 경계+1)
        \\case 부정(Negative)
        """
        self.assertFalse(isFreshEnough(fieldTimestampMs=799, nowMs=1000))


class TestInputValidatorGetValidatedSignal(unittest.TestCase):
    def setUp(self):
        """!\\brief 매 테스트마다 새 InputValidator 인스턴스를 준비한다."""
        self.validator = InputValidator()

    def testGetValidatedSignalAllFreshAndWellFormedYieldsNormal(self):
        """!
        \\brief 모든 입력이 신선하고 형식이 올바르면 systemStateHint가 NORMAL인지 검증한다.
        \\technique 동등분할 (유효 클래스)
        \\case 긍정(Positive)
        """
        raw, nowMs = makeRawSignal(crashStatusRaw="CONFIRMED")
        result = self.validator.getValidatedSignal(raw, nowMs)
        self.assertEqual(result.systemStateHint, SystemState.NORMAL)
        self.assertTrue(result.crashStatusValid)
        self.assertEqual(result.crashStatus, CrashStatus.CONFIRMED)

    def testGetValidatedSignalRejectsInvalidCrashStatusEnum(self):
        """!
        \\brief crash_status가 정의된 열거값이 아니면 거절되는지 검증한다(SWR-013b).
        \\technique 동등분할 (무효 클래스) + 오류추정
        \\case 부정(Negative)
        """
        raw, nowMs = makeRawSignal(crashStatusRaw="UNKNOWN_VALUE")
        result = self.validator.getValidatedSignal(raw, nowMs)
        self.assertFalse(result.crashStatusValid)
        self.assertEqual(result.crashStatus, CrashStatus.NONE)

    def testGetValidatedSignalRejectsNonBooleanApproachRisk(self):
        """!
        \\brief approach_risk 입력이 boolean이 아니면 거절되는지 검증한다(SWR-013b).
        \\technique 동등분할 (형식 오류)
        \\case 부정(Negative)
        """
        raw, nowMs = makeRawSignal(leftRaw="TRUE_STRING")
        result = self.validator.getValidatedSignal(raw, nowMs)
        self.assertFalse(result.approachRiskLeftValid)
        self.assertFalse(result.approachRiskLeft)

    def testGetValidatedSignalMarksDegradedWhenAnyFieldStale(self):
        """!
        \\brief 하나의 안전 입력이라도 freshness를 초과하면 DEGRADED가 되는지 검증한다(SWR-013a).
        \\technique 경계값분석 + 상태전이
        \\case 부정(Negative)
        """
        raw, nowMs = makeRawSignal(faultAgeMs=201)
        result = self.validator.getValidatedSignal(raw, nowMs)
        self.assertFalse(result.sensorFaultValid)
        self.assertEqual(result.systemStateHint, SystemState.DEGRADED)

    def testGetValidatedSignalNeverRaisesOnInvalidInput(self):
        """!
        \\brief 완전히 무효한 입력이 주어져도 예외를 던지지 않는지 검증한다(SWD-001 §9).
        \\technique 오류추정
        \\case 부정(Negative)
        """
        raw, nowMs = makeRawSignal(
            crashStatusRaw="", leftRaw=None, rightRaw=None, faultRaw=None,
            crashStatusAgeMs=99999, leftAgeMs=99999, rightAgeMs=99999, faultAgeMs=99999,
        )
        try:
            result = self.validator.getValidatedSignal(raw, nowMs)
        except Exception as unexpectedError:  # noqa: BLE001
            self.fail(f"getValidatedSignal raised unexpectedly: {unexpectedError}")
        self.assertEqual(result.systemStateHint, SystemState.DEGRADED)


if __name__ == "__main__":
    unittest.main()
