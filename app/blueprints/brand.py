from flask import Blueprint, render_template

bp = Blueprint("brand", __name__)


@bp.route("/info")
def info():
    return render_template("brand/info.html")
