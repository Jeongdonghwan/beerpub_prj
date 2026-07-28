from flask import Blueprint, render_template, request

from ..extensions import db
from ..models import Notice

bp = Blueprint("board", __name__)

PER_PAGE = 10


@bp.route("/notice")
def notice_list():
    page = request.args.get("page", 1, type=int)
    pg = Notice.query.order_by(Notice.id.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    return render_template("board/notice_list.html", pg=pg)


@bp.route("/notice/<int:notice_id>")
def notice_view(notice_id):
    item = Notice.query.get_or_404(notice_id)
    item.hit += 1
    db.session.commit()
    return render_template("board/notice_view.html", item=item)
