from flask import Blueprint, render_template

bp = Blueprint("startup", __name__)


@bp.route("/step")
def step():
    return render_template("startup/step.html")


@bp.route("/cost")
def cost():
    return render_template("startup/cost.html")
