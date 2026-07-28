from flask import Blueprint, render_template

from ..models import Interior

bp = Blueprint("interior", __name__)


@bp.route("/list")
def list_():
    items = Interior.query.order_by(Interior.sort, Interior.id).all()
    return render_template("interior/list.html", items=items)


@bp.route("/popup/<int:interior_id>")
def popup(interior_id):
    item = Interior.query.get_or_404(interior_id)
    return render_template("interior/_popup.html", item=item)
