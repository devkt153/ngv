"""!
\\brief UNIT-004 SensorFaultHandler — SWR-021a, SWR-021b 구현.
\\implements UNIT-004
"""

from childlock.interfaces import IPriorityHandler
from childlock.types import HandlerResult, LockDecision, SystemState

SENSOR_FAULT_HOLD_REASON = "SENSOR_FAULT_HOLD"
"""!\\brief SWR-021a/021b 센서고장 홀드 사유코드."""


class SensorFaultHandler(IPriorityHandler):
    """!
    \\brief 우선순위 2 — sensor_fault=TRUE 시 직전 출력 유지(SWR-021a) + state=FAULT(SWR-021b).
    """

    def tryHandle(self, signal, previous) -> HandlerResult:
        """!
        \\brief sensor_fault가 TRUE(valid)인지 판단해 출력 동결을 결정한다.
        \\param signal 검증된 신호.
        \\param previous 직전 확정 LockDecision — 좌/우를 그대로 유지하는 데 사용한다.
        \\return sensor_fault가 아니면 handled=False, TRUE면 handled=True + previous 좌/우 유지 + FAULT.
        """
        if not signal.sensorFaultValid:
            return HandlerResult(handled=False, decision=None, reasonCode="")
        if not signal.sensorFault:
            return HandlerResult(handled=False, decision=None, reasonCode="")
        faultDecision = LockDecision(
            leftState=previous.leftState,
            rightState=previous.rightState,
            systemState=SystemState.FAULT,
            reasonCode=SENSOR_FAULT_HOLD_REASON,
        )
        return HandlerResult(
            handled=True, decision=faultDecision, reasonCode=SENSOR_FAULT_HOLD_REASON
        )
