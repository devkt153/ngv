"""!
\\brief 통합시험(tests/integration)과 시스템시험(tests/system)이 공유하는
실제 파이프라인 배선 및 신호 생성 헬퍼(테스트 유틸리티).
중복 배선 코드를 방지하기 위해 여기 한 곳에서만 정의한다.
"""

from childlock.door_lock_arbiter import DoorLockArbiter
from childlock.handlers.approach_risk_handler import ApproachRiskHandler
from childlock.handlers.crash_release_handler import CrashReleaseHandler
from childlock.handlers.default_handler import DefaultHandler
from childlock.handlers.sensor_fault_handler import SensorFaultHandler
from childlock.input_validator import InputValidator
from childlock.output_publisher import InMemoryActuatorPort, OutputPublisher
from childlock.types import RawVehicleSignal


def buildDefaultArbiter():
    """!\\brief SWA-001 통합 순서(2단계)대로 배선된 기본 DoorLockArbiter(4 Handler 포함)를 만든다."""
    return DoorLockArbiter(
        crashHandler=CrashReleaseHandler(),
        sensorFaultHandler=SensorFaultHandler(),
        approachRiskHandler=ApproachRiskHandler(),
        defaultHandler=DefaultHandler(),
    )


class RealChildlockWiring:
    """!
    \\brief InputValidator+DoorLockArbiter(4 Handler)+OutputPublisher를 실제 객체로 배선하는
    공용 조립체(테스트 유틸리티). 결함주입이 필요하면 arbiter/actuatorPort를 대체 구현으로 넘긴다.
    """

    def __init__(self, arbiter=None, actuatorPort=None):
        """!\\brief 실제 구성으로 초기화한다(결함주입용 대체 구현 주입 가능)."""
        self.inputValidator = InputValidator()
        self.arbiter = arbiter if arbiter is not None else buildDefaultArbiter()
        self.actuatorPort = actuatorPort if actuatorPort is not None else InMemoryActuatorPort()
        self.outputPublisher = OutputPublisher(self.actuatorPort)

    def runCycle(self, raw: RawVehicleSignal, nowMs: int):
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
