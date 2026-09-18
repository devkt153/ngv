"""!
\\brief SWD-001 §4(공통 자료형)에 정의된 값 타입.
\\implements UNIT-001, UNIT-002, UNIT-003, UNIT-004, UNIT-005, UNIT-006, UNIT-007
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CrashStatus(Enum):
    """!
    \\brief 충돌 상태 (OEM-IF-002).
    """

    NONE = "NONE"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"


class LockState(Enum):
    """!
    \\brief 도어 잠금 출력 상태 (OEM-IF-005).
    """

    LOCKED = "LOCKED"
    RELEASED = "RELEASED"


class SystemState(Enum):
    """!
    \\brief 시스템 건강 상태.
    """

    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    FAULT = "FAULT"


@dataclass(frozen=True)
class RawVehicleSignal:
    """!
    \\brief Vehicle이 제공하는 원시 신호 스냅샷(필드별 timestamp 포함).
    \\implements UNIT-001
    """

    crashStatusRaw: str
    crashStatusTimestampMs: int
    approachRiskLeftRaw: Optional[bool]
    approachRiskLeftTimestampMs: int
    approachRiskRightRaw: Optional[bool]
    approachRiskRightTimestampMs: int
    sensorFaultRaw: Optional[bool]
    sensorFaultTimestampMs: int


@dataclass(frozen=True)
class ValidatedSignalSnapshot:
    """!
    \\brief InputValidator가 검증한 신호 스냅샷 (SWD-001 §4).
    \\implements UNIT-001
    """

    crashStatus: CrashStatus
    crashStatusValid: bool
    approachRiskLeft: bool
    approachRiskLeftValid: bool
    approachRiskRight: bool
    approachRiskRightValid: bool
    sensorFault: bool
    sensorFaultValid: bool
    systemStateHint: SystemState


@dataclass(frozen=True)
class LockDecision:
    """!
    \\brief 좌/우 도어 출력과 시스템 상태를 담는 확정 결정.
    \\implements UNIT-002, UNIT-003, UNIT-004, UNIT-005, UNIT-006, UNIT-007
    """

    leftState: LockState
    rightState: LockState
    systemState: SystemState
    reasonCode: str


@dataclass(frozen=True)
class HandlerResult:
    """!
    \\brief IPriorityHandler.tryHandle()의 반환값.
    \\implements UNIT-003, UNIT-004, UNIT-005, UNIT-006
    """

    handled: bool
    decision: Optional[LockDecision]
    reasonCode: str
