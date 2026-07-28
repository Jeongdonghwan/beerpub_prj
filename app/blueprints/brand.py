from flask import Blueprint, render_template

from ..models import History

bp = Blueprint("brand", __name__)


@bp.route("/info")
def info():
    return render_template("brand/info.html")


@bp.route("/history")
def history():
    rows = History.query.order_by(History.year.desc(), History.month.desc(), History.sort).all()
    return render_template("brand/history.html", rows=rows)
