from flask import Blueprint, render_template, request

from ..models import Store

bp = Blueprint("store", __name__)


@bp.route("/list")
def list_():
    region = request.args.get("region", "")
    query = Store.query.filter_by(is_active=True)
    if region:
        query = query.filter_by(region=region)
    stores = query.order_by(Store.id).all()
    regions = [r[0] for r in Store.query.with_entities(Store.region).distinct().all() if r[0]]
    return render_template("store/list.html", stores=stores, regions=regions, current_region=region)
