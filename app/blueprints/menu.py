from flask import Blueprint, render_template, request

from ..models import Menu, MenuCategory

bp = Blueprint("menu", __name__)


@bp.route("/preview")
def preview():
    categories = (
        MenuCategory.query.filter_by(is_active=True).order_by(MenuCategory.sort).all()
    )
    return render_template("menu/preview.html", categories=categories)


@bp.route("/list")
def list_():
    categories = (
        MenuCategory.query.filter_by(is_active=True).order_by(MenuCategory.sort).all()
    )
    ca_id = request.args.get("ca_id", type=int)
    query = Menu.query.filter_by(is_active=True)
    current = None
    if ca_id:
        current = MenuCategory.query.get(ca_id)
        query = query.filter_by(category_id=ca_id)
    menus = query.order_by(Menu.sort, Menu.id).all()
    return render_template(
        "menu/list.html", categories=categories, menus=menus, current=current
    )


@bp.route("/popup/<int:menu_id>")
def popup(menu_id):
    item = Menu.query.get_or_404(menu_id)
    return render_template("menu/_popup.html", item=item)
