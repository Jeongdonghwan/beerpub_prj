from datetime import datetime, timedelta

from ..models import Inquiry

WINDOW_SECONDS = 60
MAX_PER_WINDOW = 3


def inquiry_rate_limited(ip):
    """같은 IP 가 60초 내 3건 이상 접수했으면 True. DB 기반이라 멀티워커에서도 안전."""
    since = datetime.utcnow() - timedelta(seconds=WINDOW_SECONDS)
    count = Inquiry.query.filter(Inquiry.ip == ip, Inquiry.created_at >= since).count()
    return count >= MAX_PER_WINDOW
