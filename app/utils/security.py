import re
import secrets

from flask import request, session

PHONE_RE = re.compile(r"^0\d{1,2}-?\d{3,4}-?\d{4}$")

HONEYPOT_FIELD = "website"  # 봇 전용 숨김 필드 — 값이 있으면 스팸


def get_csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def check_csrf():
    token = request.form.get("_csrf", "") or request.headers.get("X-CSRF-Token", "")
    return token == session.get("_csrf", "-")


def is_honeypot_filled(form):
    return bool(form.get(HONEYPOT_FIELD, "").strip())


def valid_phone(phone):
    return bool(PHONE_RE.match(phone.strip()))


def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or ""
