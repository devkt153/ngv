"""!
\\brief IPriorityHandler 인터페이스 계약 단위시험.
"""

import unittest

from childlock.interfaces import IPriorityHandler


class PassthroughHandler(IPriorityHandler):
    """!\\brief 추상 메서드의 기본 구현을 직접 호출하기 위한 테스트 전용 서브클래스(테스트 유틸리티)."""

    def tryHandle(self, signal, previous):
        """!\\brief 부모(추상)의 tryHandle을 그대로 호출한다."""
        return super().tryHandle(signal, previous)


class TestIPriorityHandlerContract(unittest.TestCase):
    def testAbstractTryHandleRaisesNotImplementedError(self):
        """!
        \\brief 구현되지 않은 추상 tryHandle을 직접 호출하면 NotImplementedError가 발생하는지 검증한다.
        \\technique 오류추정
        \\case 부정(Negative)
        """
        handler = PassthroughHandler()
        with self.assertRaises(NotImplementedError):
            handler.tryHandle(None, None)


if __name__ == "__main__":
    unittest.main()
