from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from config.brand import BRAND

from ..extensions import db
from ..models import Inquiry
from ..utils.notify import get_notifier
from ..utils.rate_limit import inquiry_rate_limited
from ..utils.security import client_ip, is_honeypot_filled, valid_phone

bp = Blueprint("inquiry", __name__)


@bp.route("/")
def form():
    preset = None
    if request.args.get("type") == "taste":
        preset = {"name": "", "phone": "", "region": "", "channel": "",
                  "message": "무료시식 신청합니다."}
    return render_template("inquiry/form.html", form_data=preset)


@bp.route("/done")
def done():
    return render_template("inquiry/done.html")


def _validate(form):
    """검증 실패 시 에러 메시지, 통과 시 None."""
    name = form.get("name", "").strip()
    phone = form.get("phone", "").strip()
    region = form.get("region", "").strip()
    channel = form.get("channel", "").strip()
    if not name:
        return "성함을 입력해 주세요."
    if not valid_phone(phone):
        return "연락처를 정확히 입력해 주세요. (예: 010-1234-5678)"
    if form.get("agree_privacy") != "on":
        return "개인정보처리방침에 동의해 주세요."
    if region and region not in BRAND["regions"]:
        return "가맹희망지역을 선택해 주세요."
    if channel and channel not in BRAND["channels"]:
        return "유입경로를 선택해 주세요."
    return None


@bp.route("/submit", methods=["POST"])
def submit():
    wants_json = request.headers.get("X-Requested-With") == "fetch"

    def fail(msg, code=400):
        if wants_json:
            return jsonify(ok=False, msg=msg), code
        return render_template("inquiry/form.html", error=msg, form_data=request.form), code

    # honeypot — 봇이면 저장 없이 정상 접수인 척 종료
    if is_honeypot_filled(request.form):
        if wants_json:
            return jsonify(ok=True)
        return redirect(url_for("inquiry.done"))

    error = _validate(request.form)
    if error:
        return fail(error)

    ip = client_ip()
    if inquiry_rate_limited(ip):
        return fail("접수가 너무 잦습니다. 잠시 후 다시 시도해 주세요.", 429)

    item = Inquiry(
        name=request.form["name"].strip(),
        phone=request.form["phone"].strip(),
        region=request.form.get("region", "").strip(),
        channel=request.form.get("channel", "").strip(),
        message=request.form.get("message", "").strip(),
        agree_privacy=True,
        ip=ip,
    )
    db.session.add(item)
    db.session.commit()
    get_notifier().send(item)

    if wants_json:
        return jsonify(ok=True)
    return redirect(url_for("inquiry.done"))
