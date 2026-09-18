"""!
\\brief UNIT-001 InputValidator — SWR-013a(freshness), SWR-013b(형식/범위) 구현.
\\implements UNIT-001
"""

from childlock.types import CrashStatus, RawVehicleSignal, SystemState, ValidatedSignalSnapshot

FRESHNESS_LIMIT_MS = 200
"""!\\brief SWR-013a: 필수 입력의 최대 허용 미갱신 시간(ms)."""

VALID_CRASH_STATUS_VALUES = {"NONE", "PENDING", "CONFIRMED"}
"""!\\brief SWR-013b: crash_status로 허용되는 문자열 값(OEM-IF-002)."""


def isFreshEnough(fieldTimestampMs: int, nowMs: int) -> bool:
    """!
    \\brief 필드가 FRESHNESS_LIMIT_MS 이내에 갱신되었는지 확인한다.
    \\param fieldTimestampMs 그 필드가 마지막으로 갱신된 시각(ms).
    \\param nowMs 현재 평가 시각(ms).
    \\return 신선하면 True.
    """
    ageMs = nowMs - fieldTimestampMs
    return ageMs <= FRESHNESS_LIMIT_MS


def isValidCrashStatus(crashStatusRaw: str) -> bool:
    """!
    \\brief crash_status 원시값이 OEM-IF-002 유효 열거값인지 확인한다(SWR-013b).
    """
    return crashStatusRaw in VALID_CRASH_STATUS_VALUES


def isValidBoolean(rawValue: object) -> bool:
    """!
    \\brief boolean 입력(approach_risk_*, sensor_fault)의 형식이 유효한지 확인한다(SWR-013b).
    """
    return isinstance(rawValue, bool)


def parseCrashStatus(crashStatusRaw: str) -> CrashStatus:
    """!
    \\brief 유효성이 확인된 crash_status 문자열을 CrashStatus로 변환한다.
    \\pre isValidCrashStatus(crashStatusRaw) == True
    """
    return CrashStatus(crashStatusRaw)


class InputValidator:
    """!
    \\brief UNIT-001 — 안전 입력의 형식·범위·freshness를 검증한다(CMP-001).
    """

    def getValidatedSignal(
        self, raw: RawVehicleSignal, nowMs: int
    ) -> ValidatedSignalSnapshot:
        """!
        \\brief 원시 신호를 검증해 ValidatedSignalSnapshot을 반환한다.
        \\param raw Vehicle이 제공한 원시 신호(필드별 timestamp 포함).
        \\param nowMs 현재 평가 시각(ms).
        \\return 필드별 값과 유효성 플래그, systemStateHint를 포함한 스냅샷.
        \\post 예외를 던지지 않는다 — 무효 데이터는 Valid=False로 표현한다.
        """
        crashValid = isValidCrashStatus(raw.crashStatusRaw) and isFreshEnough(
            raw.crashStatusTimestampMs, nowMs
        )
        leftValid = isValidBoolean(raw.approachRiskLeftRaw) and isFreshEnough(
            raw.approachRiskLeftTimestampMs, nowMs
        )
        rightValid = isValidBoolean(raw.approachRiskRightRaw) and isFreshEnough(
            raw.approachRiskRightTimestampMs, nowMs
        )
        faultValid = isValidBoolean(raw.sensorFaultRaw) and isFreshEnough(
            raw.sensorFaultTimestampMs, nowMs
        )
        allValid = crashValid and leftValid and rightValid and faultValid
        stateHint = SystemState.NORMAL if allValid else SystemState.DEGRADED
        return ValidatedSignalSnapshot(
            crashStatus=parseCrashStatus(raw.crashStatusRaw) if crashValid else CrashStatus.NONE,
            crashStatusValid=crashValid,
            approachRiskLeft=raw.approachRiskLeftRaw if leftValid else False,
            approachRiskLeftValid=leftValid,
            approachRiskRight=raw.approachRiskRightRaw if rightValid else False,
            approachRiskRightValid=rightValid,
            sensorFault=raw.sensorFaultRaw if faultValid else False,
            sensorFaultValid=faultValid,
            systemStateHint=stateHint,
        )
