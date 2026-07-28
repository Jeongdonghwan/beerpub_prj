"""가맹문의 접수 알림 — 인터페이스 분리 (추후 SMTP/알림톡 구현체 교체).

새 채널 추가 시 Notifier 를 상속해 send() 만 구현하고 get_notifier() 에서 반환.
"""
import logging

logger = logging.getLogger("beerpub.notify")
logging.basicConfig(level=logging.INFO)


class Notifier:
    def send(self, inquiry):
        raise NotImplementedError


class ConsoleNotifier(Notifier):
    """개발용 — 콘솔(로그)로만 출력."""

    def send(self, inquiry):
        logger.info(
            "[가맹문의 접수] #%s %s / %s / %s / %s",
            inquiry.id, inquiry.name, inquiry.phone, inquiry.region, inquiry.channel,
        )


def get_notifier():
    # [확인필요] 운영 전환 시 SMTP/알림톡 Notifier 로 교체
    return ConsoleNotifier()
