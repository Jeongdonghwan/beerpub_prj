from datetime import date
from functools import wraps

from flask import (
    Blueprint, abort, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash

from config.brand import BRAND

from ..extensions import db
from ..models import (
    AdminUser, Banner, History, Inquiry, Interior, Menu, MenuCategory, Notice,
    Popup, Story, Store,
)
from ..utils.security import check_csrf
from ..utils.uploads import save_image

bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------- 보드 레지스트리
# field: (name, label, type[, extra])
#   type: text / number / float / textarea / check / date / badge / image:<board> / select:<provider>
def _category_options():
    return [(c.id, c.name) for c in MenuCategory.query.order_by(MenuCategory.sort).all()]


def _region_options():
    return [(r, r) for r in BRAND["regions"]]


BOARDS = {
    "category": {
        "model": MenuCategory, "title": "메뉴 카테고리",
        "fields": [("name", "카테고리명", "text"), ("sort", "정렬", "number"),
                   ("is_active", "노출", "check")],
        "cols": ["id", "name", "sort", "is_active"],
    },
    "menu": {
        "model": Menu, "title": "메뉴",
        "fields": [("category_id", "카테고리", "select", _category_options),
                   ("name", "메뉴명", "text"), ("name_en", "영문명", "text"),
                   ("price", "가격(원)", "number"), ("description", "설명", "textarea"),
                   ("badge", "뱃지", "select", lambda: [("", "없음"), ("new", "NEW"), ("best", "BEST"), ("signature", "시그니처")]),
                   ("image", "사진 (800x800 권장)", "image:menu"),
                   ("detail_image", "상세 사진", "image:menu"),
                   ("sort", "정렬", "number"), ("is_active", "노출", "check")],
        "cols": ["id", "name", "price", "badge", "sort", "is_active"],
    },
    "interior": {
        "model": Interior, "title": "인테리어",
        "fields": [("title", "제목", "text"), ("image", "사진 (1600x1000 권장)", "image:interior"),
                   ("sort", "정렬", "number")],
        "cols": ["id", "title", "sort"],
    },
    "story": {
        "model": Story, "title": "성공창업 스토리",
        "fields": [("branch_name", "지점명", "text"), ("title", "제목", "text"),
                   ("summary", "한줄 카피", "text"), ("content", "본문", "textarea"),
                   ("thumb", "썸네일 (800x600 권장)", "image:story"),
                   ("sort", "정렬", "number"), ("is_active", "노출", "check")],
        "cols": ["id", "branch_name", "title", "sort", "is_active"],
    },
    "store": {
        "model": Store, "title": "매장",
        "fields": [("name", "지점명", "text"), ("region", "지역", "select", _region_options),
                   ("address", "주소", "text"), ("phone", "전화", "text"),
                   ("lat", "위도", "float"), ("lng", "경도", "float"),
                   ("is_active", "노출", "check")],
        "cols": ["id", "name", "region", "phone", "is_active"],
    },
    "history": {
        "model": History, "title": "연혁",
        "fields": [("year", "연도", "number"), ("month", "월", "number"),
                   ("content", "내용", "text"), ("sort", "정렬", "number")],
        "cols": ["id", "year", "month", "content"],
    },
    "banner": {
        "model": Banner, "title": "배너",
        "fields": [("title", "제목", "text"), ("image", "이미지 (360x120 권장)", "image:banner"),
                   ("link", "링크", "text"), ("sort", "정렬", "number"),
                   ("is_active", "노출", "check")],
        "cols": ["id", "title", "link", "sort", "is_active"],
    },
    "popup": {
        "model": Popup, "title": "레이어 팝업",
        "fields": [("title", "제목", "text"), ("image", "이미지 (500x600 권장)", "image:popup"),
                   ("link", "링크", "text"), ("start_date", "시작일", "date"),
                   ("end_date", "종료일", "date"), ("is_active", "노출", "check")],
        "cols": ["id", "title", "is_active", "start_date", "end_date"],
    },
    "notice": {
        "model": Notice, "title": "창업소식",
        "fields": [("title", "제목", "text"), ("content", "본문", "textarea")],
        "cols": ["id", "title", "hit", "created_at"],
    },
}

# ---------------------------------------------------------------- 인증
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = AdminUser.query.filter_by(username=request.form.get("username", "")).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session["admin_id"] = user.id
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        error = "아이디 또는 비밀번호가 올바르지 않습니다."
    return render_template("admin/login.html", error=error)


@bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


@bp.before_request
def guard():
    if request.endpoint in ("admin.login", "admin.logout"):
        return None
    if not session.get("admin_id"):
        return redirect(url_for("admin.login", next=request.path))
    if request.method == "POST" and not check_csrf():
        abort(400, "CSRF 검증 실패")
    return None


# ---------------------------------------------------------------- 대시보드 / 문의
@bp.route("/")
def dashboard():
    new_count = Inquiry.query.filter_by(status="new").count()
    recent = Inquiry.query.order_by(Inquiry.id.desc()).limit(5).all()
    counts = {key: cfg["model"].query.count() for key, cfg in BOARDS.items()}
    return render_template(
        "admin/dashboard.html", new_count=new_count, recent=recent,
        counts=counts, boards=BOARDS,
    )


@bp.route("/inquiry")
def inquiry_list():
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)
    query = Inquiry.query
    if status:
        query = query.filter_by(status=status)
    pg = query.order_by(Inquiry.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/inquiry_list.html", pg=pg, status=status)


@bp.route("/inquiry/<int:inquiry_id>", methods=["POST"])
def inquiry_update(inquiry_id):
    item = Inquiry.query.get_or_404(inquiry_id)
    if request.form.get("status") in ("new", "contacted", "closed"):
        item.status = request.form["status"]
    item.memo = request.form.get("memo", item.memo)
    db.session.commit()
    return redirect(request.referrer or url_for("admin.inquiry_list"))


# ---------------------------------------------------------------- 제네릭 CRUD
def _get_board(board):
    if board not in BOARDS:
        abort(404)
    return BOARDS[board]


def _apply_form(cfg, item, board):
    for field in cfg["fields"]:
        name, _, ftype = field[0], field[1], field[2]
        if ftype.startswith("image:"):
            upload_board = ftype.split(":", 1)[1]
            url, thumb = save_image(request.files.get(name), upload_board)
            if url:
                setattr(item, name, url)
                if name == "image" and hasattr(item, "thumb"):
                    item.thumb = thumb or url
            elif request.form.get(f"{name}__clear"):
                setattr(item, name, "")
                if name == "image" and hasattr(item, "thumb"):
                    item.thumb = ""
        elif ftype == "check":
            setattr(item, name, request.form.get(name) == "on")
        elif ftype == "number":
            setattr(item, name, request.form.get(name, type=int) or 0)
        elif ftype == "float":
            raw = request.form.get(name, "").strip()
            setattr(item, name, float(raw) if raw else None)
        elif ftype == "date":
            raw = request.form.get(name, "").strip()
            setattr(item, name, date.fromisoformat(raw) if raw else None)
        elif ftype == "select" and field[0] == "category_id":
            setattr(item, name, request.form.get(name, type=int))
        else:
            setattr(item, name, request.form.get(name, "").strip())


@bp.route("/<board>")
def board_list(board):
    cfg = _get_board(board)
    items = cfg["model"].query.order_by(cfg["model"].id.desc()).all()
    return render_template("admin/board_list.html", board=board, cfg=cfg, items=items)


@bp.route("/<board>/new", methods=["GET", "POST"])
@bp.route("/<board>/<int:item_id>", methods=["GET", "POST"])
def board_edit(board, item_id=None):
    cfg = _get_board(board)
    item = cfg["model"].query.get_or_404(item_id) if item_id else cfg["model"]()
    if request.method == "POST":
        _apply_form(cfg, item, board)
        if not item_id:
            db.session.add(item)
        db.session.commit()
        return redirect(url_for("admin.board_list", board=board))
    return render_template("admin/board_edit.html", board=board, cfg=cfg, item=item)


@bp.route("/<board>/<int:item_id>/delete", methods=["POST"])
def board_delete(board, item_id):
    cfg = _get_board(board)
    item = cfg["model"].query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("admin.board_list", board=board))
