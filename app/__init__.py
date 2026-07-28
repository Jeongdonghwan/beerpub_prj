from flask import Flask

from config.brand import BRAND
from config.settings import Config

from .extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from .blueprints.main import bp as main_bp
    from .blueprints.brand import bp as brand_bp
    from .blueprints.menu import bp as menu_bp
    from .blueprints.interior import bp as interior_bp
    from .blueprints.store import bp as store_bp
    from .blueprints.startup import bp as startup_bp
    from .blueprints.board import bp as board_bp
    from .blueprints.inquiry import bp as inquiry_bp
    from .blueprints.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(brand_bp, url_prefix="/brand")
    app.register_blueprint(menu_bp, url_prefix="/menu")
    app.register_blueprint(interior_bp, url_prefix="/interior")
    app.register_blueprint(store_bp, url_prefix="/store")
    app.register_blueprint(startup_bp, url_prefix="/startup")
    app.register_blueprint(board_bp, url_prefix="/board")
    app.register_blueprint(inquiry_bp, url_prefix="/inquiry")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_globals():
        from .models import MenuCategory, Popup, get_site_config
        from .utils.security import get_csrf_token

        return {
            "brand": BRAND,
            "site_config": get_site_config(),
            "gnb_categories": MenuCategory.query.filter_by(is_active=True)
            .order_by(MenuCategory.sort)
            .all(),
            "layer_popups": Popup.query.filter_by(is_active=True).limit(3).all(),
            "csrf_token": get_csrf_token,
        }

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template

        return render_template("error.html", code=404, msg="페이지를 찾을 수 없습니다."), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template

        return render_template("error.html", code=500, msg="일시적인 오류가 발생했습니다."), 500

    return app
